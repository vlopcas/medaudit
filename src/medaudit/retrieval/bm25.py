"""Small, dependency-free BM25 baseline for learning and evaluation."""

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from medaudit.documents import Chunk

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    """Normalize accents and tokenize words, codes, dates and numbers."""
    normalized = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return TOKEN_PATTERN.findall(ascii_text)


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A scored chunk returned by a retriever."""

    chunk: Chunk
    score: float


class BM25Index:
    """Okapi BM25 index suitable as a transparent lexical baseline."""

    def __init__(self, chunks: list[Chunk], *, k1: float = 1.5, b: float = 0.75):
        if not chunks:
            raise ValueError("at least one chunk is required")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("k1 must be positive and b must be between 0 and 1")

        self._chunks = chunks
        self._k1 = k1
        self._b = b
        self._term_frequencies = [
            Counter(tokenize(chunk.text)) for chunk in chunks
        ]
        self._lengths = [
            sum(frequencies.values()) for frequencies in self._term_frequencies
        ]
        self._average_length = sum(self._lengths) / len(self._lengths)
        self._document_frequency = Counter(
            term for frequencies in self._term_frequencies for term in frequencies
        )

    def search(
        self, query: str, *, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:
        """Return the highest-scoring chunks with deterministic tie-breaking."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if min_score < 0:
            raise ValueError("min_score cannot be negative")

        query_terms = set(tokenize(query))
        results: list[SearchResult] = []
        for chunk, frequencies, length in zip(
            self._chunks, self._term_frequencies, self._lengths, strict=True
        ):
            score = sum(
                self._score_term(term, frequencies[term], length)
                for term in query_terms
                if frequencies[term]
            )
            if score > 0 and score >= min_score:
                results.append(SearchResult(chunk=chunk, score=score))

        results.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
        return results[:top_k]

    def _score_term(self, term: str, frequency: int, length: int) -> float:
        document_count = len(self._chunks)
        document_frequency = self._document_frequency[term]
        inverse_document_frequency = math.log(
            1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
        )
        length_ratio = length / self._average_length if self._average_length else 0
        denominator = frequency + self._k1 * (1 - self._b + self._b * length_ratio)
        return inverse_document_frequency * (frequency * (self._k1 + 1) / denominator)
