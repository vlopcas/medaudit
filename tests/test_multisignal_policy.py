import unittest
from typing import Any

from medaudit.evaluation.multisignal_policy import (
    calibrate_multisignal_policy,
    cross_validate_multisignal_policy,
)


def case(answerable: bool, top: float, coverage: float) -> dict[str, Any]:
    return {
        "answerable": answerable,
        "signals": {
            "top_score": top,
            "normalized_margin": 0.0,
            "query_coverage": coverage,
            "rare_query_coverage": 0.0,
        },
    }


class MultisignalPolicyTest(unittest.TestCase):
    def test_conjunction_can_improve_abstention_at_coverage_floor(self) -> None:
        report = {
            "schema_version": 1,
            "partition": "calibration",
            "cases": [
                case(True, 10, 1.0),
                case(True, 9, 0.9),
                case(True, 8, 0.8),
                case(True, 7, 0.7),
                case(False, 9, 0.2),
                case(False, 2, 0.9),
            ],
        }

        result = calibrate_multisignal_policy(
            report, min_answerable_acceptance=0.75
        )

        self.assertEqual(len(result["policy"]["conditions"]), 2)
        self.assertEqual(
            result["calibration"]["selected_metrics"]["unanswerable_abstention"],
            1.0,
        )

    def test_rejects_non_calibration_report(self) -> None:
        with self.assertRaisesRegex(ValueError, "calibration partition"):
            calibrate_multisignal_policy(
                {"schema_version": 1, "partition": "evaluation", "cases": []},
                min_answerable_acceptance=0.8,
            )

    def test_cross_validation_covers_every_case_once(self) -> None:
        cases = [
            {
                **case(answerable, float(index + 1), float((index % 3) + 1)),
                "case_id": f"case-{answerable}-{index}",
            }
            for answerable in (True, False)
            for index in range(6)
        ]
        report = {
            "schema_version": 1,
            "partition": "calibration",
            "cases": cases,
        }

        result = cross_validate_multisignal_policy(
            report, min_answerable_acceptance=0.5, fold_count=3, seed="fixed"
        )

        self.assertEqual(result["case_count"], 12)
        self.assertEqual(
            sum(fold["validation_case_count"] for fold in result["folds"]), 12
        )
