"""In-memory cosine retrieval over normalized local embeddings."""

from typing import Protocol

import numpy as np

from medaudit.documents import Chunk
from medaudit.retrieval.bm25 import SearchResult
from medaudit.retrieval.embeddings import FloatMatrix


class Embedder(Protocol):
    """Encode passages and queries into compatible normalized matrices."""

    def encode_passages(self, texts: list[str], *, batch_size: int) -> FloatMatrix: ...

    def encode_query(self, text: str) -> FloatMatrix: ...


class DenseIndex:
    """Rank chunks by cosine similarity using a local embedding provider."""

    def __init__(
        self,
        chunks: list[Chunk],
        embedder: Embedder,
        *,
        batch_size: int = 32,
    ) -> None:
        if not chunks:
            raise ValueError("at least one chunk is required")
        if batch_size <= 0:
            raise ValueError("embedding batch size must be positive")
        matrix = embedder.encode_passages(
            [chunk.text for chunk in chunks], batch_size=batch_size
        )
        self._validate_matrix(matrix, len(chunks))
        self._chunks = chunks
        self._embedder = embedder
        self._matrix = matrix

    def search(
        self, query: str, *, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:
        """Return highest cosine similarities with deterministic tie-breaking."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if not -1 <= min_score <= 1:
            raise ValueError("dense minimum score must be between minus one and one")
        query_matrix = self._embedder.encode_query(query)
        self._validate_matrix(query_matrix, 1)
        if query_matrix.shape[1] != self._matrix.shape[1]:
            raise ValueError("query and passage embedding dimensions do not match")
        scores = self._matrix @ query_matrix[0]
        results = [
            SearchResult(chunk=chunk, score=float(score))
            for chunk, score in zip(self._chunks, scores, strict=True)
            if score >= min_score
        ]
        results.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
        return results[:top_k]

    @staticmethod
    def _validate_matrix(matrix: FloatMatrix, expected_rows: int) -> None:
        if matrix.ndim != 2 or matrix.shape[0] != expected_rows or not matrix.shape[1]:
            raise ValueError("embedding matrix has an unexpected shape")
        if matrix.dtype != np.float32:
            raise ValueError("embedding matrix must use float32")
        if not np.isfinite(matrix).all():
            raise ValueError("embedding matrix contains non-finite values")
