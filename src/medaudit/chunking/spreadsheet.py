"""Chunk spreadsheet rows while preserving sheet and row provenance."""

import hashlib

from medaudit.documents import Chunk, DocumentElement
from medaudit.parsing import ParsedDocument

SPREADSHEET_PARSERS = frozenset({"openpyxl-rows-v1", "xlrd-rows-v1"})


class SpreadsheetChunker:
    """Group consecutive rows and repeat the sheet's first row as context."""

    def __init__(
        self, max_characters: int = 1_500, max_header_characters: int = 300
    ):
        if max_characters <= 0:
            raise ValueError("max_characters must be positive")
        if max_header_characters < 0:
            raise ValueError("max_header_characters cannot be negative")
        self._max_characters = max_characters
        self._max_header_characters = max_header_characters

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        sheets: dict[str, list[DocumentElement]] = {}
        for element in parsed.elements:
            sheet = element.metadata.get("sheet", element.section or "")
            sheets.setdefault(sheet, []).append(element)
        for rows in sheets.values():
            chunks.extend(self._chunk_sheet(parsed, rows))
        return chunks

    def _chunk_sheet(
        self, parsed: ParsedDocument, rows: list[DocumentElement]
    ) -> list[Chunk]:
        if not rows:
            return []
        if len(rows) == 1:
            return [self._build_chunk(parsed, None, rows)]
        candidate_header = rows[0]
        header = (
            candidate_header
            if len(candidate_header.text) <= self._max_header_characters
            else None
        )
        data_rows = rows[1:] if header is not None else rows
        chunks: list[Chunk] = []
        group: list[DocumentElement] = []
        for row in data_rows:
            proposed = self._render(header, [*group, row])
            if group and len(proposed) > self._max_characters:
                chunks.append(self._build_chunk(parsed, header, group))
                group = []
            group.append(row)
        if group:
            chunks.append(self._build_chunk(parsed, header, group))
        return chunks

    @staticmethod
    def _render(
        header: DocumentElement | None, rows: list[DocumentElement]
    ) -> str:
        values = [row.text for row in rows]
        if header is not None:
            values.insert(0, header.text)
        return "\n".join(values)

    def _build_chunk(
        self,
        parsed: ParsedDocument,
        header: DocumentElement | None,
        rows: list[DocumentElement],
    ) -> Chunk:
        included = ([header] if header is not None else []) + rows
        identity = "\0".join(
            [
                parsed.document.document_id,
                "spreadsheet-rows-v1",
                str(self._max_characters),
                *(element.element_id for element in included),
            ]
        )
        row_numbers = [int(element.metadata["row"]) for element in rows]
        first = included[0]
        metadata = {
            "element_ids": ",".join(element.element_id for element in included),
            "strategy": "spreadsheet-rows-v1",
            "document_version": parsed.document.version,
            "sheet": first.metadata.get("sheet", first.section or ""),
            "row_start": str(min(row_numbers)),
            "row_end": str(max(row_numbers)),
        }
        if header is not None:
            metadata["header_row"] = header.metadata["row"]
        return Chunk(
            chunk_id=f"ch-{hashlib.sha256(identity.encode()).hexdigest()[:16]}",
            document_id=parsed.document.document_id,
            text=self._render(header, rows),
            section=first.section,
            metadata=metadata,
        )


def is_spreadsheet(parsed: ParsedDocument) -> bool:
    """Return whether all parsed elements came from a spreadsheet row parser."""
    return bool(parsed.elements) and all(
        element.metadata.get("parser") in SPREADSHEET_PARSERS
        for element in parsed.elements
    )
