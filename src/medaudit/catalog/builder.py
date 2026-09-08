"""Build or refresh a private metadata catalog without guessing semantics."""

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from medaudit.catalog.models import Catalog, CatalogEntry, ReviewStatus
from medaudit.catalog.serialization import load_catalog, write_catalog
from medaudit.ingestion.inventory import FileRecord, collect_inventory

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def build_catalog(
    records: list[FileRecord], existing: Catalog | None = None
) -> Catalog:
    """Refresh technical fields while preserving reviewed human metadata."""
    grouped: dict[str, list[FileRecord]] = defaultdict(list)
    for record in records:
        grouped[record.sha256].append(record)
    previous = {
        entry.content_sha256: entry for entry in existing.entries
    } if existing else {}
    entries: list[CatalogEntry] = []

    for content_hash, copies in sorted(grouped.items()):
        paths = tuple(sorted(record.relative_path for record in copies))
        size_bytes = copies[0].size_bytes
        if content_hash in previous:
            entries.append(
                replace(
                    previous[content_hash],
                    relative_paths=paths,
                    media_type=MEDIA_TYPES[copies[0].extension],
                    size_bytes=size_bytes,
                    review_status=(
                        ReviewStatus.PENDING
                        if previous[content_hash].review_status is ReviewStatus.MISSING
                        else previous[content_hash].review_status
                    ),
                )
            )
        else:
            entries.append(
                CatalogEntry(
                    document_id=f"doc-{content_hash[:16]}",
                    content_sha256=content_hash,
                    relative_paths=paths,
                    media_type=MEDIA_TYPES[copies[0].extension],
                    size_bytes=size_bytes,
                )
            )

    current_hashes = set(grouped)
    for content_hash, entry in previous.items():
        if content_hash not in current_hashes:
            entries.append(replace(entry, review_status=ReviewStatus.MISSING))
    entries.sort(key=lambda entry: entry.document_id)
    return Catalog(schema_version=1, entries=tuple(entries))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Refresh a local catalog and print only non-sensitive counts."""
    args = build_parser().parse_args(argv)
    if not args.input.is_dir():
        raise SystemExit("input directory does not exist")
    existing = load_catalog(args.output) if args.output.exists() else None
    catalog = build_catalog(collect_inventory(args.input), existing)
    write_catalog(catalog, args.output)
    counts: dict[str, int] = defaultdict(int)
    for entry in catalog.entries:
        counts[entry.review_status.value] += 1
    summary = {"document_count": len(catalog.entries), "status": counts}
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
