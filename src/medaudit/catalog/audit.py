"""Privacy-safe audit of a reviewed catalog against the local corpus."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from medaudit.catalog.models import Catalog, ReviewStatus
from medaudit.catalog.serialization import load_catalog
from medaudit.ingestion.inventory import FileRecord, collect_inventory


@dataclass(frozen=True, slots=True)
class CatalogAudit:
    """Aggregate catalog health without private names or metadata."""

    document_count: int
    corpus_document_count: int
    status_counts: dict[str, int]
    effective_reviewed_count: int
    not_yet_effective_count: int
    expired_count: int
    untracked_content_count: int
    unavailable_content_count: int
    inconsistent_missing_status_count: int

    @property
    def ready(self) -> bool:
        """Return whether catalog and corpus agree and all sources are reviewed."""
        return (
            self.status_counts.get(ReviewStatus.PENDING.value, 0) == 0
            and self.untracked_content_count == 0
            and self.unavailable_content_count == 0
            and self.inconsistent_missing_status_count == 0
        )


def audit_catalog(
    catalog: Catalog, records: list[FileRecord], reference_date: date
) -> CatalogAudit:
    """Compare catalog identity and temporal state using aggregate counts only."""
    status_counts = Counter(entry.review_status.value for entry in catalog.entries)
    corpus_hashes = {record.sha256 for record in records}
    catalog_hashes = {entry.content_sha256 for entry in catalog.entries}
    effective = 0
    future = 0
    expired = 0
    inconsistent_missing = 0

    for entry in catalog.entries:
        available = entry.content_sha256 in corpus_hashes
        if entry.review_status is ReviewStatus.MISSING and available:
            inconsistent_missing += 1
        if entry.review_status is not ReviewStatus.REVIEWED:
            continue
        if entry.effective_from is not None and reference_date < entry.effective_from:
            future += 1
        elif (
            entry.effective_until is not None
            and reference_date > entry.effective_until
        ):
            expired += 1
        else:
            effective += 1

    return CatalogAudit(
        document_count=len(catalog.entries),
        corpus_document_count=len(corpus_hashes),
        status_counts=dict(sorted(status_counts.items())),
        effective_reviewed_count=effective,
        not_yet_effective_count=future,
        expired_count=expired,
        untracked_content_count=len(corpus_hashes - catalog_hashes),
        unavailable_content_count=len(catalog_hashes - corpus_hashes),
        inconsistent_missing_status_count=inconsistent_missing,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--reference-date", type=date.fromisoformat, default=date.today()
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a private catalog while printing aggregate information only."""
    args = build_parser().parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
        report = audit_catalog(
            catalog, collect_inventory(args.input), args.reference_date
        )
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "ready": False}))
        return 2
    payload = asdict(report)
    payload["ready"] = report.ready
    print(json.dumps(payload, sort_keys=True))
    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
