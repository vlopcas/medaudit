import unittest
from datetime import date
from typing import Any

import pymupdf

from medaudit.documents import Document
from medaudit.parsing import PDFParser


class PDFParserTest(unittest.TestCase):
    def test_extracts_synthetic_text_with_page_provenance(self) -> None:
        source: Any = pymupdf.open()  # type: ignore[no-untyped-call]
        first_page = source.new_page()
        first_page.insert_text((72, 72), "Synthetic rule PX-101")
        second_page = source.new_page()
        second_page.insert_text((72, 72), "Synthetic exception")
        content = source.tobytes()
        source.close()
        document = Document("pdf-v1", "Synthetic PDF", "1", date(2026, 1, 1))

        parsed = PDFParser().parse(document, content)

        self.assertEqual(len(parsed.elements), 2)
        self.assertEqual([element.page for element in parsed.elements], [1, 2])
        self.assertIn("PX-101", parsed.elements[0].text)
        self.assertIn("bbox", parsed.elements[0].metadata)

    def test_rejects_invalid_pdf(self) -> None:
        document = Document("pdf-v1", "Synthetic PDF", "1", date(2026, 1, 1))

        with self.assertRaisesRegex(ValueError, "invalid or unsupported PDF"):
            PDFParser().parse(document, b"not a pdf")
