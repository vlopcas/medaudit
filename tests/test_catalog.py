import hashlib
import tempfile
import unittest
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.catalog import (
    Catalog,
    CatalogAccessError,
    CatalogEntry,
    CatalogRejection,
    ReviewStatus,
    document_from_reviewed_entry,
    validate_catalog,
)
from medaudit.catalog.audit import audit_catalog
from medaudit.catalog.builder import build_catalog
from medaudit.catalog.serialization import (
    load_catalog,
    parse_catalog_date,
    write_catalog,
)
from medaudit.ingestion.inventory import FileRecord


def entry(
    document_id: str = "doc-a",
    content_hash: str = "a" * 64,
    **changes: object,
) -> CatalogEntry:
    values: dict[str, object] = {
        "document_id": document_id,
        "content_sha256": content_hash,
        "relative_paths": ("synthetic.pdf",),
        "media_type": "application/pdf",
        "size_bytes": 10,
    }
    values.update(changes)
    return CatalogEntry(**values)  # type: ignore[arg-type]


class CatalogValidationTest(unittest.TestCase):
    def test_reviewed_entry_requires_semantic_metadata(self) -> None:
        catalog = Catalog(1, (entry(review_status=ReviewStatus.REVIEWED),))

        with self.assertRaisesRegex(ValueError, "is missing"):
            validate_catalog(catalog)

    def test_rejects_invalid_effective_period(self) -> None:
        catalog = Catalog(
            1,
            (
                entry(
                    effective_from=date(2026, 2, 1),
                    effective_until=date(2026, 1, 1),
                ),
            ),
        )

        with self.assertRaisesRegex(ValueError, "invalid effective period"):
            validate_catalog(catalog)

    def test_rejects_supersession_cycle(self) -> None:
        first = entry("doc-a", "a" * 64, supersedes=("doc-b",))
        second = entry("doc-b", "b" * 64, supersedes=("doc-a",))

        with self.assertRaisesRegex(ValueError, "cycle"):
            validate_catalog(Catalog(1, (first, second)))


class CatalogBuilderTest(unittest.TestCase):
    def test_refresh_preserves_reviewed_metadata_and_tracks_copies(self) -> None:
        reviewed = entry(
            review_status=ReviewStatus.REVIEWED,
            title="Synthetic policy",
            family="policy",
            organization="Synthetic Org",
            version="1",
            effective_from=date(2026, 1, 1),
        )
        records = [
            FileRecord("copy-b.pdf", ".pdf", 10, "ignored", "a" * 64),
            FileRecord("copy-a.pdf", ".pdf", 10, "ignored", "a" * 64),
        ]

        catalog = build_catalog(records, Catalog(1, (reviewed,)))

        self.assertEqual(len(catalog.entries), 1)
        self.assertEqual(catalog.entries[0].review_status, ReviewStatus.REVIEWED)
        self.assertEqual(
            catalog.entries[0].relative_paths, ("copy-a.pdf", "copy-b.pdf")
        )

    def test_catalog_round_trip(self) -> None:
        catalog = Catalog(1, (entry(effective_from=date(2026, 1, 1)),))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "catalog.local.json"

            write_catalog(catalog, output)
            loaded = load_catalog(output)

        self.assertEqual(loaded, catalog)

    def test_iso_timestamp_is_normalized_to_date(self) -> None:
        self.assertEqual(
            parse_catalog_date("2026-03-01T00:00:00Z"), date(2026, 3, 1)
        )

    def test_output_requires_private_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "catalog.json"

            with self.assertRaisesRegex(ValueError, "must end with .local.json"):
                write_catalog(Catalog(1, (entry(),)), output)


class CatalogAccessTest(unittest.TestCase):
    content = b"wholly synthetic policy content"
    content_hash = hashlib.sha256(content).hexdigest()

    def reviewed_entry(self, **changes: Any) -> CatalogEntry:
        return entry(
            content_hash=self.content_hash,
            review_status=ReviewStatus.REVIEWED,
            title="Synthetic policy",
            family="policy",
            organization="Synthetic Org",
            version="1",
            effective_from=date(2026, 1, 1),
            **changes,
        )

    def test_converts_reviewed_effective_matching_content(self) -> None:
        document = document_from_reviewed_entry(
            self.reviewed_entry(), self.content, date(2026, 2, 1)
        )

        self.assertEqual(document.document_id, "doc-a")
        self.assertEqual(document.metadata["organization"], "Synthetic Org")

    def test_rejects_pending_entry(self) -> None:
        pending = entry(content_hash=self.content_hash)

        with self.assertRaises(CatalogAccessError) as caught:
            document_from_reviewed_entry(pending, self.content, date(2026, 2, 1))

        self.assertEqual(caught.exception.reason, CatalogRejection.PENDING_REVIEW)

    def test_rejects_document_outside_effective_period(self) -> None:
        expired = self.reviewed_entry(effective_until=date(2026, 1, 31))

        with self.assertRaises(CatalogAccessError) as caught:
            document_from_reviewed_entry(expired, self.content, date(2026, 2, 1))

        self.assertEqual(caught.exception.reason, CatalogRejection.EXPIRED)

    def test_rejects_content_that_does_not_match_catalog(self) -> None:
        with self.assertRaises(CatalogAccessError) as caught:
            document_from_reviewed_entry(
                self.reviewed_entry(), b"changed", date(2026, 2, 1)
            )

        self.assertEqual(caught.exception.reason, CatalogRejection.CONTENT_MISMATCH)


class CatalogAuditTest(unittest.TestCase):
    def test_reports_only_aggregate_readiness(self) -> None:
        content_hash = "a" * 64
        reviewed = entry(
            content_hash=content_hash,
            review_status=ReviewStatus.REVIEWED,
            title="Synthetic policy",
            family="policy",
            organization="Synthetic Org",
            version="1",
            effective_from=date(2026, 1, 1),
        )
        records = [FileRecord("private.pdf", ".pdf", 10, "ignored", content_hash)]

        report = audit_catalog(Catalog(1, (reviewed,)), records, date(2026, 2, 1))

        self.assertTrue(report.ready)
        self.assertEqual(report.effective_reviewed_count, 1)
        self.assertFalse(hasattr(report, "relative_paths"))

    def test_detects_catalog_and_corpus_drift(self) -> None:
        records = [FileRecord("new.pdf", ".pdf", 10, "ignored", "b" * 64)]

        report = audit_catalog(Catalog(1, (entry(),)), records, date(2026, 2, 1))

        self.assertFalse(report.ready)
        self.assertEqual(report.untracked_content_count, 1)
        self.assertEqual(report.unavailable_content_count, 1)
