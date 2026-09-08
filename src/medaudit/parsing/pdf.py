"""Local PDF text-block parser backed by PyMuPDF."""

import hashlib
from typing import Any

import pymupdf

from medaudit.documents import Document, DocumentElement, ElementKind
from medaudit.parsing.models import ParsedDocument


class PDFParser:
    """Extract ordered text blocks while retaining page and bounding boxes."""

    supported_media_types = frozenset({"application/pdf"})

    def parse(self, document: Document, content: bytes) -> ParsedDocument:
        elements: list[DocumentElement] = []
        try:
            pdf: Any = pymupdf.open(  # type: ignore[no-untyped-call]
                stream=content, filetype="pdf"
            )
        except Exception as error:
            raise ValueError("invalid or unsupported PDF content") from error

        try:
            if pdf.needs_pass:
                raise ValueError("encrypted PDF requires a password")
            ordinal = 0
            for page_number, page in enumerate(pdf, start=1):
                for block in page.get_text("blocks", sort=True):
                    if int(block[6]) != 0:
                        continue
                    text = str(block[4]).strip()
                    if not text:
                        continue
                    coordinates = tuple(round(float(value), 2) for value in block[:4])
                    elements.append(
                        DocumentElement(
                            element_id=_element_id(
                                document.document_id, ordinal, text
                            ),
                            document_id=document.document_id,
                            ordinal=ordinal,
                            kind=ElementKind.PARAGRAPH,
                            text=text,
                            page=page_number,
                            metadata={
                                "bbox": ",".join(map(str, coordinates)),
                                "parser": "pymupdf-blocks-v1",
                            },
                        )
                    )
                    ordinal += 1
        finally:
            pdf.close()
        return ParsedDocument(document=document, elements=tuple(elements))


def _element_id(document_id: str, ordinal: int, text: str) -> str:
    value = f"{document_id}\0{ordinal}\0{text}".encode()
    return f"el-{hashlib.sha256(value).hexdigest()[:16]}"
