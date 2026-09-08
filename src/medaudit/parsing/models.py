"""Parser output models."""

from dataclasses import dataclass

from medaudit.documents import Document, DocumentElement


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """A source document and its ordered normalized elements."""

    document: Document
    elements: tuple[DocumentElement, ...]

    def __post_init__(self) -> None:
        if any(
            element.document_id != self.document.document_id
            for element in self.elements
        ):
            raise ValueError("all elements must belong to the parsed document")
        ordinals = [element.ordinal for element in self.elements]
        if ordinals != sorted(ordinals) or len(ordinals) != len(set(ordinals)):
            raise ValueError("element ordinals must be unique and ordered")
