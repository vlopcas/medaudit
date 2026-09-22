"""Static overlap audit for reviewed structured rule sets."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from itertools import combinations

from medaudit.rules.models import RuleSet, StructuredRule


class RuleAuditCode(StrEnum):
    """Closed classes of actionable static overlap."""

    CONFLICTING_OVERLAP = "conflicting_overlap"
    REDUNDANT_OVERLAP = "redundant_overlap"


@dataclass(frozen=True, slots=True)
class RuleAuditFinding:
    """Content-free pair of rule versions requiring catalog review."""

    code: RuleAuditCode
    rule_versions: tuple[str, str]

    def __post_init__(self) -> None:
        if len(set(self.rule_versions)) != 2:
            raise ValueError("audit finding requires two distinct rule versions")
        if self.rule_versions != tuple(sorted(self.rule_versions)):
            raise ValueError("audit finding rule versions must be sorted")


def audit_rule_set(rule_set: RuleSet) -> tuple[RuleAuditFinding, ...]:
    """Find same-priority overlaps that can match at least one shared query."""
    findings: list[RuleAuditFinding] = []
    for left, right in combinations(rule_set.rules, 2):
        if not _same_resolution_scope(left, right):
            continue
        if not _periods_overlap(left, right):
            continue
        if not _conditions_are_compatible(left, right):
            continue
        code = (
            RuleAuditCode.REDUNDANT_OVERLAP
            if left.decision is right.decision
            else RuleAuditCode.CONFLICTING_OVERLAP
        )
        left_version = f"{left.rule_id}@{left.version}"
        right_version = f"{right.rule_id}@{right.version}"
        ordered_versions = (
            (left_version, right_version)
            if left_version < right_version
            else (right_version, left_version)
        )
        findings.append(
            RuleAuditFinding(
                code=code,
                rule_versions=ordered_versions,
            )
        )
    return tuple(
        sorted(findings, key=lambda item: (item.code.value, item.rule_versions))
    )


def _same_resolution_scope(left: StructuredRule, right: StructuredRule) -> bool:
    return (
        left.subject == right.subject
        and left.action == right.action
        and left.priority == right.priority
    )


def _periods_overlap(left: StructuredRule, right: StructuredRule) -> bool:
    left_end = left.effective_until or date.max
    right_end = right.effective_until or date.max
    return max(left.effective_from, right.effective_from) <= min(left_end, right_end)


def _conditions_are_compatible(
    left: StructuredRule, right: StructuredRule
) -> bool:
    left_conditions = dict(left.conditions)
    right_conditions = dict(right.conditions)
    shared_keys = left_conditions.keys() & right_conditions.keys()
    return all(left_conditions[key] == right_conditions[key] for key in shared_keys)
