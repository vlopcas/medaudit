"""Diagnose private retrieval results without exposing case content."""

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.private_bm25 import write_private_report


def diagnose_baseline(
    baseline: dict[str, Any], review: dict[str, Any]
) -> dict[str, Any]:
    """Join reviewed metadata and case metrics into a private diagnostic."""
    metadata = {case["candidate_id"]: case for case in review["cases"]}
    results = [
        case
        for snapshot in baseline["snapshots"]
        for case in snapshot["evaluation"]["cases"]
    ]
    if len({case["case_id"] for case in results}) != len(results):
        raise ValueError("duplicate baseline case ids")
    if {case["case_id"] for case in results} != set(metadata):
        raise ValueError("baseline and review cases do not match")

    groups: dict[str, defaultdict[str, list[dict[str, Any]]]] = {
        "category": defaultdict(list),
        "difficulty": defaultdict(list),
        "reasoning_type": defaultdict(list),
    }
    cases: list[dict[str, Any]] = []
    zero_hit = 0
    partial_recall = 0
    incorrect_abstention = 0
    for result in results:
        source = metadata[result["case_id"]]
        answerable = source["answerability"] == "answerable"
        if answerable:
            reciprocal_rank = float(result["reciprocal_rank"])
            recall = float(result["recall"])
            zero_hit += reciprocal_rank == 0
            partial_recall += recall < 1
            normalized = {
                "case_id": result["case_id"],
                "answerable": True,
                "reciprocal_rank": reciprocal_rank,
                "recall": recall,
            }
        else:
            correct = bool(result["correct_abstention"])
            incorrect_abstention += not correct
            normalized = {
                "case_id": result["case_id"],
                "answerable": False,
                "correct_abstention": correct,
            }
        cases.append(normalized)
        for dimension in groups:
            groups[dimension][source[dimension]].append(normalized)

    return {
        "schema_version": 1,
        "case_count": len(results),
        "zero_hit_count": zero_hit,
        "partial_recall_count": partial_recall,
        "incorrect_abstention_count": incorrect_abstention,
        "group_count": sum(len(values) for values in groups.values()),
        "groups": {
            dimension: {
                name: _summarize(items)
                for name, items in sorted(values.items())
            }
            for dimension, values in groups.items()
        },
        "cases": cases,
    }


def _summarize(items: list[dict[str, Any]]) -> dict[str, int | float | None]:
    answerable = [item for item in items if item["answerable"]]
    unanswerable = [item for item in items if not item["answerable"]]
    return {
        "case_count": len(items),
        "answerable_count": len(answerable),
        "hit_rate": (
            sum(item["reciprocal_rank"] > 0 for item in answerable) / len(answerable)
            if answerable
            else None
        ),
        "mean_reciprocal_rank": (
            sum(item["reciprocal_rank"] for item in answerable) / len(answerable)
            if answerable
            else None
        ),
        "mean_recall": (
            sum(item["recall"] for item in answerable) / len(answerable)
            if answerable
            else None
        ),
        "abstention_accuracy": (
            sum(item["correct_abstention"] for item in unanswerable)
            / len(unanswerable)
            if unanswerable
            else None
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        baseline: dict[str, Any] = json.loads(
            args.baseline.read_text(encoding="utf-8")
        )
        review: dict[str, Any] = json.loads(args.review.read_text(encoding="utf-8"))
        report = diagnose_baseline(baseline, review)
        write_private_report(report, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    summary = {
        key: value
        for key, value in report.items()
        if key not in {"groups", "cases"}
    }
    summary["succeeded"] = True
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
