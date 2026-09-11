import unittest
from typing import Any, ClassVar

from medaudit.evaluation.confidence_analysis import _distribution, _pairwise_rate


class ConfidenceAnalysisTest(unittest.TestCase):
    answerable: ClassVar[list[dict[str, Any]]] = [
        {"signals": {"query_coverage": 0.8}},
        {"signals": {"query_coverage": 1.0}},
    ]
    unanswerable: ClassVar[list[dict[str, Any]]] = [
        {"signals": {"query_coverage": 0.4}}
    ]

    def test_summarizes_signal_distribution(self) -> None:
        result = _distribution(self.answerable, "query_coverage")

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["median"], 0.9)

    def test_computes_pairwise_separation_rate(self) -> None:
        rate = _pairwise_rate(
            self.answerable, self.unanswerable, "query_coverage"
        )

        self.assertEqual(rate, 1.0)
