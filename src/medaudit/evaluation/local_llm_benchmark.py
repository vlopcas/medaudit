"""Run an end-to-end grounded-generation benchmark on synthetic data only."""

import argparse
import asyncio
import hashlib
import json
import time
import urllib.error
import urllib.request
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.evaluation.content_grade import grade_expected_content
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


def verify_input(path: Path, expected_sha256: str | None) -> str:
    """Hash a synthetic input and optionally enforce its frozen fingerprint."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("synthetic benchmark input fingerprint mismatch")
    return digest


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
    correct_statuses = 0
    correct_answers = 0
    matched_concepts = 0
    expected_concepts = 0
    citation_precision_sum = 0.0
    citation_recall_sum = 0.0
    grounded_generation_count = 0
    categories: defaultdict[str, dict[str, int]] = defaultdict(
        lambda: {
            "case_count": 0,
            "gate_correct": 0,
            "generated": 0,
            "status_correct": 0,
            "content_correct": 0,
            "relevant_citation": 0,
        }
    )
    generated = 0
    latencies: list[float] = []
    for case in cases:
        relevant = set(case.get("relevant_chunk_ids", []))
        expected = case.get("expected")
        if not isinstance(expected, dict) or expected.get("status") not in {
            "answered",
            "insufficient_evidence",
        }:
            raise ValueError("synthetic case requires an expected status")
        decision = pipeline.retrieve(case["question"], top_k=top_k)
        expected_generation = expected["status"] == "answered"
        correct_gates += decision.can_generate == expected_generation
        category = categories[str(case["category"])]
        category["case_count"] += 1
        category["gate_correct"] += decision.can_generate == expected_generation
        if not decision.can_generate:
            continue
        generated += 1
        category["generated"] += 1
        response = await client.generate(build_grounded_request(decision))
        answer = validate_grounded_response(response, decision)
        valid_outputs += 1
        correct_statuses += answer.status == expected["status"]
        category["status_correct"] += answer.status == expected["status"]
        cited = {citation.chunk_id for citation in answer.citations}
        citation_correct = bool(cited.intersection(relevant))
        relevant_citations += citation_correct
        category["relevant_citation"] += citation_correct
        if expected_generation:
            grounded_generation_count += 1
            citation_precision_sum += (
                len(cited.intersection(relevant)) / len(cited) if cited else 0.0
            )
            citation_recall_sum += len(cited.intersection(relevant)) / len(relevant)
            grade = grade_expected_content(answer.answer, expected)
            correct_answers += grade.correct
            matched_concepts += grade.matched_concept_count
            expected_concepts += grade.concept_count
            category["content_correct"] += grade.correct
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
            "citation_precision": (
                citation_precision_sum / grounded_generation_count
                if grounded_generation_count
                else None
            ),
            "citation_recall": (
                citation_recall_sum / grounded_generation_count
                if grounded_generation_count
                else None
            ),
            "response_status_accuracy": (
                correct_statuses / generated if generated else None
            ),
            "answer_content_accuracy": (
                correct_answers / generated if generated else None
            ),
            "required_concept_recall": (
                matched_concepts / expected_concepts if expected_concepts else None
            ),
            "mean_generation_latency_ms": (
                sum(latencies) / len(latencies) if latencies else None
            ),
        },
        "by_category": {
            name: values for name, values in sorted(categories.items())
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
    parser.add_argument("--expected-corpus-sha256")
    parser.add_argument("--expected-cases-sha256")
    parser.add_argument("--refuse-overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.refuse_overwrite and args.output.exists():
            raise FileExistsError("benchmark output already exists")
        corpus_sha256 = verify_input(args.corpus, args.expected_corpus_sha256)
        cases_sha256 = verify_input(args.cases, args.expected_cases_sha256)
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
        report["input_fingerprints"] = {
            "corpus_sha256": corpus_sha256,
            "cases_sha256": cases_sha256,
        }
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
