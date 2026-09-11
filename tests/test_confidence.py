import unittest

from medaudit.documents import Chunk
from medaudit.retrieval import BM25Index, ConfidenceAnalyzer


class ConfidenceAnalyzerTest(unittest.TestCase):
    def test_computes_interpretable_signals(self) -> None:
        chunks = [
            Chunk("c1", "d1", "rarecode authorization synthetic"),
            Chunk("c2", "d2", "billing synthetic"),
            Chunk("c3", "d1", "other synthetic rule"),
        ]
        results = BM25Index(chunks).search("rarecode authorization", top_k=3)

        signals = ConfidenceAnalyzer(chunks).analyze(
            "rarecode authorization", results
        )

        self.assertEqual(signals.query_coverage, 1.0)
        self.assertEqual(signals.rare_query_coverage, 1.0)
        self.assertGreater(signals.normalized_margin, 0)
        self.assertEqual(signals.top_document_concentration, 1.0)

    def test_returns_zero_signals_without_results(self) -> None:
        chunks = [Chunk("c1", "d1", "synthetic")]

        signals = ConfidenceAnalyzer(chunks).analyze("missing", [])

        self.assertEqual(signals.result_count, 0)
        self.assertEqual(signals.top_score, 0.0)
        self.assertIsNone(signals.rare_query_coverage)

    def test_rejects_invalid_rare_ratio(self) -> None:
        with self.assertRaisesRegex(ValueError, "rare document ratio"):
            ConfidenceAnalyzer([Chunk("c1", "d1", "synthetic")], rare_document_ratio=0)
