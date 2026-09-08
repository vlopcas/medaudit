"""Orchestrate deterministic parsing and chunking."""

from collections.abc import Iterable
from dataclasses import dataclass

from medaudit.chunking import Chunker
from medaudit.documents import Chunk, Document
from medaudit.parsing import DocumentParser, ParsedDocument


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Complete normalized result of one document ingestion."""

    schema_version: int
    parsed_document: ParsedDocument
    chunks: tuple[Chunk, ...]


class ParserRegistry:
    """Resolve one explicitly registered parser for each media type."""

    def __init__(self, parsers: Iterable[DocumentParser]):
        self._by_media_type: dict[str, DocumentParser] = {}
        for parser in parsers:
            for media_type in parser.supported_media_types:
                normalized = self._normalize(media_type)
                if normalized in self._by_media_type:
                    raise ValueError(f"duplicate parser for media type: {normalized}")
                self._by_media_type[normalized] = parser

    def get(self, media_type: str) -> DocumentParser:
        """Return the parser or fail closed for unsupported content."""
        normalized = self._normalize(media_type)
        try:
            return self._by_media_type[normalized]
        except KeyError as error:
            raise ValueError(f"unsupported media type: {normalized}") from error

    @staticmethod
    def _normalize(media_type: str) -> str:
        normalized = media_type.partition(";")[0].strip().casefold()
        if not normalized:
            raise ValueError("media type cannot be blank")
        return normalized


class IngestionPipeline:
    """Run parsing and chunking without storage or network side effects."""

    SCHEMA_VERSION = 1

    def __init__(self, registry: ParserRegistry, chunker: Chunker):
        self._registry = registry
        self._chunker = chunker

    def ingest(
        self, document: Document, content: bytes, media_type: str
    ) -> IngestionResult:
        """Normalize and chunk a document using its declared media type."""
        parser = self._registry.get(media_type)
        parsed = parser.parse(document, content)
        chunks = tuple(self._chunker.chunk(parsed))
        return IngestionResult(
            schema_version=self.SCHEMA_VERSION,
            parsed_document=parsed,
            chunks=chunks,
        )
