"""Boundary implemented by chunking strategies."""

from typing import Protocol

from medaudit.documents import Chunk
from medaudit.parsing import ParsedDocument


class Chunker(Protocol):
    """Transform normalized document elements into retrievable chunks."""

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        """Create chunks while preserving source provenance."""
        ...
