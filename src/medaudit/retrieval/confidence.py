"""Interpretable confidence signals for ranked lexical retrieval results."""

import math
from collections import Counter
from dataclasses import dataclass

from medaudit.documents import Chunk
from medaudit.retrieval.bm25 import SearchResult, tokenize


@dataclass(frozen=True, slots=True)
class ConfidenceSignals:
    """Query-result signals that do not depend on a learned model."""

    top_score: float
    normalized_margin: float
    query_coverage: float
    rare_query_coverage: float | None
    top_document_concentration: float
    result_count: int


class ConfidenceAnalyzer:
    """Compute confidence signals against a fixed retrieval corpus."""

    def __init__(self, chunks: list[Chunk], *, rare_document_ratio: float = 0.01):
        if not chunks:
            raise ValueError("at least one chunk is required")
        if not 0 < rare_document_ratio <= 1:
            raise ValueError("rare document ratio must be between zero and one")
        self._rare_limit = max(1, math.ceil(len(chunks) * rare_document_ratio))
        self._document_frequency = Counter(
            term for chunk in chunks for term in set(tokenize(chunk.text))
        )

    def analyze(
        self, query: str, results: list[SearchResult]
    ) -> ConfidenceSignals:
        """Measure the relationship between a query and its ranked results."""
        if not results:
            return ConfidenceSignals(0.0, 0.0, 0.0, None, 0.0, 0)
        query_terms = set(tokenize(query))
        top_terms = set(tokenize(results[0].chunk.text))
        coverage = (
            len(query_terms.intersection(top_terms)) / len(query_terms)
            if query_terms
            else 0.0
        )
        rare_terms = {
            term
            for term in query_terms
            if 0 < self._document_frequency[term] <= self._rare_limit
        }
        rare_coverage = (
            len(rare_terms.intersection(top_terms)) / len(rare_terms)
            if rare_terms
            else None
        )
        top_score = results[0].score
        second_score = results[1].score if len(results) > 1 else 0.0
        margin = (top_score - second_score) / top_score if top_score else 0.0
        documents = Counter(result.chunk.document_id for result in results)
        concentration = max(documents.values()) / len(results)
        return ConfidenceSignals(
            top_score=top_score,
            normalized_margin=margin,
            query_coverage=coverage,
            rare_query_coverage=rare_coverage,
            top_document_concentration=concentration,
            result_count=len(results),
        )
