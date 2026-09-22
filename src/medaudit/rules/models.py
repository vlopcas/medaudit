"""Versioned, deterministic contracts for reviewed structured rules."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class RuleDecision(StrEnum):
    """Closed outcomes that a reviewed rule may encode."""

    ALLOW = "allow"
    DENY = "deny"


class RuleResolutionStatus(StrEnum):
    """Whether deterministic evaluation produced a usable decision."""

    APPLIED = "applied"
    NO_MATCH = "no_match"
    REVIEW = "review"


class RuleResolutionCode(StrEnum):
    """Content-free reason for one resolution state."""

    ACTIVE_RULE = "active_rule"
    NO_APPLICABLE_RULE = "no_applicable_rule"
    CONFLICTING_RULES = "conflicting_rules"


@dataclass(frozen=True, slots=True)
class StructuredRule:
    """One reviewed rule version with explicit scope and provenance."""

    rule_id: str
    version: int
    subject: str
    action: str
    decision: RuleDecision
    effective_from: date
    effective_until: date | None
    priority: int
    conditions: tuple[tuple[str, str], ...]
    source_document_id: str

    def __post_init__(self) -> None:
        if not all((self.rule_id, self.subject, self.action, self.source_document_id)):
            raise ValueError("rule identity, scope and source are required")
        if self.version < 1:
            raise ValueError("rule version must be positive")
        if self.priority < 0:
            raise ValueError("rule priority cannot be negative")
        if (
            self.effective_until is not None
            and self.effective_until < self.effective_from
        ):
            raise ValueError("rule effective period is invalid")
        keys = [key for key, value in self.conditions if key and value]
        if len(keys) != len(self.conditions) or len(keys) != len(set(keys)):
            raise ValueError("rule conditions require unique non-empty keys and values")

    def is_effective_on(self, reference_date: date) -> bool:
        return self.effective_from <= reference_date and (
            self.effective_until is None or reference_date <= self.effective_until
        )


@dataclass(frozen=True, slots=True)
class RuleSet:
    """A versioned collection of reviewed rules."""

    schema_version: int
    rules: tuple[StructuredRule, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported rule schema version")
        if not self.rules:
            raise ValueError("rule set cannot be empty")
        identities = [(rule.rule_id, rule.version) for rule in self.rules]
        if len(identities) != len(set(identities)):
            raise ValueError("rule id and version pairs must be unique")


@dataclass(frozen=True, slots=True)
class RuleQuery:
    """Explicit input to deterministic rule resolution."""

    subject: str
    action: str
    reference_date: date
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.subject or not self.action:
            raise ValueError("rule query subject and action are required")
        keys = [key for key, value in self.attributes if key and value]
        if len(keys) != len(self.attributes) or len(keys) != len(set(keys)):
            raise ValueError(
                "query attributes require unique non-empty keys and values"
            )


@dataclass(frozen=True, slots=True)
class RuleResolution:
    """Content-free decision plus rule-version provenance."""

    status: RuleResolutionStatus
    code: RuleResolutionCode
    decision: RuleDecision | None
    matched_rule_versions: tuple[str, ...]

    def __post_init__(self) -> None:
        has_decision = self.decision is not None
        if (self.status is RuleResolutionStatus.APPLIED) != has_decision:
            raise ValueError("only applied resolutions may carry a decision")
        expected_codes = {
            RuleResolutionStatus.APPLIED: RuleResolutionCode.ACTIVE_RULE,
            RuleResolutionStatus.NO_MATCH: RuleResolutionCode.NO_APPLICABLE_RULE,
            RuleResolutionStatus.REVIEW: RuleResolutionCode.CONFLICTING_RULES,
        }
        if self.code is not expected_codes[self.status]:
            raise ValueError("resolution status and code are inconsistent")
        if (
            self.status is RuleResolutionStatus.APPLIED
            and not self.matched_rule_versions
        ):
            raise ValueError("applied resolution requires rule provenance")
        if self.status is RuleResolutionStatus.NO_MATCH and self.matched_rule_versions:
            raise ValueError("no-match resolution cannot carry rule provenance")
        if (
            self.status is RuleResolutionStatus.REVIEW
            and len(self.matched_rule_versions) < 2
        ):
            raise ValueError("conflict review requires at least two rule versions")
