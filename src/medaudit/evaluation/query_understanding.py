"""Evaluate deterministic query understanding on a synthetic golden set."""

import argparse
import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.query_understanding import DeterministicQueryAnalyzer, QueryIntent


@dataclass(frozen=True, slots=True)
class QueryUnderstandingCase:
    """Expected routing signals for one synthetic query."""

    case_id: str
    query: str
    intent: QueryIntent
    reference_date: date | None
    procedure: str | None
    requires_external_data: bool
    requires_decomposition: bool


def load_cases(path: Path) -> list[QueryUnderstandingCase]:
    """Load and validate the public synthetic evaluation cases."""
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported query-understanding dataset schema")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("at least one query-understanding case is required")

    cases: list[QueryUnderstandingCase] = []
    seen: set[str] = set()
    for item in raw_cases:
        case_id = item["id"]
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        raw_date = item.get("reference_date")
        cases.append(
            QueryUnderstandingCase(
                case_id=case_id,
                query=item["query"],
                intent=QueryIntent(item["intent"]),
                reference_date=date.fromisoformat(raw_date) if raw_date else None,
                procedure=item.get("procedure"),
                requires_external_data=item["requires_external_data"],
                requires_decomposition=item["requires_decomposition"],
            )
        )
    return cases


def evaluate_query_understanding(
    cases: list[QueryUnderstandingCase],
    analyzer: DeterministicQueryAnalyzer | None = None,
) -> dict[str, Any]:
    """Compare every supported output field with its expected value."""
    if not cases:
        raise ValueError("at least one query-understanding case is required")
    analyzer = analyzer or DeterministicQueryAnalyzer()
    fields = (
        "intent",
        "reference_date",
        "procedure",
        "requires_external_data",
        "requires_decomposition",
    )
    correct = dict.fromkeys(fields, 0)
    case_results: list[dict[str, Any]] = []

    for case in cases:
        actual = analyzer.analyze(case.query)
        expected_values = {
            "intent": case.intent,
            "reference_date": case.reference_date,
            "procedure": case.procedure,
            "requires_external_data": case.requires_external_data,
            "requires_decomposition": case.requires_decomposition,
        }
        matches = {
            field: getattr(actual, field) == expected
            for field, expected in expected_values.items()
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

    return {
        "schema_version": 1,
        "analyzer": "deterministic-v1",
        "case_count": len(cases),
        "metrics": {
            "exact_match": sum(
                result["all_fields_correct"] for result in case_results
            )
            / len(cases),
            "accuracy_by_field": {
                field: count / len(cases) for field, count in correct.items()
            },
        },
        "cases": case_results,
    }


def verify_input(path: Path, expected_sha256: str | None = None) -> str:
    """Fingerprint a dataset and optionally enforce a frozen digest."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("query-understanding dataset fingerprint mismatch")
    return digest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--refuse-overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.output and args.refuse_overwrite and args.output.exists():
        raise FileExistsError("evaluation output already exists")
    fingerprint = verify_input(args.cases, args.expected_sha256)
    report = evaluate_query_understanding(load_cases(args.cases))
    report["input_sha256"] = fingerprint
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
