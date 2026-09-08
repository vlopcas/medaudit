import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from medaudit.catalog import Catalog, CatalogEntry, ReviewStatus
from medaudit.catalog.serialization import write_catalog
from medaudit.chunking import StructureAwareChunker
from medaudit.ingestion import IngestionPipeline, ParserRegistry
from medaudit.ingestion.corpus import _resolve_source, process_catalog
from medaudit.parsing import PlainTextParser


class CorpusProcessingTest(unittest.TestCase):
    def test_processes_only_effective_reviewed_documents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = b"Synthetic evidence for PX-101."
            (root / "source.txt").write_bytes(content)
            active = self.entry(
                "active",
                hashlib.sha256(content).hexdigest(),
                ("source.txt",),
            )
            expired = self.entry(
                "expired",
                "b" * 64,
                ("absent.txt",),
                effective_until=date(2026, 1, 31),
            )
            catalog_path = root / "catalog.local.json"
            output = root / "chunks.local.jsonl"
            write_catalog(Catalog(1, (active, expired)), catalog_path)
            pipeline = IngestionPipeline(
                ParserRegistry([PlainTextParser()]),
                StructureAwareChunker(max_characters=500),
            )

            summary = process_catalog(
                catalog_path,
                root,
                output,
                date(2026, 2, 1),
                pipeline=pipeline,
            )

            records = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertTrue(summary.succeeded)
            self.assertEqual(summary.processed_document_count, 1)
            self.assertEqual(summary.status_counts["expired"], 1)
            self.assertEqual(records[0]["document"]["document_id"], "active")
            self.assertIn("Synthetic evidence", records[0]["chunk"]["text"])

    def test_rejects_output_without_private_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "must end with .local.jsonl"):
                process_catalog(
                    Path(directory) / "catalog.local.json",
                    Path(directory),
                    Path(directory) / "chunks.jsonl",
                    date(2026, 1, 1),
                )

    def test_resolves_renamed_source_by_catalog_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "current.pdf"
            source.write_bytes(b"synthetic")
            catalog_entry = self.entry("doc", "a" * 64, ("old.pdf",))

            resolved = _resolve_source(
                catalog_entry, root, {catalog_entry.content_sha256: "current.pdf"}
            )

            self.assertEqual(resolved, source)

    @staticmethod
    def entry(
        document_id: str,
        content_hash: str,
        paths: tuple[str, ...],
        *,
        effective_until: date | None = None,
    ) -> CatalogEntry:
        return CatalogEntry(
            document_id=document_id,
            content_sha256=content_hash,
            relative_paths=paths,
            media_type="text/plain",
            size_bytes=10,
            review_status=ReviewStatus.REVIEWED,
            title="Synthetic policy",
            family="policy",
            organization="Synthetic Org",
            version="1",
            effective_from=date(2026, 1, 1),
            effective_until=effective_until,
        )
