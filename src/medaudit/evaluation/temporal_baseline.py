"""Run a private BM25 baseline across date-specific golden sets."""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.catalog.serialization import load_catalog
from medaudit.evaluation.private_bm25 import (
    evaluate_private,
    load_private_cases,
    load_private_chunks,
    validate_private_references,
    write_private_report,
)
from medaudit.evaluation.temporal_audit import (
    audit_temporal_references,
    load_golden_sets,
)
from medaudit.ingestion.corpus import process_catalog


def run_temporal_baseline(
    *,
    catalog_path: Path,
    input_root: Path,
    golden_directory: Path,
    output_directory: Path,
    top_k: int,
    min_score: float,
    enable_ocr: bool,
) -> dict[str, Any]:
    """Materialize, evaluate and consolidate all temporally valid snapshots."""
    golden_sets = load_golden_sets(golden_directory)
    temporal_audit = audit_temporal_references(
        golden_sets, load_catalog(catalog_path)
    )
    if not temporal_audit["ready"]:
        raise ValueError("temporal evaluation references are not ready")

    snapshots_directory = output_directory / "snapshots"
    reports_directory = output_directory / "reports"
    snapshot_reports: list[dict[str, Any]] = []
    total_chunks = 0
    for golden_set in golden_sets:
        snapshot_date = date.fromisoformat(golden_set["reference_date"])
        suffix = snapshot_date.isoformat()
        chunks_path = snapshots_directory / f"chunks-{suffix}.local.jsonl"
        report_path = reports_directory / f"bm25-{suffix}.local.json"
        processing = process_catalog(
            catalog_path,
            input_root,
            chunks_path,
            snapshot_date,
            enable_ocr=enable_ocr,
        )
        if not processing.succeeded:
            raise RuntimeError("a temporal snapshot could not be processed")
        chunks, chunk_date = load_private_chunks(chunks_path)
        cases_path = golden_directory / f"retrieval-{suffix}.local.json"
        cases, case_date = load_private_cases(cases_path)
        if chunk_date != case_date:
            raise ValueError("snapshot and golden set dates do not match")
        validate_private_references(chunks, cases)
        report = evaluate_private(
            chunks, cases, top_k=top_k, min_score=min_score
        )
        write_private_report(report, report_path)
        total_chunks += len(chunks)
        snapshot_reports.append(
            {
                "reference_date": suffix,
                "processing": asdict(processing),
                "evaluation": report,
            }
        )

    consolidated = consolidate_metrics(snapshot_reports, top_k)
    result = {
        "schema_version": 1,
        "retriever": "bm25",
        "top_k": top_k,
        "min_score": min_score,
        "snapshot_count": len(snapshot_reports),
        "materialized_chunk_count": total_chunks,
        **consolidated,
        "snapshots": snapshot_reports,
    }
    write_private_report(result, output_directory / "baseline.local.json")
    return result


def consolidate_metrics(
    snapshot_reports: list[dict[str, Any]], top_k: int
) -> dict[str, Any]:
    """Combine per-snapshot rates using their applicable case counts."""
    answerable = sum(
        item["evaluation"]["answerable_case_count"] for item in snapshot_reports
    )
    unanswerable = sum(
        item["evaluation"]["unanswerable_case_count"] for item in snapshot_reports
    )

    def weighted(metric: str, count_key: str, total: int) -> float | None:
        if not total:
            return None
        value = sum(
            (item["evaluation"]["metrics"][metric] or 0.0)
            * item["evaluation"][count_key]
            for item in snapshot_reports
        )
        return float(value / total)

    return {
        "case_count": answerable + unanswerable,
        "answerable_case_count": answerable,
        "unanswerable_case_count": unanswerable,
        "metrics": {
            f"hit_rate@{top_k}": weighted(
                f"hit_rate@{top_k}", "answerable_case_count", answerable
            ),
            f"recall@{top_k}": weighted(
                f"recall@{top_k}", "answerable_case_count", answerable
            ),
            "mrr": weighted("mrr", "answerable_case_count", answerable),
            "abstention_accuracy": weighted(
                "abstention_accuracy", "unanswerable_case_count", unanswerable
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--golden-sets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("--enable-ocr", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_temporal_baseline(
            catalog_path=args.catalog,
            input_root=args.input,
            golden_directory=args.golden_sets,
            output_directory=args.output,
            top_k=args.top_k,
            min_score=args.min_score,
            enable_ocr=args.enable_ocr,
        )
    except (KeyError, TypeError, ValueError, OSError, RuntimeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    summary = {key: value for key, value in result.items() if key != "snapshots"}
    summary["succeeded"] = True
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
