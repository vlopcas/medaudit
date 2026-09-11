"""Deterministic rank fusion for heterogeneous retrievers."""

from collections import defaultdict
from dataclasses import dataclass

from medaudit.documents import Chunk
from medaudit.retrieval.bm25 import SearchResult
from medaudit.retrieval.protocol import Retriever


@dataclass(frozen=True, slots=True)
class WeightedRetriever:
    """A retriever and its contribution to rank fusion."""

    retriever: Retriever
    weight: float = 1.0

    def __post_init__(self) -> None:
        if self.weight <= 0:
            raise ValueError("retriever weight must be positive")


class ReciprocalRankFusion:
    """Fuse rankings without assuming comparable raw score scales."""

    def __init__(
        self,
        retrievers: list[WeightedRetriever],
        *,
        rank_constant: int = 60,
        candidate_depth: int = 20,
    ) -> None:
        if len(retrievers) < 2:
            raise ValueError("rank fusion requires at least two retrievers")
        if rank_constant < 0:
            raise ValueError("rank constant cannot be negative")
        if candidate_depth <= 0:
            raise ValueError("candidate depth must be positive")
        self._retrievers = retrievers
        self._rank_constant = rank_constant
        self._candidate_depth = candidate_depth

    def search(
        self, query: str, *, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:
        """Return fused chunks with deterministic tie-breaking."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if min_score < 0:
            raise ValueError("min_score cannot be negative")
        scores: defaultdict[str, float] = defaultdict(float)
        chunks: dict[str, Chunk] = {}
        for weighted in self._retrievers:
            results = weighted.retriever.search(
                query, top_k=max(top_k, self._candidate_depth), min_score=0.0
            )
            for rank, result in enumerate(results, start=1):
                chunk_id = result.chunk.chunk_id
                known = chunks.get(chunk_id)
                if known is not None and known != result.chunk:
                    raise ValueError("retrievers disagree about chunk identity")
                chunks[chunk_id] = result.chunk
                scores[chunk_id] += weighted.weight / (self._rank_constant + rank)
        fused = [
            SearchResult(chunk=chunks[chunk_id], score=score)
            for chunk_id, score in scores.items()
            if score >= min_score
        ]
        fused.sort(key=lambda result: (-result.score, result.chunk.chunk_id))
        return fused[:top_k]
