"""Deterministic resolution for reviewed structured rules."""

from dataclasses import dataclass

from medaudit.rules.models import (
    RuleQuery,
    RuleResolution,
    RuleResolutionCode,
    RuleResolutionStatus,
    RuleSet,
)


@dataclass(frozen=True, slots=True)
class DeterministicRuleEngine:
    """Resolve exact scopes, dates and conditions without an LLM."""

    rule_set: RuleSet

    def resolve(self, query: RuleQuery) -> RuleResolution:
        attributes = dict(query.attributes)
        candidates = [
            rule
            for rule in self.rule_set.rules
            if rule.subject == query.subject
            and rule.action == query.action
            and rule.is_effective_on(query.reference_date)
            and all(attributes.get(key) == value for key, value in rule.conditions)
        ]
        if not candidates:
            return RuleResolution(
                status=RuleResolutionStatus.NO_MATCH,
                code=RuleResolutionCode.NO_APPLICABLE_RULE,
                decision=None,
                matched_rule_versions=(),
            )
        highest_priority = max(rule.priority for rule in candidates)
        selected = sorted(
            (rule for rule in candidates if rule.priority == highest_priority),
            key=lambda rule: (rule.rule_id, rule.version),
        )
        provenance = tuple(
            f"{rule.rule_id}@{rule.version}" for rule in selected
        )
        decisions = {rule.decision for rule in selected}
        if len(decisions) != 1:
            return RuleResolution(
                status=RuleResolutionStatus.REVIEW,
                code=RuleResolutionCode.CONFLICTING_RULES,
                decision=None,
                matched_rule_versions=provenance,
            )
        return RuleResolution(
            status=RuleResolutionStatus.APPLIED,
            code=RuleResolutionCode.ACTIVE_RULE,
            decision=decisions.pop(),
            matched_rule_versions=provenance,
        )
