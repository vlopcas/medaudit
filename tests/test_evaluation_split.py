import tempfile
import unittest
from pathlib import Path
from typing import Any

from medaudit.evaluation.split import split_reviewed_cases, validate_split, write_split


def reviewed_cases() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "review_status": "reviewed",
        "cases": [
            {
                "candidate_id": f"case-{number}",
                "answerability": (
                    "answerable" if number < 6 else "insufficient_evidence"
                ),
                "review_status": "approved",
            }
            for number in range(10)
        ],
    }


class EvaluationSplitTest(unittest.TestCase):
    def test_split_is_deterministic_disjoint_and_stratified(self) -> None:
        review = reviewed_cases()

        first = split_reviewed_cases(review, calibration_fraction=0.7, seed="fixed")
        second = split_reviewed_cases(review, calibration_fraction=0.7, seed="fixed")

        self.assertEqual(first, second)
        calibration = set(first["partitions"]["calibration"])
        evaluation = set(first["partitions"]["evaluation"])
        self.assertFalse(calibration & evaluation)
        self.assertEqual(calibration | evaluation, {f"case-{n}" for n in range(10)})
        answerable = {f"case-{n}" for n in range(6)}
        insufficient = {f"case-{n}" for n in range(6, 10)}
        self.assertTrue(answerable & calibration)
        self.assertTrue(answerable & evaluation)
        self.assertTrue(insufficient & calibration)
        self.assertTrue(insufficient & evaluation)

    def test_detects_source_drift(self) -> None:
        review = reviewed_cases()
        manifest = split_reviewed_cases(
            review, calibration_fraction=0.7, seed="fixed"
        )
        review["cases"].append(
            {
                "candidate_id": "new-case",
                "answerability": "insufficient_evidence",
                "review_status": "approved",
            }
        )

        with self.assertRaisesRegex(ValueError, "do not match"):
            validate_split(manifest, review)

    def test_rejects_overlapping_partitions(self) -> None:
        review = reviewed_cases()
        manifest = split_reviewed_cases(
            review, calibration_fraction=0.7, seed="fixed"
        )
        manifest["partitions"]["evaluation"].append(
            manifest["partitions"]["calibration"][0]
        )

        with self.assertRaisesRegex(ValueError, "overlap"):
            validate_split(manifest, review)

    def test_output_requires_private_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "must end with .local.json"):
                write_split({}, Path(directory) / "split.json")
