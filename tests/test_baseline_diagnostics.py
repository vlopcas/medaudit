import json
import unittest
from typing import Any

from medaudit.evaluation.diagnostics import diagnose_baseline


class BaselineDiagnosticsTest(unittest.TestCase):
    def test_counts_failures_and_keeps_questions_out(self) -> None:
        baseline = {
            "snapshots": [
                {
                    "evaluation": {
                        "cases": [
                            {"case_id": "hit", "reciprocal_rank": 0.5, "recall": 1.0},
                            {"case_id": "miss", "reciprocal_rank": 0.0, "recall": 0.0},
                            {"case_id": "abs", "correct_abstention": False},
                        ]
                    }
                }
            ]
        }
        review = {
            "cases": [
                self.review_case("hit", "answerable", "easy"),
                self.review_case("miss", "answerable", "hard"),
                self.review_case("abs", "candidate_unanswerable", "hard"),
            ]
        }

        report = diagnose_baseline(baseline, review)

        self.assertEqual(report["zero_hit_count"], 1)
        self.assertEqual(report["partial_recall_count"], 1)
        self.assertEqual(report["incorrect_abstention_count"], 1)
        self.assertEqual(report["groups"]["difficulty"]["hard"]["case_count"], 2)
        self.assertNotIn("Synthetic private question", json.dumps(report))

    def test_rejects_mismatched_case_sets(self) -> None:
        baseline: dict[str, Any] = {
            "snapshots": [{"evaluation": {"cases": []}}]
        }
        review: dict[str, Any] = {
            "cases": [self.review_case("extra", "answerable", "easy")]
        }

        with self.assertRaisesRegex(ValueError, "do not match"):
            diagnose_baseline(baseline, review)

    @staticmethod
    def review_case(
        case_id: str, answerability: str, difficulty: str
    ) -> dict[str, str]:
        return {
            "candidate_id": case_id,
            "question": "Synthetic private question",
            "answerability": answerability,
            "category": "synthetic_category",
            "difficulty": difficulty,
            "reasoning_type": "single_document",
        }
