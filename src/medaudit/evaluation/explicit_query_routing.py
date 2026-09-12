"""Evaluate the narrow explicit query-routing policy."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.query_understanding import ExplicitQueryRouter, QueryRoute


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != "explicit-routing-v1"
    ):
        raise ValueError("unsupported explicit routing dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("at least one explicit routing case is required")
    identifiers = [case["id"] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("explicit routing case ids must be unique")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not cases:
        raise ValueError("at least one explicit routing case is required")
    router = ExplicitQueryRouter()
    expected_counts: Counter[str] = Counter()
    correct_counts: Counter[str] = Counter()
    outcomes: list[dict[str, Any]] = []
    for case in cases:
        expected = QueryRoute(case["route"])
        actual = router.route(case["query"])
        correct = actual is expected
        expected_counts[expected.value] += 1
        correct_counts[expected.value] += correct
        outcomes.append(
            {
                "case_id": case["id"],
                "correct": correct,
                "expected_route": expected.value,
                "actual_route": actual.value,
            }
        )
    return {
        "schema_version": 1,
        "policy": "explicit-routing-v1",
        "case_count": len(cases),
        "metrics": {
            "accuracy": sum(item["correct"] for item in outcomes) / len(cases),
            "accuracy_by_expected_route": {
                route: correct_counts[route] / count
                for route, count in sorted(expected_counts.items())
            },
        },
        "cases": outcomes,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--refuse-overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.output and args.refuse_overwrite and args.output.exists():
        raise FileExistsError("explicit routing output already exists")
    report = evaluate(load_cases(args.cases))
    report["input_sha256"] = verify_input(args.cases, args.expected_sha256)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
