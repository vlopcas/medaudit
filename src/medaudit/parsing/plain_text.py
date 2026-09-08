"""Deterministic parser used for synthetic fixtures and early experiments."""

import hashlib

from medaudit.documents import Document, DocumentElement, ElementKind
from medaudit.parsing.models import ParsedDocument


class PlainTextParser:
    """Parse UTF-8 text; form feeds delimit pages and Markdown headings sections."""

    supported_media_types = frozenset({"text/plain", "text/markdown"})

    def parse(self, document: Document, content: bytes) -> ParsedDocument:
        try:
            decoded = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("plain-text content must be valid UTF-8") from error

        elements: list[DocumentElement] = []
        section: str | None = None
        ordinal = 0
        for page, page_text in enumerate(decoded.split("\f"), start=1):
            for block in page_text.split("\n\n"):
                text = block.strip()
                if not text:
                    continue
                kind = ElementKind.PARAGRAPH
                if text.startswith("# "):
                    kind = (
                        ElementKind.TITLE if not elements else ElementKind.HEADING
                    )
                    text = text[2:].strip()
                    section = text
                elif text.startswith("## "):
                    kind = ElementKind.HEADING
                    text = text[3:].strip()
                    section = text
                elif text.startswith("- "):
                    kind = ElementKind.LIST_ITEM
                    text = text[2:].strip()

                elements.append(
                    DocumentElement(
                        element_id=self._element_id(
                            document.document_id, ordinal, text
                        ),
                        document_id=document.document_id,
                        ordinal=ordinal,
                        kind=kind,
                        text=text,
                        page=page,
                        section=section,
                    )
                )
                ordinal += 1
        return ParsedDocument(document=document, elements=tuple(elements))

    @staticmethod
    def _element_id(document_id: str, ordinal: int, text: str) -> str:
        value = f"{document_id}\0{ordinal}\0{text}".encode()
        return f"el-{hashlib.sha256(value).hexdigest()[:16]}"
