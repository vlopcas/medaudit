"""Diagnose calibration ranking deltas without exposing private content."""

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.private_bm25 import write_private_report

DIMENSIONS = ("category", "difficulty", "reasoning_type")


def diagnose_hybrid(
    benchmark: dict[str, Any], review: dict[str, Any]
) -> dict[str, Any]:
    """Compare dense and hybrid outcomes against BM25 by reviewed dimension."""
    if benchmark.get("schema_version") != 1:
        raise ValueError("unsupported hybrid benchmark schema")
    if benchmark.get("partition") != "calibration":
        raise ValueError("hybrid diagnostics require calibration results")
    metadata = {case["candidate_id"]: case for case in review["cases"]}
    if len(metadata) != len(review["cases"]):
        raise ValueError("duplicate reviewed case id")

    retrievers = benchmark["retrievers"]
    baseline = _answerable_by_id(retrievers["bm25"]["cases"])
    comparisons: dict[str, Any] = {}
    for name in ("dense", "hybrid_rrf"):
        candidate = _answerable_by_id(retrievers[name]["cases"])
        if set(candidate) != set(baseline):
            raise ValueError("retriever answerable cases do not match")
        if set(baseline) - set(metadata):
            raise ValueError("benchmark case is absent from review")
        groups: dict[str, defaultdict[str, list[tuple[float, float, float, float]]]] = {
            dimension: defaultdict(list) for dimension in DIMENSIONS
        }
        pairs: list[tuple[float, float, float, float]] = []
        for case_id in sorted(baseline):
            base = baseline[case_id]
            other = candidate[case_id]
            pair = (
                float(base["reciprocal_rank"]),
                float(other["reciprocal_rank"]),
                float(base["recall"]),
                float(other["recall"]),
            )
            pairs.append(pair)
            for dimension in DIMENSIONS:
                groups[dimension][metadata[case_id][dimension]].append(pair)
        comparisons[name] = {
            "overall": _summarize_pairs(pairs),
            "groups": {
                dimension: {
                    value: _summarize_pairs(items)
                    for value, items in sorted(values.items())
                }
                for dimension, values in groups.items()
            },
        }
    return {
        "schema_version": 1,
        "partition": "calibration",
        "baseline": "bm25",
        "answerable_case_count": len(baseline),
        "comparisons": comparisons,
    }


def _answerable_by_id(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    selected = {case["case_id"]: case for case in cases if case["answerable"]}
    if len(selected) != sum(bool(case["answerable"]) for case in cases):
        raise ValueError("duplicate answerable benchmark case id")
    return selected


def _summarize_pairs(
    pairs: list[tuple[float, float, float, float]],
) -> dict[str, int | float]:
    if not pairs:
        raise ValueError("diagnostic group must not be empty")
    mrr_deltas = [other - base for base, other, _, _ in pairs]
    recall_deltas = [other - base for _, _, base, other in pairs]
    return {
        "case_count": len(pairs),
        "mrr_win_count": sum(delta > 0 for delta in mrr_deltas),
        "mrr_tie_count": sum(delta == 0 for delta in mrr_deltas),
        "mrr_loss_count": sum(delta < 0 for delta in mrr_deltas),
        "mean_mrr_delta": sum(mrr_deltas) / len(pairs),
        "recall_win_count": sum(delta > 0 for delta in recall_deltas),
        "recall_tie_count": sum(delta == 0 for delta in recall_deltas),
        "recall_loss_count": sum(delta < 0 for delta in recall_deltas),
        "mean_recall_delta": sum(recall_deltas) / len(pairs),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        benchmark: dict[str, Any] = json.loads(
            args.benchmark.read_text(encoding="utf-8")
        )
        review: dict[str, Any] = json.loads(args.review.read_text(encoding="utf-8"))
        report = diagnose_hybrid(benchmark, review)
        write_private_report(report, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "answerable_case_count": report["answerable_case_count"],
                "comparison_count": len(report["comparisons"]),
                "partition": report["partition"],
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
