"""Boundary implemented by format-specific document parsers."""

from typing import Protocol

from medaudit.documents import Document
from medaudit.parsing.models import ParsedDocument


class DocumentParser(Protocol):
    """Convert source bytes into a normalized, provenance-aware document."""

    @property
    def supported_media_types(self) -> frozenset[str]:
        """Return media types accepted by this parser."""
        ...

    def parse(self, document: Document, content: bytes) -> ParsedDocument:
        """Parse bytes without performing network I/O."""
        ...
