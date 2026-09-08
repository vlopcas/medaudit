import tempfile
import unittest
from datetime import date
from pathlib import Path

from medaudit.catalog import Catalog, CatalogEntry, ReviewStatus, validate_catalog
from medaudit.catalog.builder import build_catalog
from medaudit.catalog.serialization import load_catalog, write_catalog
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

    def test_output_requires_private_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "catalog.json"

            with self.assertRaisesRegex(ValueError, "must end with .local.json"):
                write_catalog(Catalog(1, (entry(),)), output)
