import unittest

from medaudit.documents import Chunk
from medaudit.evaluation.hybrid_benchmark import (
    evaluate_rankings,
    summarize_outcomes,
)
from medaudit.evaluation.private_bm25 import PrivateEvaluationCase
from medaudit.retrieval.bm25 import SearchResult


class StaticRetriever:
    def __init__(self, results: list[SearchResult]) -> None:
        self._results = results

    def search(
        self, query: str, *, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:
        return self._results[:top_k]


class HybridBenchmarkTest(unittest.TestCase):
    def test_summarizes_answerable_and_unanswerable_cases(self) -> None:
        chunks = [
            Chunk("wrong", "doc-wrong", "synthetic"),
            Chunk("right", "doc-right", "synthetic"),
        ]
        retriever = StaticRetriever(
            [SearchResult(chunks[0], 2.0), SearchResult(chunks[1], 1.0)]
        )
        cases = [
            PrivateEvaluationCase(
                "answerable",
                "synthetic query",
                "single_document",
                relevant_chunk_ids=frozenset({"right"}),
            ),
            PrivateEvaluationCase(
                "unanswerable", "synthetic query", "insufficient_evidence"
            ),
        ]

        outcomes = evaluate_rankings(cases, retriever, top_k=2)
        summary = summarize_outcomes(outcomes, top_k=2)

        self.assertEqual(summary["metrics"]["hit_rate@2"], 1.0)
        self.assertEqual(summary["metrics"]["recall@2"], 1.0)
        self.assertEqual(summary["metrics"]["mrr"], 0.5)
        self.assertEqual(summary["metrics"]["unanswerable_nonempty_rate"], 1.0)
        self.assertNotIn("synthetic query", str(summary))
