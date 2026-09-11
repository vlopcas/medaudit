import unittest

from medaudit.evaluation.hybrid_diagnostics import diagnose_hybrid


def outcome(case_id: str, reciprocal_rank: float, recall: float) -> dict[str, object]:
    return {
        "case_id": case_id,
        "answerable": True,
        "hit": reciprocal_rank > 0,
        "reciprocal_rank": reciprocal_rank,
        "recall": recall,
    }


class HybridDiagnosticsTest(unittest.TestCase):
    def test_counts_ranking_wins_ties_and_losses_by_dimension(self) -> None:
        benchmark = {
            "schema_version": 1,
            "partition": "calibration",
            "retrievers": {
                "bm25": {"cases": [outcome("a", 1.0, 1.0), outcome("b", 0.0, 0.0)]},
                "dense": {"cases": [outcome("a", 0.5, 1.0), outcome("b", 1.0, 1.0)]},
                "hybrid_rrf": {
                    "cases": [outcome("a", 1.0, 1.0), outcome("b", 0.0, 0.0)]
                },
            },
        }
        review = {
            "cases": [
                {
                    "candidate_id": case_id,
                    "category": "single_document",
                    "difficulty": "medium",
                    "reasoning_type": "lookup",
                }
                for case_id in ("a", "b")
            ]
        }

        report = diagnose_hybrid(benchmark, review)

        dense = report["comparisons"]["dense"]["overall"]
        self.assertEqual(dense["mrr_win_count"], 1)
        self.assertEqual(dense["mrr_loss_count"], 1)
        hybrid = report["comparisons"]["hybrid_rrf"]["overall"]
        self.assertEqual(hybrid["mrr_tie_count"], 2)

    def test_rejects_non_calibration_benchmark(self) -> None:
        with self.assertRaisesRegex(ValueError, "calibration"):
            diagnose_hybrid(
                {"schema_version": 1, "partition": "evaluation"}, {"cases": []}
            )
