"""Analyze retrieval confidence signals on private temporal snapshots."""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from medaudit.evaluation.private_bm25 import (
    load_private_cases,
    load_private_chunks,
    write_private_report,
)
from medaudit.evaluation.split import validate_split
from medaudit.retrieval import (
    BM25Index,
    ConfidenceAnalyzer,
    ConfidenceSignals,
)

SIGNAL_NAMES = (
    "top_score",
    "normalized_margin",
    "query_coverage",
    "rare_query_coverage",
    "top_document_concentration",
    "result_count",
)


def analyze_temporal_confidence(
    snapshots_directory: Path,
    golden_directory: Path,
    review: dict[str, Any],
    *,
    top_k: int,
    selected_case_ids: set[str] | None = None,
    partition: str | None = None,
) -> dict[str, Any]:
    """Measure signal distributions without selecting a decision threshold."""
    review_by_id = {case["candidate_id"]: case for case in review["cases"]}
    cases_report: list[dict[str, Any]] = []
    seen_case_ids: set[str] = set()
    for cases_path in sorted(golden_directory.glob("retrieval-*.local.json")):
        suffix = cases_path.name.removeprefix("retrieval-").removesuffix(
            ".local.json"
        )
        cases, case_date = load_private_cases(cases_path)
        for case in cases:
            seen_case_ids.add(case.case_id)
            if case.case_id not in review_by_id:
                raise ValueError("confidence case is absent from review")
        selected_cases = [
            case
            for case in cases
            if selected_case_ids is None or case.case_id in selected_case_ids
        ]
        if not selected_cases:
            continue
        chunks_path = snapshots_directory / f"chunks-{suffix}.local.jsonl"
        if chunks_path.stat().st_size:
            chunks, chunk_date = load_private_chunks(chunks_path)
            if chunk_date != case_date:
                raise ValueError("snapshot and golden set dates do not match")
            index: BM25Index | None = BM25Index(chunks)
            analyzer: ConfidenceAnalyzer | None = ConfidenceAnalyzer(chunks)
        else:
            index = None
            analyzer = None
        for case in selected_cases:
            if index is None or analyzer is None:
                signals = asdict(ConfidenceSignals(0.0, 0.0, 0.0, None, 0.0, 0))
            else:
                results = index.search(case.question, top_k=top_k)
                signals = asdict(analyzer.analyze(case.question, results))
            reviewed = review_by_id[case.case_id]
            cases_report.append(
                {
                    "case_id": case.case_id,
                    "answerable": bool(
                        case.relevant_chunk_ids or case.relevant_document_ids
                    ),
                    "category": reviewed["category"],
                    "difficulty": reviewed["difficulty"],
                    "reasoning_type": reviewed["reasoning_type"],
                    "signals": signals,
                }
            )
    expected_case_ids = selected_case_ids or set(review_by_id)
    if seen_case_ids != set(review_by_id):
        raise ValueError("confidence analysis and review cases do not match")
    if {case["case_id"] for case in cases_report} != expected_case_ids:
        raise ValueError("confidence analysis partition does not match split")
    answerable = [case for case in cases_report if case["answerable"]]
    unanswerable = [case for case in cases_report if not case["answerable"]]
    return {
        "schema_version": 1,
        "top_k": top_k,
        "partition": partition,
        "case_count": len(cases_report),
        "answerable_case_count": len(answerable),
        "unanswerable_case_count": len(unanswerable),
        "signals": {
            name: {
                "answerable": _distribution(answerable, name),
                "unanswerable": _distribution(unanswerable, name),
                "answerable_greater_rate": _pairwise_rate(
                    answerable, unanswerable, name
                ),
            }
            for name in SIGNAL_NAMES
        },
        "cases": cases_report,
    }


def _values(cases: list[dict[str, Any]], name: str) -> list[float]:
    return [
        float(case["signals"][name])
        for case in cases
        if case["signals"][name] is not None
    ]


def _distribution(cases: list[dict[str, Any]], name: str) -> dict[str, Any]:
    values = sorted(_values(cases, name))
    if not values:
        return {"count": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "count": len(values),
        "min": values[0],
        "median": median(values),
        "mean": mean(values),
        "max": values[-1],
    }


def _pairwise_rate(
    answerable: list[dict[str, Any]],
    unanswerable: list[dict[str, Any]],
    name: str,
) -> float | None:
    positives = _values(answerable, name)
    negatives = _values(unanswerable, name)
    if not positives or not negatives:
        return None
    comparisons = [
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    ]
    return mean(comparisons)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--golden-sets", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--split", type=Path)
    parser.add_argument(
        "--partition", choices=("calibration", "evaluation")
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        review: dict[str, Any] = json.loads(args.review.read_text(encoding="utf-8"))
        if bool(args.split) != bool(args.partition):
            raise ValueError("split and partition must be provided together")
        selected_case_ids: set[str] | None = None
        if args.split:
            if args.partition is None:
                raise ValueError("split partition is required")
            split: dict[str, Any] = json.loads(args.split.read_text(encoding="utf-8"))
            validate_split(split, review)
            selected_case_ids = set(split["partitions"][args.partition])
        report = analyze_temporal_confidence(
            args.snapshots,
            args.golden_sets,
            review,
            top_k=args.top_k,
            selected_case_ids=selected_case_ids,
            partition=args.partition,
        )
        write_private_report(report, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "case_count": report["case_count"],
                "answerable_case_count": report["answerable_case_count"],
                "unanswerable_case_count": report["unanswerable_case_count"],
                "signal_count": len(report["signals"]),
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
