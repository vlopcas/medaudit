"""Candidate-constrained semantic reranking over a lexical retriever."""

from collections import defaultdict

import numpy as np

from medaudit.documents import Chunk
from medaudit.retrieval.bm25 import SearchResult
from medaudit.retrieval.dense import Embedder
from medaudit.retrieval.embeddings import FloatMatrix
from medaudit.retrieval.protocol import Retriever


class SemanticCandidateReranker:
    """Fuse lexical and semantic ranks only within base-retriever candidates."""

    def __init__(
        self,
        base: Retriever,
        chunks: list[Chunk],
        passage_embeddings: FloatMatrix,
        embedder: Embedder,
        *,
        candidate_depth: int = 20,
        rank_constant: int = 60,
        lexical_weight: float = 1.0,
        semantic_weight: float = 1.0,
    ) -> None:
        if candidate_depth <= 0:
            raise ValueError("candidate depth must be positive")
        if rank_constant < 0:
            raise ValueError("rank constant cannot be negative")
        if lexical_weight <= 0 or semantic_weight <= 0:
            raise ValueError("reranking weights must be positive")
        if (
            passage_embeddings.ndim != 2
            or passage_embeddings.shape[0] != len(chunks)
            or passage_embeddings.dtype != np.float32
            or not np.isfinite(passage_embeddings).all()
        ):
            raise ValueError("passage embeddings are invalid")
        identifiers = [chunk.chunk_id for chunk in chunks]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("duplicate chunk ids")
        self._base = base
        self._vectors = {
            chunk.chunk_id: vector
            for chunk, vector in zip(chunks, passage_embeddings, strict=True)
        }
        self._embedder = embedder
        self._candidate_depth = candidate_depth
        self._rank_constant = rank_constant
        self._lexical_weight = lexical_weight
        self._semantic_weight = semantic_weight

    def search(
        self, query: str, *, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:
        """Rerank lexical candidates using rank-based semantic evidence."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if min_score < 0:
            raise ValueError("min_score cannot be negative")
        candidates = self._base.search(
            query, top_k=max(top_k, self._candidate_depth), min_score=0.0
        )
        if not candidates:
            return []
        query_vector = self._embedder.encode_query(query)
        if query_vector.ndim != 2 or query_vector.shape[0] != 1:
            raise ValueError("query embedding has an unexpected shape")
        semantic = sorted(
            candidates,
            key=lambda result: (
                -float(self._vectors[result.chunk.chunk_id] @ query_vector[0]),
                result.chunk.chunk_id,
            ),
        )
        scores: defaultdict[str, float] = defaultdict(float)
        chunks_by_id = {result.chunk.chunk_id: result.chunk for result in candidates}
        for rank, result in enumerate(candidates, start=1):
            scores[result.chunk.chunk_id] += self._lexical_weight / (
                self._rank_constant + rank
            )
        for rank, result in enumerate(semantic, start=1):
            scores[result.chunk.chunk_id] += self._semantic_weight / (
                self._rank_constant + rank
            )
        reranked = [
            SearchResult(chunks_by_id[chunk_id], score)
            for chunk_id, score in scores.items()
            if score >= min_score
        ]
        reranked.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
        return reranked[:top_k]
