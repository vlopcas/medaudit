import unittest
from datetime import date

from medaudit.rules import (
    RuleAdmissionCode,
    RuleAdmissionStatus,
    RuleDecision,
    RuleSet,
    StructuredRule,
    admit_rule_set,
)


def make_rule(
    rule_id: str,
    decision: RuleDecision,
    *,
    region: str | None = None,
) -> StructuredRule:
    conditions: tuple[tuple[str, str], ...] = (("plan", "gold"),)
    if region is not None:
        conditions += (("region", region),)
    return StructuredRule(
        rule_id=rule_id,
        version=1,
        subject="claim",
        action="pay",
        decision=decision,
        effective_from=date(2026, 1, 1),
        effective_until=None,
        priority=5,
        conditions=conditions,
        source_document_id=f"source-{rule_id}",
    )


class StructuredRuleAdmissionTest(unittest.TestCase):
    def test_clean_catalog_is_admitted(self) -> None:
        result = admit_rule_set(
            RuleSet(schema_version=1, rules=(make_rule("base", RuleDecision.ALLOW),))
        )

        self.assertEqual(result.status, RuleAdmissionStatus.ADMITTED)
        self.assertEqual(result.code, RuleAdmissionCode.CLEAN_CATALOG)
        self.assertEqual(result.findings, ())

    def test_conflict_is_rejected(self) -> None:
        result = admit_rule_set(
            RuleSet(
                schema_version=1,
                rules=(
                    make_rule("allow", RuleDecision.ALLOW),
                    make_rule("deny", RuleDecision.DENY),
                ),
            )
        )

        self.assertEqual(result.status, RuleAdmissionStatus.REJECTED)
        self.assertEqual(result.code, RuleAdmissionCode.CONFLICTING_OVERLAP)

    def test_redundancy_requires_explicit_review(self) -> None:
        rule_set = RuleSet(
            schema_version=1,
            rules=(
                make_rule("base", RuleDecision.ALLOW),
                make_rule("specific", RuleDecision.ALLOW, region="south"),
            ),
        )

        pending = admit_rule_set(rule_set)
        admitted = admit_rule_set(
            rule_set,
            reviewed_redundancies=frozenset({("base@1", "specific@1")}),
        )

        self.assertEqual(pending.status, RuleAdmissionStatus.REVIEW)
        self.assertEqual(
            pending.code, RuleAdmissionCode.REDUNDANCY_REVIEW_REQUIRED
        )
        self.assertEqual(admitted.status, RuleAdmissionStatus.ADMITTED)

    def test_stale_redundancy_review_is_rejected(self) -> None:
        rule_set = RuleSet(
            schema_version=1,
            rules=(make_rule("base", RuleDecision.ALLOW),),
        )

        with self.assertRaisesRegex(ValueError, "current findings"):
            admit_rule_set(
                rule_set,
                reviewed_redundancies=frozenset({("old@1", "stale@1")}),
            )


if __name__ == "__main__":
    unittest.main()
