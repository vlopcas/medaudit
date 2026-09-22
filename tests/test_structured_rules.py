import unittest
from datetime import date
from pathlib import Path

from medaudit.evaluation.structured_rules import evaluate, load_dataset
from medaudit.rules import (
    RuleDecision,
    RuleQuery,
    RuleResolution,
    RuleResolutionCode,
    RuleResolutionStatus,
    RuleSet,
    StructuredRule,
)


class StructuredRulesTest(unittest.TestCase):
    def test_development_dataset_matches_expected_resolutions(self) -> None:
        rule_set, cases = load_dataset(
            Path("data/synthetic_cases/structured_rules_development.json")
        )

        report = evaluate(rule_set, cases)

        self.assertEqual(report["case_count"], 8)
        self.assertEqual(report["metrics"]["exact_match"], 1.0)

    def test_rule_set_rejects_duplicate_version_identity(self) -> None:
        rule = StructuredRule(
            rule_id="synthetic",
            version=1,
            subject="subject",
            action="action",
            decision=RuleDecision.ALLOW,
            effective_from=date(2026, 1, 1),
            effective_until=None,
            priority=1,
            conditions=(),
            source_document_id="source",
        )

        with self.assertRaises(ValueError):
            RuleSet(schema_version=1, rules=(rule, rule))

    def test_query_rejects_duplicate_attribute_keys(self) -> None:
        with self.assertRaises(ValueError):
            RuleQuery(
                subject="subject",
                action="action",
                reference_date=date(2026, 1, 1),
                attributes=(("channel", "blue"), ("channel", "red")),
            )

    def test_resolution_rejects_inconsistent_status_and_code(self) -> None:
        with self.assertRaises(ValueError):
            RuleResolution(
                status=RuleResolutionStatus.APPLIED,
                code=RuleResolutionCode.NO_APPLICABLE_RULE,
                decision=RuleDecision.ALLOW,
                matched_rule_versions=("synthetic@1",),
            )


if __name__ == "__main__":
    unittest.main()
