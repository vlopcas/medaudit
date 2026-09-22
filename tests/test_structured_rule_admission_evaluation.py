import unittest
from pathlib import Path

from medaudit.evaluation.structured_rule_admission import evaluate, load_dataset


class StructuredRuleAdmissionEvaluationTest(unittest.TestCase):
    def test_development_dataset_matches_all_expected_outcomes(self) -> None:
        cases = load_dataset(
            Path(
                "data/synthetic_cases/structured_rule_admission_development.json"
            )
        )

        report = evaluate(cases)

        self.assertTrue(report["metrics"]["exact_match"])
        self.assertEqual(report["metrics"]["passed"], 5)
        self.assertEqual(report["metrics"]["total"], 5)

    def test_loader_rejects_unexpected_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            load_dataset(
                Path(
                    "data/synthetic_cases/structured_rule_admission_development.json"
                ),
                expected_policy="structured-rule-admission-holdout-v1",
            )


if __name__ == "__main__":
    unittest.main()
