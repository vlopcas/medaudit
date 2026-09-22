"""Fail-closed admission policy for reviewed structured rule sets."""

from dataclasses import dataclass
from enum import StrEnum

from medaudit.rules.audit import (
    RuleAuditCode,
    RuleAuditFinding,
    audit_rule_set,
)
from medaudit.rules.models import RuleSet


class RuleAdmissionStatus(StrEnum):
    """Whether a rule set may enter deterministic execution."""

    ADMITTED = "admitted"
    REJECTED = "rejected"
    REVIEW = "review"


class RuleAdmissionCode(StrEnum):
    """Content-free reason for one admission outcome."""

    CLEAN_CATALOG = "clean_catalog"
    CONFLICTING_OVERLAP = "conflicting_overlap"
    REDUNDANCY_REVIEW_REQUIRED = "redundancy_review_required"


@dataclass(frozen=True, slots=True)
class RuleAdmissionResult:
    """Admission outcome and unresolved static findings."""

    status: RuleAdmissionStatus
    code: RuleAdmissionCode
    findings: tuple[RuleAuditFinding, ...]

    def __post_init__(self) -> None:
        expected_codes = {
            RuleAdmissionStatus.ADMITTED: RuleAdmissionCode.CLEAN_CATALOG,
            RuleAdmissionStatus.REJECTED: RuleAdmissionCode.CONFLICTING_OVERLAP,
            RuleAdmissionStatus.REVIEW: (
                RuleAdmissionCode.REDUNDANCY_REVIEW_REQUIRED
            ),
        }
        if self.code is not expected_codes[self.status]:
            raise ValueError("admission status and code are inconsistent")
        if self.status is RuleAdmissionStatus.ADMITTED and self.findings:
            raise ValueError("admitted catalogs cannot have unresolved findings")
        if self.status is not RuleAdmissionStatus.ADMITTED and not self.findings:
            raise ValueError("non-admitted catalogs require unresolved findings")


def admit_rule_set(
    rule_set: RuleSet,
    *,
    reviewed_redundancies: frozenset[tuple[str, str]] = frozenset(),
) -> RuleAdmissionResult:
    """Admit a catalog only after conflicts and redundancies are resolved."""
    findings = audit_rule_set(rule_set)
    redundant_pairs = {
        finding.rule_versions
        for finding in findings
        if finding.code is RuleAuditCode.REDUNDANT_OVERLAP
    }
    if not reviewed_redundancies <= redundant_pairs:
        raise ValueError("reviewed redundancies must reference current findings")

    conflicts = tuple(
        finding
        for finding in findings
        if finding.code is RuleAuditCode.CONFLICTING_OVERLAP
    )
    if conflicts:
        return RuleAdmissionResult(
            status=RuleAdmissionStatus.REJECTED,
            code=RuleAdmissionCode.CONFLICTING_OVERLAP,
            findings=conflicts,
        )

    pending_redundancies = tuple(
        finding
        for finding in findings
        if finding.code is RuleAuditCode.REDUNDANT_OVERLAP
        and finding.rule_versions not in reviewed_redundancies
    )
    if pending_redundancies:
        return RuleAdmissionResult(
            status=RuleAdmissionStatus.REVIEW,
            code=RuleAdmissionCode.REDUNDANCY_REVIEW_REQUIRED,
            findings=pending_redundancies,
        )

    return RuleAdmissionResult(
        status=RuleAdmissionStatus.ADMITTED,
        code=RuleAdmissionCode.CLEAN_CATALOG,
        findings=(),
    )
