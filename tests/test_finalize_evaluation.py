import tempfile
import unittest
from datetime import date
from pathlib import Path

from medaudit.evaluation.finalize import finalize_review, write_golden_sets


class FinalizeEvaluationTest(unittest.TestCase):
    def test_groups_approved_cases_and_defaults_missing_date(self) -> None:
        review = {
            "schema_version": 1,
            "review_status": "reviewed",
            "cases": [
                self.case("dated", "2026-01-01"),
                self.case("defaulted", None),
            ],
        }

        golden = finalize_review(review, date(2026, 9, 8))

        self.assertEqual(set(golden), {date(2026, 1, 1), date(2026, 9, 8)})
        self.assertEqual(golden[date(2026, 9, 8)]["relevance_level"], "document")

    def test_rejects_pending_case(self) -> None:
        pending = self.case("pending", None)
        pending["review_status"] = "pending"
        review = {
            "schema_version": 1,
            "review_status": "reviewed",
            "cases": [pending],
        }

        with self.assertRaisesRegex(ValueError, "must be approved"):
            finalize_review(review, date(2026, 9, 8))

    def test_rejects_answerable_case_without_relevance(self) -> None:
        invalid = self.case("invalid", None)
        invalid["proposed_relevant_document_ids"] = []
        review = {
            "schema_version": 1,
            "review_status": "reviewed",
            "cases": [invalid],
        }

        with self.assertRaisesRegex(ValueError, "no relevant documents"):
            finalize_review(review, date(2026, 9, 8))

    def test_does_not_overwrite_existing_snapshot(self) -> None:
        golden = {
            date(2026, 9, 8): {
                "schema_version": 1,
                "reference_date": "2026-09-08",
                "cases": [],
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_golden_sets(golden, output)

            with self.assertRaisesRegex(FileExistsError, "already exists"):
                write_golden_sets(golden, output)

    @staticmethod
    def case(case_id: str, reference_date: str | None) -> dict[str, object]:
        return {
            "candidate_id": case_id,
            "question": "Synthetic question?",
            "category": "exact_lookup",
            "answerability": "answerable",
            "reference_date": reference_date,
            "proposed_relevant_document_ids": ["doc-1"],
            "review_status": "approved",
        }
