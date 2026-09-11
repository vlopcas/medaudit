import unittest
from typing import ClassVar

from medaudit.documents import Chunk
from medaudit.retrieval import (
    ReciprocalRankFusion,
    SearchResult,
    WeightedRetriever,
)


class StubRetriever:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int, float]] = []

    def search(
        self, query: str, *, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:
        self.calls.append((query, top_k, min_score))
        return self.results[:top_k]


class ReciprocalRankFusionTest(unittest.TestCase):
    chunks: ClassVar[list[Chunk]] = [
        Chunk("chunk-a", "doc-a", "synthetic alpha"),
        Chunk("chunk-b", "doc-b", "synthetic beta"),
        Chunk("chunk-c", "doc-c", "synthetic gamma"),
    ]

    def test_fuses_rankings_without_comparing_raw_scores(self) -> None:
        lexical = StubRetriever(
            [
                SearchResult(self.chunks[0], 1000.0),
                SearchResult(self.chunks[1], 500.0),
            ]
        )
        semantic = StubRetriever(
            [
                SearchResult(self.chunks[1], 0.9),
                SearchResult(self.chunks[2], 0.8),
            ]
        )
        fusion = ReciprocalRankFusion(
            [WeightedRetriever(lexical), WeightedRetriever(semantic)],
            rank_constant=60,
        )

        results = fusion.search("synthetic query", top_k=3)

        self.assertEqual([result.chunk.chunk_id for result in results], [
            "chunk-b",
            "chunk-a",
            "chunk-c",
        ])
        self.assertEqual(lexical.calls, [("synthetic query", 20, 0.0)])
        self.assertEqual(semantic.calls, [("synthetic query", 20, 0.0)])

    def test_weights_retriever_contributions(self) -> None:
        first = StubRetriever([SearchResult(self.chunks[0], 1.0)])
        second = StubRetriever([SearchResult(self.chunks[1], 1.0)])
        fusion = ReciprocalRankFusion(
            [WeightedRetriever(first), WeightedRetriever(second, weight=2.0)]
        )

        results = fusion.search("synthetic query", top_k=2)

        self.assertEqual(results[0].chunk.chunk_id, "chunk-b")

    def test_rejects_conflicting_chunk_identity(self) -> None:
        first = StubRetriever([SearchResult(self.chunks[0], 1.0)])
        conflicting = Chunk("chunk-a", "different-doc", "different synthetic")
        second = StubRetriever([SearchResult(conflicting, 1.0)])
        fusion = ReciprocalRankFusion(
            [WeightedRetriever(first), WeightedRetriever(second)]
        )

        with self.assertRaisesRegex(ValueError, "chunk identity"):
            fusion.search("synthetic query")

    def test_requires_two_retrievers(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least two"):
            ReciprocalRankFusion([WeightedRetriever(StubRetriever([]))])
