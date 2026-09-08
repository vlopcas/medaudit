"""Explicit, local OCR fallback for PDF pages without extractable text."""

import hashlib
import shutil
from dataclasses import replace
from typing import Any, Protocol

import pymupdf

from medaudit.documents import Document, DocumentElement, ElementKind
from medaudit.parsing.models import ParsedDocument
from medaudit.parsing.pdf import PDFParser, get_pdf_page_count


class OCRProvider(Protocol):
    """Local OCR engine boundary used by the fallback parser."""

    @property
    def name(self) -> str:
        """Stable provider name stored in provenance."""
        ...

    def is_available(self) -> bool:
        """Return whether local OCR dependencies are ready."""
        ...

    def extract_page(self, content: bytes, page_number: int) -> str:
        """Extract text from one one-based PDF page."""
        ...


class TesseractOCRProvider:
    """Use PyMuPDF's local Tesseract integration for full-page OCR."""

    name = "tesseract-pymupdf-v1"

    def __init__(self, *, language: str = "por", dpi: int = 300):
        if not language.strip():
            raise ValueError("OCR language cannot be blank")
        if dpi <= 0:
            raise ValueError("OCR dpi must be positive")
        self._language = language
        self._dpi = dpi

    def is_available(self) -> bool:
        return shutil.which("tesseract") is not None

    def extract_page(self, content: bytes, page_number: int) -> str:
        if not self.is_available():
            raise RuntimeError("local Tesseract executable is not available")
        pdf: Any = pymupdf.open(  # type: ignore[no-untyped-call]
            stream=content, filetype="pdf"
        )
        try:
            if page_number < 1 or page_number > pdf.page_count:
                raise ValueError("OCR page number is outside the document")
            page = pdf[page_number - 1]
            text_page = page.get_textpage_ocr(
                language=self._language,
                dpi=self._dpi,
                full=True,
            )
            return str(page.get_text("text", textpage=text_page, sort=True)).strip()
        finally:
            pdf.close()


class OCRFallbackPDFParser:
    """Apply OCR only to pages where normal PDF extraction returned no text."""

    supported_media_types = frozenset({"application/pdf"})

    def __init__(self, provider: OCRProvider, primary: PDFParser | None = None):
        self._provider = provider
        self._primary = primary or PDFParser()

    def parse(self, document: Document, content: bytes) -> ParsedDocument:
        parsed = self._primary.parse(document, content)
        page_count = get_pdf_page_count(content)
        text_pages = {element.page for element in parsed.elements}
        missing_pages = [
            page_number
            for page_number in range(1, page_count + 1)
            if page_number not in text_pages
        ]
        if missing_pages and not self._provider.is_available():
            raise RuntimeError("OCR is required but the local provider is unavailable")

        elements = list(parsed.elements)
        for page_number in missing_pages:
            text = self._provider.extract_page(content, page_number).strip()
            if not text:
                continue
            elements.append(
                DocumentElement(
                    element_id=_ocr_element_id(
                        document.document_id, page_number, self._provider.name, text
                    ),
                    document_id=document.document_id,
                    ordinal=len(elements),
                    kind=ElementKind.PARAGRAPH,
                    text=text,
                    page=page_number,
                    metadata={
                        "parser": "ocr-fallback-v1",
                        "ocr_provider": self._provider.name,
                    },
                )
            )

        ordered = sorted(
            elements, key=lambda element: (element.page or 0, element.ordinal)
        )
        normalized = tuple(
            replace(element, ordinal=ordinal)
            for ordinal, element in enumerate(ordered)
        )
        return ParsedDocument(document=document, elements=normalized)


def _ocr_element_id(
    document_id: str, page_number: int, provider: str, text: str
) -> str:
    value = f"{document_id}\0{page_number}\0{provider}\0{text}".encode()
    return f"el-{hashlib.sha256(value).hexdigest()[:16]}"
