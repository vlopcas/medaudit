"""Provider-neutral retrieval contract."""

from typing import Protocol

from medaudit.retrieval.bm25 import SearchResult


class Retriever(Protocol):
    """Rank chunks for a text query."""

    def search(
        self, query: str, *, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]: ...
