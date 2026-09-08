import unittest
from datetime import date
from typing import Any

import pymupdf

from medaudit.documents import Document
from medaudit.parsing import OCRFallbackPDFParser


class FakeOCRProvider:
    name = "fake-ocr-v1"

    def __init__(self, *, available: bool = True):
        self.available = available
        self.requested_pages: list[int] = []

    def is_available(self) -> bool:
        return self.available

    def extract_page(self, content: bytes, page_number: int) -> str:
        self.requested_pages.append(page_number)
        return f"Synthetic OCR page {page_number}"


def synthetic_mixed_pdf() -> bytes:
    pdf: Any = pymupdf.open()  # type: ignore[no-untyped-call]
    pdf.new_page()
    text_page = pdf.new_page()
    text_page.insert_text((72, 72), "Native synthetic text")
    content = bytes(pdf.tobytes())
    pdf.close()
    return content


class OCRFallbackPDFParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.document = Document("pdf-v1", "Synthetic PDF", "1", date(2026, 1, 1))

    def test_ocr_runs_only_for_page_without_native_text(self) -> None:
        provider = FakeOCRProvider()

        parsed = OCRFallbackPDFParser(provider).parse(
            self.document, synthetic_mixed_pdf()
        )

        self.assertEqual(provider.requested_pages, [1])
        self.assertEqual([element.page for element in parsed.elements], [1, 2])
        self.assertEqual(parsed.elements[0].metadata["ocr_provider"], "fake-ocr-v1")
        self.assertNotIn("ocr_provider", parsed.elements[1].metadata)

    def test_missing_local_provider_fails_explicitly(self) -> None:
        provider = FakeOCRProvider(available=False)

        with self.assertRaisesRegex(RuntimeError, "provider is unavailable"):
            OCRFallbackPDFParser(provider).parse(
                self.document, synthetic_mixed_pdf()
            )
