import unittest

from medaudit.evaluation.temporal_baseline import consolidate_metrics


class TemporalBaselineTest(unittest.TestCase):
    def test_consolidates_metrics_weighted_by_case_counts(self) -> None:
        snapshots = [
            self.snapshot(3, 1, 1.0, 0.5, 0.75, 1.0),
            self.snapshot(1, 1, 0.0, 1.0, 0.25, 0.0),
        ]

        result = consolidate_metrics(snapshots, top_k=5)

        self.assertEqual(result["case_count"], 6)
        self.assertEqual(result["metrics"]["hit_rate@5"], 0.75)
        self.assertEqual(result["metrics"]["recall@5"], 0.625)
        self.assertEqual(result["metrics"]["mrr"], 0.625)
        self.assertEqual(result["metrics"]["abstention_accuracy"], 0.5)

    def test_returns_none_when_metric_has_no_applicable_cases(self) -> None:
        snapshots = [self.snapshot(1, 0, 1.0, 1.0, 1.0, None)]

        result = consolidate_metrics(snapshots, top_k=5)

        self.assertIsNone(result["metrics"]["abstention_accuracy"])

    @staticmethod
    def snapshot(
        answerable: int,
        unanswerable: int,
        hit_rate: float,
        recall: float,
        mrr: float,
        abstention: float | None,
    ) -> dict[str, object]:
        return {
            "evaluation": {
                "answerable_case_count": answerable,
                "unanswerable_case_count": unanswerable,
                "metrics": {
                    "hit_rate@5": hit_rate,
                    "recall@5": recall,
                    "mrr": mrr,
                    "abstention_accuracy": abstention,
                },
            }
        }
