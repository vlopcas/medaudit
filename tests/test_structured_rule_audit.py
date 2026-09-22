import unittest
from pathlib import Path

from medaudit.evaluation.structured_rule_audit import evaluate, load_dataset


class StructuredRuleAuditTest(unittest.TestCase):
    def test_development_dataset_finds_only_expected_overlaps(self) -> None:
        rule_set, expected = load_dataset(
            Path("data/synthetic_cases/structured_rule_audit_development.json")
        )

        report = evaluate(rule_set, expected)

        self.assertTrue(report["metrics"]["exact_match"])
        self.assertEqual(report["finding_count"], 3)
        self.assertEqual(
            report["metrics"]["finding_count_by_code"],
            {"conflicting_overlap": 2, "redundant_overlap": 1},
        )


if __name__ == "__main__":
    unittest.main()
