"""Route parsed documents to a format-appropriate chunking strategy."""

from medaudit.chunking.spreadsheet import SpreadsheetChunker, is_spreadsheet
from medaudit.chunking.structural import StructureAwareChunker
from medaudit.documents import Chunk
from medaudit.parsing import ParsedDocument


class FormatAwareChunker:
    """Keep structural documents and spreadsheet rows on separate policies."""

    def __init__(self, max_characters: int = 1_500):
        self._structural = StructureAwareChunker(max_characters=max_characters)
        self._spreadsheet = SpreadsheetChunker(max_characters=max_characters)

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        if is_spreadsheet(parsed):
            return self._spreadsheet.chunk(parsed)
        return self._structural.chunk(parsed)
