import unittest

from medaudit.evaluation.structural_decomposition import evaluate


class StructuralDecompositionEvaluationTest(unittest.TestCase):
    def test_reports_confusion_matrix_and_rates(self) -> None:
        report = evaluate(
            [
                {
                    "id": "positive",
                    "query": "Use o manual A e o manual B.",
                    "requires_decomposition": True,
                },
                {
                    "id": "negative",
                    "query": "Liste os manuais.",
                    "requires_decomposition": False,
                },
            ]
        )

        self.assertEqual(report["metrics"]["accuracy"], 1.0)
        self.assertEqual(report["metrics"]["false_positive_rate"], 0.0)
        self.assertEqual(report["confusion"]["true_positive"], 1)
