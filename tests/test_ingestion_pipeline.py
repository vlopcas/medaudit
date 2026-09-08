import hashlib
import json
import unittest
from datetime import date

from medaudit.catalog import CatalogAccessError, CatalogEntry, ReviewStatus
from medaudit.chunking import StructureAwareChunker
from medaudit.documents import Document
from medaudit.ingestion import IngestionPipeline, ParserRegistry
from medaudit.ingestion.serialization import serialize_result
from medaudit.parsing import PlainTextParser


class ParserRegistryTest(unittest.TestCase):
    def test_normalizes_media_type_and_ignores_parameters(self) -> None:
        parser = PlainTextParser()
        registry = ParserRegistry([parser])

        self.assertIs(registry.get(" Text/Plain; charset=UTF-8 "), parser)

    def test_rejects_unsupported_media_type(self) -> None:
        registry = ParserRegistry([PlainTextParser()])

        with self.assertRaisesRegex(ValueError, "unsupported media type"):
            registry.get("application/pdf")

    def test_rejects_ambiguous_registration(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate parser"):
            ParserRegistry([PlainTextParser(), PlainTextParser()])


class IngestionPipelineTest(unittest.TestCase):
    def test_parse_chunk_and_serialize(self) -> None:
        document = Document(
            document_id="synthetic-v1",
            title="Documento sintético",
            version="1",
            effective_from=date(2026, 1, 1),
        )
        pipeline = IngestionPipeline(
            ParserRegistry([PlainTextParser()]),
            StructureAwareChunker(max_characters=500),
        )

        result = pipeline.ingest(
            document,
            "# Regra\n\nO código PX-101 exige autorização.".encode(),
            "text/markdown",
        )
        payload = json.loads(serialize_result(result))

        self.assertEqual(result.schema_version, 1)
        self.assertEqual(len(result.chunks), 1)
        self.assertEqual(payload["parsed_document"]["document"]["version"], "1")
        self.assertEqual(
            payload["parsed_document"]["document"]["effective_from"],
            "2026-01-01",
        )

    def test_catalog_ingestion_enforces_review_and_integrity(self) -> None:
        content = b"Synthetic evidence."
        catalog_entry = CatalogEntry(
            document_id="synthetic-v1",
            content_sha256=hashlib.sha256(content).hexdigest(),
            relative_paths=("synthetic.txt",),
            media_type="text/plain",
            size_bytes=len(content),
            review_status=ReviewStatus.REVIEWED,
            title="Synthetic evidence",
            family="policy",
            organization="Synthetic Org",
            version="1",
            effective_from=date(2026, 1, 1),
        )
        pipeline = IngestionPipeline(
            ParserRegistry([PlainTextParser()]),
            StructureAwareChunker(max_characters=500),
        )

        result = pipeline.ingest_catalog_entry(
            catalog_entry, content, date(2026, 2, 1)
        )

        self.assertEqual(result.parsed_document.document.document_id, "synthetic-v1")
        with self.assertRaises(CatalogAccessError):
            pipeline.ingest_catalog_entry(
                catalog_entry, b"modified", date(2026, 2, 1)
            )
