import unittest
from typing import Any

from medaudit.evaluation.confidence_policy import calibrate_top_score_policy


def report(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": 1, "partition": "calibration", "cases": cases}


def case(*, answerable: bool, score: float) -> dict[str, Any]:
    return {"answerable": answerable, "signals": {"top_score": score}}


class ConfidencePolicyTest(unittest.TestCase):
    def test_maximizes_abstention_under_answerable_acceptance_floor(self) -> None:
        calibration = report(
            [
                case(answerable=True, score=10),
                case(answerable=True, score=9),
                case(answerable=True, score=8),
                case(answerable=True, score=2),
                case(answerable=False, score=7),
                case(answerable=False, score=1),
            ]
        )

        result = calibrate_top_score_policy(
            calibration, min_answerable_acceptance=0.75
        )

        self.assertEqual(result["policy"]["threshold"], 8)
        self.assertEqual(
            result["calibration"]["selected_metrics"]["answerable_acceptance"],
            0.75,
        )
        self.assertEqual(
            result["calibration"]["selected_metrics"]["unanswerable_abstention"],
            1.0,
        )

    def test_rejects_non_calibration_report(self) -> None:
        payload = report(
            [case(answerable=True, score=1), case(answerable=False, score=0)]
        )
        payload["partition"] = "evaluation"

        with self.assertRaisesRegex(ValueError, "calibration partition"):
            calibrate_top_score_policy(payload, min_answerable_acceptance=0.8)

    def test_requires_both_answerability_classes(self) -> None:
        with self.assertRaisesRegex(ValueError, "both answerability classes"):
            calibrate_top_score_policy(
                report([case(answerable=True, score=1)]),
                min_answerable_acceptance=0.8,
            )
