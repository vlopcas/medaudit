import unittest
from datetime import date

from medaudit.chunking import FormatAwareChunker, StructureAwareChunker
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


class FormatAwareChunkerTest(unittest.TestCase):
    def test_groups_spreadsheet_rows_and_repeats_header(self) -> None:
        document = Document("sheet-v1", "Synthetic", "1", date(2026, 1, 1))
        parsed = ParsedDocument(
            document=document,
            elements=tuple(
                DocumentElement(
                    f"e{row}",
                    "sheet-v1",
                    row - 1,
                    ElementKind.TABLE,
                    text,
                    section="Rules",
                    metadata={
                        "sheet": "Rules",
                        "row": str(row),
                        "parser": "openpyxl-rows-v1",
                    },
                )
                for row, text in enumerate(
                    ["Code\tLimit", "PX-101\t2", "PX-102\t3", "PX-103\t4"],
                    start=1,
                )
            ),
        )

        chunks = FormatAwareChunker(max_characters=30).chunk(parsed)

        self.assertEqual(len(chunks), 2)
        self.assertTrue(all(chunk.text.startswith("Code\tLimit\n") for chunk in chunks))
        self.assertEqual(chunks[0].metadata["row_start"], "2")
        self.assertEqual(chunks[0].metadata["row_end"], "3")
        self.assertEqual(chunks[1].metadata["row_start"], "4")
        self.assertEqual(chunks[0].metadata["strategy"], "spreadsheet-rows-v1")

    def test_groups_non_empty_rows_across_formatting_gaps(self) -> None:
        document = Document("sheet-v1", "Synthetic", "1", date(2026, 1, 1))
        elements = (
            self.row("header", 1, 0),
            self.row("first", 2, 1),
            self.row("after gap", 4, 2),
        )

        chunks = FormatAwareChunker(max_characters=1_000).chunk(
            ParsedDocument(document, elements)
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].metadata["row_start"], "2")
        self.assertEqual(chunks[0].metadata["row_end"], "4")

    def test_does_not_repeat_an_oversized_first_row(self) -> None:
        document = Document("sheet-v1", "Synthetic", "1", date(2026, 1, 1))
        elements = (
            self.row("H" * 301, 1, 0),
            self.row("first", 2, 1),
            self.row("second", 3, 2),
        )

        chunks = FormatAwareChunker(max_characters=1_000).chunk(
            ParsedDocument(document, elements)
        )

        self.assertEqual(len(chunks), 1)
        self.assertNotIn("header_row", chunks[0].metadata)
        self.assertEqual(chunks[0].text.count("H" * 301), 1)

    @staticmethod
    def row(text: str, row: int, ordinal: int) -> DocumentElement:
        return DocumentElement(
            f"e{row}",
            "sheet-v1",
            ordinal,
            ElementKind.TABLE,
            text,
            section="Rules",
            metadata={
                "sheet": "Rules",
                "row": str(row),
                "parser": "openpyxl-rows-v1",
            },
        )
