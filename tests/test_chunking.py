import unittest
from datetime import date

from medaudit.chunking import StructureAwareChunker
from medaudit.documents import Document, DocumentElement, ElementKind
from medaudit.parsing import ParsedDocument, PlainTextParser


class StructureAwareChunkerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = Document("doc-v1", "Sintético", "1", date(2026, 1, 1))

    def test_does_not_cross_section_or_page_boundary(self) -> None:
        parsed = PlainTextParser().parse(
            self.document,
            (
                "# Regra\n\nParágrafo um.\n\n## Exceção\n\n"
                "Parágrafo dois.\fPágina dois."
            ).encode(),
        )

        chunks = StructureAwareChunker(max_characters=1_000).chunk(parsed)

        self.assertEqual(len(chunks), 3)
        self.assertEqual(
            [chunk.section for chunk in chunks], ["Regra", "Exceção", "Exceção"]
        )
        self.assertEqual([chunk.page for chunk in chunks], [1, 1, 2])

    def test_respects_size_between_elements(self) -> None:
        parsed = PlainTextParser().parse(
            self.document, b"First synthetic paragraph.\n\nSecond synthetic paragraph."
        )

        chunks = StructureAwareChunker(max_characters=30).chunk(parsed)

        self.assertEqual(len(chunks), 2)

    def test_chunk_ids_are_deterministic(self) -> None:
        parsed = PlainTextParser().parse(self.document, b"Synthetic paragraph.")
        chunker = StructureAwareChunker()

        self.assertEqual(
            chunker.chunk(parsed)[0].chunk_id,
            chunker.chunk(parsed)[0].chunk_id,
        )

    def test_table_remains_an_atomic_chunk(self) -> None:
        parsed = ParsedDocument(
            document=self.document,
            elements=(
                DocumentElement(
                    "e1", "doc-v1", 0, ElementKind.PARAGRAPH, "Contexto", 1, "S1"
                ),
                DocumentElement(
                    "e2", "doc-v1", 1, ElementKind.TABLE, "A | B", 1, "S1"
                ),
                DocumentElement(
                    "e3", "doc-v1", 2, ElementKind.PARAGRAPH, "Conclusão", 1, "S1"
                ),
            ),
        )

        chunks = StructureAwareChunker(max_characters=1_000).chunk(parsed)

        self.assertEqual(
            [chunk.text for chunk in chunks],
            ["Contexto", "A | B", "Conclusão"],
        )
