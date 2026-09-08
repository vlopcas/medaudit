"""Core document models independent of parsers and storage engines."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class ElementKind(StrEnum):
    """Semantic type preserved by a document parser."""

    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    FIGURE = "figure"


@dataclass(frozen=True, slots=True)
class Document:
    """A versioned source document with provenance metadata."""

    document_id: str
    title: str
    version: str
    effective_from: date
    effective_until: date | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def is_effective_on(self, reference_date: date) -> bool:
        """Return whether this version applies on the given date, inclusively."""
        return self.effective_from <= reference_date and (
            self.effective_until is None or reference_date <= self.effective_until
        )


@dataclass(frozen=True, slots=True)
class Chunk:
    """A retrievable passage that retains its source location."""

    chunk_id: str
    document_id: str
    text: str
    page: int | None = None
    section: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DocumentElement:
    """Normalized parser output before a chunking strategy is applied."""

    element_id: str
    document_id: str
    ordinal: int
    kind: ElementKind
    text: str
    page: int | None = None
    section: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise ValueError("ordinal cannot be negative")
        if not self.text.strip():
            raise ValueError("element text cannot be blank")
