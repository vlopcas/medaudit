import unittest
from dataclasses import replace
from datetime import date

from medaudit.rules import (
    RuleDecision,
    RulePublicationCode,
    RulePublicationStatus,
    RuleSet,
    StructuredRule,
    publish_rule_set,
)


def make_rule(
    rule_id: str,
    *,
    version: int = 1,
    decision: RuleDecision = RuleDecision.ALLOW,
    source: str | None = None,
) -> StructuredRule:
    return StructuredRule(
        rule_id=rule_id,
        version=version,
        subject=rule_id,
        action="apply",
        decision=decision,
        effective_from=date(2026, 1, 1),
        effective_until=None,
        priority=5,
        conditions=(("tier", "alpha"),),
        source_document_id=source or f"source-{rule_id}-{version}",
    )


def make_set(*rules: StructuredRule) -> RuleSet:
    return RuleSet(schema_version=1, rules=rules)


class StructuredRulePublicationTest(unittest.TestCase):
    def test_initial_publication_preserves_ordered_provenance(self) -> None:
        result = publish_rule_set(
            make_set(make_rule("zeta"), make_rule("alpha"))
        )

        self.assertEqual(result.status, RulePublicationStatus.PUBLISHED)
        self.assertEqual(result.code, RulePublicationCode.PUBLISHED)
        self.assertIsNotNone(result.catalog)
        assert result.catalog is not None
        self.assertEqual(
            tuple(rule.rule_id for rule in result.catalog.rules),
            ("alpha", "zeta"),
        )
        self.assertEqual(
            tuple(rule.source_document_id for rule in result.catalog.rules),
            ("source-alpha-1", "source-zeta-1"),
        )

    def test_non_admitted_catalog_is_not_published(self) -> None:
        allow = make_rule("allow")
        deny = replace(
            allow,
            rule_id="deny",
            decision=RuleDecision.DENY,
            source_document_id="source-deny",
        )

        result = publish_rule_set(make_set(allow, deny))

        self.assertEqual(result.status, RulePublicationStatus.BLOCKED)
        self.assertEqual(result.code, RulePublicationCode.CATALOG_NOT_ADMITTED)
        self.assertIsNone(result.catalog)

    def test_same_version_rewrite_is_blocked(self) -> None:
        first = publish_rule_set(make_set(make_rule("stable")))
        assert first.catalog is not None
        rewritten = make_rule("stable", source="changed-source")

        result = publish_rule_set(
            make_set(rewritten),
            previous=first.catalog,
        )

        self.assertEqual(result.status, RulePublicationStatus.BLOCKED)
        self.assertEqual(
            result.code, RulePublicationCode.VERSION_REWRITE_FORBIDDEN
        )

    def test_new_version_requires_explicit_replacement_review(self) -> None:
        first = publish_rule_set(make_set(make_rule("versioned")))
        assert first.catalog is not None
        second_set = make_set(make_rule("versioned", version=2))

        pending = publish_rule_set(second_set, previous=first.catalog)
        published = publish_rule_set(
            second_set,
            previous=first.catalog,
            reviewed_replacements=frozenset({("versioned@1", "versioned@2")}),
        )

        self.assertEqual(pending.status, RulePublicationStatus.REVIEW)
        self.assertEqual(
            pending.code, RulePublicationCode.REPLACEMENT_REVIEW_REQUIRED
        )
        self.assertEqual(published.status, RulePublicationStatus.PUBLISHED)

    def test_non_monotonic_version_is_blocked(self) -> None:
        first = publish_rule_set(make_set(make_rule("versioned", version=2)))
        assert first.catalog is not None

        result = publish_rule_set(
            make_set(make_rule("versioned", version=1)),
            previous=first.catalog,
        )

        self.assertEqual(result.status, RulePublicationStatus.BLOCKED)
        self.assertEqual(result.code, RulePublicationCode.NON_MONOTONIC_VERSION)

    def test_silent_removal_requires_review(self) -> None:
        first = publish_rule_set(make_set(make_rule("keep"), make_rule("remove")))
        assert first.catalog is not None

        result = publish_rule_set(
            make_set(make_rule("keep")),
            previous=first.catalog,
        )

        self.assertEqual(result.status, RulePublicationStatus.REVIEW)
        self.assertEqual(result.code, RulePublicationCode.REMOVAL_REVIEW_REQUIRED)

    def test_snapshot_bound_retirement_is_published(self) -> None:
        first = publish_rule_set(make_set(make_rule("keep"), make_rule("retire")))
        assert first.catalog is not None

        result = publish_rule_set(
            make_set(make_rule("keep")),
            previous=first.catalog,
            reviewed_retirements=frozenset({"retire@1"}),
            retirement_review_publication_id=first.catalog.publication_id,
        )

        self.assertEqual(result.status, RulePublicationStatus.PUBLISHED)

    def test_partial_retirement_review_keeps_catalog_in_review(self) -> None:
        first = publish_rule_set(
            make_set(
                make_rule("keep"),
                make_rule("retire-a"),
                make_rule("retire-b"),
            )
        )
        assert first.catalog is not None

        result = publish_rule_set(
            make_set(make_rule("keep")),
            previous=first.catalog,
            reviewed_retirements=frozenset({"retire-a@1"}),
            retirement_review_publication_id=first.catalog.publication_id,
        )

        self.assertEqual(result.status, RulePublicationStatus.REVIEW)
        self.assertEqual(result.affected_rule_versions, ("retire-b@1",))

    def test_retirement_review_for_stale_snapshot_is_rejected(self) -> None:
        first = publish_rule_set(make_set(make_rule("keep"), make_rule("retire")))
        assert first.catalog is not None

        with self.assertRaisesRegex(ValueError, "previous publication"):
            publish_rule_set(
                make_set(make_rule("keep")),
                previous=first.catalog,
                reviewed_retirements=frozenset({"retire@1"}),
                retirement_review_publication_id="stale-publication",
            )

    def test_retirement_review_for_present_rule_is_rejected(self) -> None:
        first = publish_rule_set(make_set(make_rule("keep"), make_rule("present")))
        assert first.catalog is not None

        with self.assertRaisesRegex(ValueError, "current removals"):
            publish_rule_set(
                make_set(make_rule("keep"), make_rule("present")),
                previous=first.catalog,
                reviewed_retirements=frozenset({"present@1"}),
                retirement_review_publication_id=first.catalog.publication_id,
            )

    def test_stale_replacement_review_is_rejected(self) -> None:
        first = publish_rule_set(make_set(make_rule("versioned")))
        assert first.catalog is not None

        with self.assertRaisesRegex(ValueError, "current changes"):
            publish_rule_set(
                make_set(make_rule("versioned", version=2)),
                previous=first.catalog,
                reviewed_replacements=frozenset(
                    {("versioned@1", "versioned@3")}
                ),
            )


if __name__ == "__main__":
    unittest.main()
