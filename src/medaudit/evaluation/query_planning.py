"""Evaluate deterministic query decomposition plans."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.query_understanding import DeterministicQueryPlanner, QueryPlan


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != "deterministic-query-planning-v1"
    ):
        raise ValueError("unsupported query planning dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("at least one query planning case is required")
    identifiers = [case["id"] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("query planning case ids must be unique")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not cases:
        raise ValueError("at least one query planning case is required")
    planner = DeterministicQueryPlanner()
    expected_counts: Counter[str] = Counter()
    correct_counts: Counter[str] = Counter()
    outcomes: list[dict[str, Any]] = []
    for case in cases:
        plan = planner.plan(case["query"])
        actual = _observable_plan(plan)
        expected = {
            "status": case["status"],
            "strategy": case.get("strategy"),
            "step_count": case["step_count"],
            "reference_dates": case.get("reference_dates", []),
            "scopes": case.get("scopes", []),
        }
        correct = actual == expected
        expected_counts[case["status"]] += 1
        correct_counts[case["status"]] += correct
        outcomes.append(
            {
                "case_id": case["id"],
                "correct": correct,
                "expected": expected,
                "actual": actual,
            }
        )
    return {
        "schema_version": 1,
        "policy": "deterministic-query-planning-v1",
        "case_count": len(cases),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes) / len(cases),
            "exact_match_by_expected_status": {
                status: correct_counts[status] / count
                for status, count in sorted(expected_counts.items())
            },
        },
        "cases": outcomes,
    }


def _observable_plan(plan: QueryPlan) -> dict[str, Any]:
    return {
        "status": plan.status.value,
        "strategy": plan.strategy.value if plan.strategy is not None else None,
        "step_count": len(plan.steps),
        "reference_dates": [
            step.reference_date.isoformat()
            for step in plan.steps
            if step.reference_date is not None
        ],
        "scopes": [step.scope for step in plan.steps if step.scope is not None],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--refuse-overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.output and args.refuse_overwrite and args.output.exists():
        raise FileExistsError("query planning output already exists")
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
