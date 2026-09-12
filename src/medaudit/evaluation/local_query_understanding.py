"""Benchmark local-LLM query semantics on synthetic queries only."""

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.local_llm_benchmark import wait_until_ready
from medaudit.evaluation.query_understanding import load_cases, verify_input
from medaudit.llm import LlamaCppClient
from medaudit.query_understanding import LocalLLMQueryAnalyzer


async def run_benchmark(cases_path: Path, *, base_url: str) -> dict[str, Any]:
    """Evaluate the hybrid analyzer without persisting query or response text."""
    cases = load_cases(cases_path)
    client = LlamaCppClient(
        base_url=base_url,
        allowed_hosts=frozenset({"llm-server", "127.0.0.1", "localhost", "::1"}),
    )
    analyzer = LocalLLMQueryAnalyzer(client)
    fields = (
        "intent",
        "reference_date",
        "procedure",
        "requires_external_data",
        "requires_decomposition",
    )
    correct = dict.fromkeys(fields, 0)
    case_results: list[dict[str, Any]] = []
    latencies: list[float] = []

    for case in cases:
        actual, response = await analyzer.analyze(case.query)
        expected = {
            "intent": case.intent,
            "reference_date": case.reference_date,
            "procedure": case.procedure,
            "requires_external_data": case.requires_external_data,
            "requires_decomposition": case.requires_decomposition,
        }
        matches = {
            field: getattr(actual, field) == value
            for field, value in expected.items()
        }
        for field, matched in matches.items():
            correct[field] += matched
        case_results.append(
            {
                "case_id": case.case_id,
                "all_fields_correct": all(matches.values()),
                "incorrect_fields": [
                    field for field, matched in matches.items() if not matched
                ],
            }
        )
        latencies.append(response.latency_ms)

    return {
        "schema_version": 1,
        "analyzer": "deterministic-extraction-local-llm-semantics-v1",
        "case_count": len(cases),
        "metrics": {
            "exact_match": sum(
                result["all_fields_correct"] for result in case_results
            )
            / len(cases),
            "accuracy_by_field": {
                field: count / len(cases) for field, count in correct.items()
            },
            "mean_generation_latency_ms": sum(latencies) / len(latencies),
        },
        "cases": case_results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://llm-server:8080")
    parser.add_argument("--startup-timeout", type=float, default=180)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    wait_until_ready(args.base_url, timeout_seconds=args.startup_timeout)
    report = asyncio.run(run_benchmark(args.cases, base_url=args.base_url))
    report["input_sha256"] = verify_input(args.cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"metrics": report["metrics"], "succeeded": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

