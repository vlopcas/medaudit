import unittest

from medaudit.evaluation.evidence_aggregation import evaluate


class EvidenceAggregationEvaluationTest(unittest.TestCase):
    def test_rejects_empty_case_collection(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            evaluate([])
