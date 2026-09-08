"""A deterministic chunker that respects page and section boundaries."""

import hashlib

from medaudit.documents import Chunk, DocumentElement, ElementKind
from medaudit.parsing import ParsedDocument


class StructureAwareChunker:
    """Group adjacent elements without crossing their structural boundaries."""

    def __init__(self, max_characters: int = 1_500):
        if max_characters <= 0:
            raise ValueError("max_characters must be positive")
        self._max_characters = max_characters

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        group: list[DocumentElement] = []
        for element in parsed.elements:
            if group and self._must_flush(group, element):
                chunks.append(self._build_chunk(parsed, group))
                group = []
            group.append(element)
        if group:
            chunks.append(self._build_chunk(parsed, group))
        return chunks

    def _must_flush(
        self, group: list[DocumentElement], candidate: DocumentElement
    ) -> bool:
        first = group[0]
        proposed_length = sum(len(element.text) for element in group) + len(group)
        proposed_length += len(candidate.text)
        changes_boundary = (candidate.page, candidate.section) != (
            first.page,
            first.section,
        )
        atomic_kinds = {
            ElementKind.TABLE,
            ElementKind.FIGURE,
        }
        preserves_atomic_element = (
            candidate.kind in atomic_kinds or first.kind in atomic_kinds
        )
        return (
            changes_boundary
            or proposed_length > self._max_characters
            or preserves_atomic_element
        )

    def _build_chunk(
        self, parsed: ParsedDocument, elements: list[DocumentElement]
    ) -> Chunk:
        text = "\n\n".join(element.text for element in elements)
        identity = "\0".join(
            [
                parsed.document.document_id,
                str(self._max_characters),
                *(element.element_id for element in elements),
            ]
        )
        chunk_id = f"ch-{hashlib.sha256(identity.encode()).hexdigest()[:16]}"
        return Chunk(
            chunk_id=chunk_id,
            document_id=parsed.document.document_id,
            text=text,
            page=elements[0].page,
            section=elements[0].section,
            metadata={
                "element_ids": ",".join(element.element_id for element in elements),
                "strategy": "structure-aware-v1",
                "document_version": parsed.document.version,
            },
        )
