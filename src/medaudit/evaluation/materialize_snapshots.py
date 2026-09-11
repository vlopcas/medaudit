"""Materialize temporal corpus snapshots without executing evaluation queries."""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.catalog.serialization import load_catalog
from medaudit.evaluation.temporal_audit import (
    audit_temporal_references,
    load_golden_sets,
)
from medaudit.ingestion.corpus import process_catalog


def materialize_snapshots(
    *,
    catalog_path: Path,
    input_root: Path,
    golden_directory: Path,
    output_directory: Path,
    enable_ocr: bool,
) -> dict[str, Any]:
    """Create one corpus snapshot per audited golden-set reference date."""
    golden_sets = load_golden_sets(golden_directory)
    audit = audit_temporal_references(golden_sets, load_catalog(catalog_path))
    if not audit["ready"]:
        raise ValueError("temporal evaluation references are not ready")

    summaries = []
    total_chunks = 0
    empty_snapshots = 0
    for golden_set in golden_sets:
        snapshot_date = date.fromisoformat(golden_set["reference_date"])
        output = output_directory / f"chunks-{snapshot_date.isoformat()}.local.jsonl"
        summary = process_catalog(
            catalog_path,
            input_root,
            output,
            snapshot_date,
            enable_ocr=enable_ocr,
        )
        if not summary.succeeded:
            raise RuntimeError("a temporal snapshot could not be processed")
        total_chunks += summary.chunk_count
        empty_snapshots += summary.chunk_count == 0
        summaries.append(
            {"reference_date": snapshot_date.isoformat(), **asdict(summary)}
        )
    return {
        "schema_version": 1,
        "snapshot_count": len(summaries),
        "materialized_chunk_count": total_chunks,
        "empty_snapshot_count": empty_snapshots,
        "snapshots": summaries,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--golden-sets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--enable-ocr", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = materialize_snapshots(
            catalog_path=args.catalog,
            input_root=args.input,
            golden_directory=args.golden_sets,
            output_directory=args.output,
            enable_ocr=args.enable_ocr,
        )
    except (KeyError, TypeError, ValueError, OSError, RuntimeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "materialized_chunk_count": result["materialized_chunk_count"],
                "empty_snapshot_count": result["empty_snapshot_count"],
                "snapshot_count": result["snapshot_count"],
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
