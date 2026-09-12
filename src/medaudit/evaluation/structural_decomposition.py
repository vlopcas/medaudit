"""Evaluate structural decomposition signals on synthetic queries."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.query_understanding import requires_structural_decomposition


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported structural decomposition dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("at least one structural decomposition case is required")
    identifiers = [case["id"] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("structural decomposition case ids must be unique")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not cases:
        raise ValueError("at least one structural decomposition case is required")
    true_positive = false_positive = true_negative = false_negative = 0
    outcomes: list[dict[str, Any]] = []
    for case in cases:
        expected = case["requires_decomposition"]
        if not isinstance(expected, bool):
            raise ValueError("requires_decomposition labels must be boolean")
        actual = requires_structural_decomposition(case["query"])
        true_positive += actual and expected
        false_positive += actual and not expected
        true_negative += not actual and not expected
        false_negative += not actual and expected
        outcomes.append(
            {"case_id": case["id"], "correct": actual is expected}
        )
    positives = true_positive + false_negative
    negatives = true_negative + false_positive
    predicted_positive = true_positive + false_positive
    return {
        "schema_version": 1,
        "analyzer": "structural-decomposition-v1",
        "case_count": len(cases),
        "metrics": {
            "accuracy": (true_positive + true_negative) / len(cases),
            "precision": (
                true_positive / predicted_positive if predicted_positive else None
            ),
            "recall": true_positive / positives if positives else None,
            "false_positive_rate": false_positive / negatives if negatives else None,
        },
        "confusion": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
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
        raise FileExistsError("structural evaluation output already exists")
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
