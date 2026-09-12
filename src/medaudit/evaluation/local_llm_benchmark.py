"""Run an end-to-end grounded-generation benchmark on synthetic data only."""

import argparse
import asyncio
import json
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.evaluation.private_bm25 import write_private_report
from medaudit.llm import LlamaCppClient
from medaudit.rag import (
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    build_grounded_request,
    validate_grounded_response,
)
from medaudit.retrieval import BM25Index


def _load_synthetic(
    corpus_path: Path, cases_path: Path
) -> tuple[list[Chunk], list[dict[str, Any]]]:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    if corpus.get("schema_version") != 1 or cases.get("schema_version") != 1:
        raise ValueError("unsupported synthetic benchmark schema")
    return [Chunk(**item) for item in corpus["chunks"]], cases["cases"]


def wait_until_ready(base_url: str, *, timeout_seconds: float) -> None:
    """Wait for the local server without exposing any benchmark content."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(1)
    raise TimeoutError("local inference server did not become ready")


async def run_benchmark(
    chunks: list[Chunk],
    cases: list[dict[str, Any]],
    *,
    base_url: str,
    threshold: float,
    top_k: int,
) -> dict[str, Any]:
    """Measure structure and grounding without persisting generated text."""
    pipeline = EvidenceFirstPipeline(
        chunks=chunks,
        retriever=BM25Index(chunks),
        policy=FrozenTopScorePolicy(threshold=threshold),
    )
    client = LlamaCppClient(
        base_url=base_url,
        allowed_hosts=frozenset({"llm-server", "127.0.0.1", "localhost", "::1"}),
    )
    valid_outputs = 0
    correct_gates = 0
    relevant_citations = 0
    generated = 0
    latencies: list[float] = []
    for case in cases:
        relevant = set(case.get("relevant_chunk_ids", []))
        decision = pipeline.retrieve(case["question"], top_k=top_k)
        expected_generation = bool(relevant)
        correct_gates += decision.can_generate == expected_generation
        if not decision.can_generate:
            continue
        generated += 1
        response = await client.generate(build_grounded_request(decision))
        answer = validate_grounded_response(response, decision)
        valid_outputs += 1
        cited = {citation.chunk_id for citation in answer.citations}
        relevant_citations += bool(cited.intersection(relevant))
        latencies.append(response.latency_ms)
    return {
        "schema_version": 1,
        "dataset": "synthetic",
        "case_count": len(cases),
        "generated_case_count": generated,
        "metrics": {
            "gate_accuracy": correct_gates / len(cases),
            "structured_output_rate": valid_outputs / generated if generated else None,
            "relevant_citation_rate": (
                relevant_citations / generated if generated else None
            ),
            "mean_generation_latency_ms": (
                sum(latencies) / len(latencies) if latencies else None
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://llm-server:8080")
    parser.add_argument("--threshold", type=float, default=3.0)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--startup-timeout", type=float, default=180)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        chunks, cases = _load_synthetic(args.corpus, args.cases)
        wait_until_ready(args.base_url, timeout_seconds=args.startup_timeout)
        report = asyncio.run(
            run_benchmark(
                chunks,
                cases,
                base_url=args.base_url,
                threshold=args.threshold,
                top_k=args.top_k,
            )
        )
        write_private_report(report, args.output)
    except (
        OSError,
        TimeoutError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(json.dumps({**report, "succeeded": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
