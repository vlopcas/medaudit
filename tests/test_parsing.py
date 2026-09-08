import unittest
from datetime import date

from medaudit.documents import Document, ElementKind
from medaudit.parsing import PlainTextParser


class PlainTextParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = Document("doc-v1", "Sintético", "1", date(2026, 1, 1))

    def test_preserves_sections_and_pages(self) -> None:
        content = (
            "# Regra sintética\n\nTexto da regra.\f"
            "## Exceção\n\nTexto da exceção."
        ).encode()

        parsed = PlainTextParser().parse(self.document, content)

        self.assertEqual(len(parsed.elements), 4)
        self.assertEqual(parsed.elements[0].kind, ElementKind.TITLE)
        self.assertEqual(parsed.elements[1].section, "Regra sintética")
        self.assertEqual(parsed.elements[2].page, 2)
        self.assertEqual(parsed.elements[3].section, "Exceção")

    def test_element_ids_are_deterministic(self) -> None:
        parser = PlainTextParser()
        first = parser.parse(self.document, b"Synthetic text")
        second = parser.parse(self.document, b"Synthetic text")

        self.assertEqual(first.elements[0].element_id, second.elements[0].element_id)

    def test_rejects_invalid_utf8(self) -> None:
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            PlainTextParser().parse(self.document, b"\xff")
