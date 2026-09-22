"""Deterministic publication boundary for admitted structured rule sets."""

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum

from medaudit.rules.admission import (
    RuleAdmissionResult,
    RuleAdmissionStatus,
    admit_rule_set,
)
from medaudit.rules.models import RuleSet, StructuredRule


class RulePublicationStatus(StrEnum):
    """Whether a catalog was published or stopped fail-closed."""

    PUBLISHED = "published"
    BLOCKED = "blocked"
    REVIEW = "review"


class RulePublicationCode(StrEnum):
    """Content-free reason for one publication outcome."""

    PUBLISHED = "published"
    CATALOG_NOT_ADMITTED = "catalog_not_admitted"
    VERSION_REWRITE_FORBIDDEN = "version_rewrite_forbidden"
    NON_MONOTONIC_VERSION = "non_monotonic_version"
    REPLACEMENT_REVIEW_REQUIRED = "replacement_review_required"
    REMOVAL_REVIEW_REQUIRED = "removal_review_required"


@dataclass(frozen=True, slots=True)
class PublishedRuleCatalog:
    """Immutable catalog snapshot with deterministic identity and provenance."""

    publication_id: str
    rules: tuple[StructuredRule, ...]

    def __post_init__(self) -> None:
        if not self.rules:
            raise ValueError("published catalog cannot be empty")
        if self.publication_id != _publication_id(self.rules):
            raise ValueError("published catalog identity does not match its rules")


@dataclass(frozen=True, slots=True)
class RulePublicationResult:
    """Publication outcome with admission evidence and affected versions."""

    status: RulePublicationStatus
    code: RulePublicationCode
    admission: RuleAdmissionResult
    catalog: PublishedRuleCatalog | None
    affected_rule_versions: tuple[str, ...]

    def __post_init__(self) -> None:
        published = self.status is RulePublicationStatus.PUBLISHED
        if published != (self.catalog is not None):
            raise ValueError("only published outcomes may carry a catalog")
        if published and self.code is not RulePublicationCode.PUBLISHED:
            raise ValueError("published outcome requires published code")
        if not published and self.code is RulePublicationCode.PUBLISHED:
            raise ValueError("blocked publication cannot use published code")


def publish_rule_set(
    rule_set: RuleSet,
    *,
    reviewed_redundancies: frozenset[tuple[str, str]] = frozenset(),
    previous: PublishedRuleCatalog | None = None,
    reviewed_replacements: frozenset[tuple[str, str]] = frozenset(),
    reviewed_retirements: frozenset[str] = frozenset(),
    retirement_review_publication_id: str | None = None,
) -> RulePublicationResult:
    """Publish only admitted catalogs and explicitly reviewed version changes."""
    admission = admit_rule_set(
        rule_set,
        reviewed_redundancies=reviewed_redundancies,
    )
    if admission.status is not RuleAdmissionStatus.ADMITTED:
        status = (
            RulePublicationStatus.REVIEW
            if admission.status is RuleAdmissionStatus.REVIEW
            else RulePublicationStatus.BLOCKED
        )
        return RulePublicationResult(
            status=status,
            code=RulePublicationCode.CATALOG_NOT_ADMITTED,
            admission=admission,
            catalog=None,
            affected_rule_versions=tuple(
                version
                for finding in admission.findings
                for version in finding.rule_versions
            ),
        )

    ordered_rules = tuple(sorted(rule_set.rules, key=_rule_sort_key))
    if previous is None:
        if reviewed_replacements or reviewed_retirements:
            raise ValueError("initial publication cannot review prior changes")
        if retirement_review_publication_id is not None:
            raise ValueError("initial publication cannot reference prior publication")
        return _published(ordered_rules, admission)

    if reviewed_retirements and (
        retirement_review_publication_id != previous.publication_id
    ):
        raise ValueError("retirement review must reference previous publication")
    if not reviewed_retirements and retirement_review_publication_id is not None:
        raise ValueError("retirement publication reference requires reviewed rules")

    previous_by_identity = {_identity(rule): rule for rule in previous.rules}
    current_by_identity = {_identity(rule): rule for rule in ordered_rules}
    rewritten = tuple(
        sorted(
            _rule_version(current)
            for identity, current in current_by_identity.items()
            if identity in previous_by_identity
            and current != previous_by_identity[identity]
        )
    )
    if rewritten:
        return _stopped(
            RulePublicationStatus.BLOCKED,
            RulePublicationCode.VERSION_REWRITE_FORBIDDEN,
            admission,
            rewritten,
        )

    previous_by_id = _group_by_rule_id(previous.rules)
    current_by_id = _group_by_rule_id(ordered_rules)
    non_monotonic = tuple(
        sorted(
            _rule_version(rule)
            for rule_id, rules in current_by_id.items()
            for rule in rules
            if _identity(rule) not in previous_by_identity
            and rule_id in previous_by_id
            and rule.version <= max(item.version for item in previous_by_id[rule_id])
        )
    )
    if non_monotonic:
        return _stopped(
            RulePublicationStatus.BLOCKED,
            RulePublicationCode.NON_MONOTONIC_VERSION,
            admission,
            non_monotonic,
        )

    removed_ids = {
        rule_id for rule_id in previous_by_id if rule_id not in current_by_id
    }
    required_retirements = {
        _rule_version(rule)
        for rule_id in removed_ids
        for rule in previous_by_id[rule_id]
    }
    if not reviewed_retirements <= required_retirements:
        raise ValueError("reviewed retirements must reference current removals")

    required_replacements = {
        (
            _rule_version(max(previous_by_id[rule_id], key=lambda item: item.version)),
            _rule_version(rule),
        )
        for rule_id, rules in current_by_id.items()
        if rule_id in previous_by_id
        for rule in rules
        if _identity(rule) not in previous_by_identity
    }
    if not reviewed_replacements <= required_replacements:
        raise ValueError("reviewed replacements must reference current changes")
    pending_replacements = required_replacements - reviewed_replacements
    if pending_replacements:
        return _stopped(
            RulePublicationStatus.REVIEW,
            RulePublicationCode.REPLACEMENT_REVIEW_REQUIRED,
            admission,
            tuple(sorted(version for pair in pending_replacements for version in pair)),
        )

    pending_retirements = required_retirements - reviewed_retirements
    if pending_retirements:
        return _stopped(
            RulePublicationStatus.REVIEW,
            RulePublicationCode.REMOVAL_REVIEW_REQUIRED,
            admission,
            tuple(sorted(pending_retirements)),
        )
    return _published(ordered_rules, admission)


def _published(
    rules: tuple[StructuredRule, ...], admission: RuleAdmissionResult
) -> RulePublicationResult:
    return RulePublicationResult(
        status=RulePublicationStatus.PUBLISHED,
        code=RulePublicationCode.PUBLISHED,
        admission=admission,
        catalog=PublishedRuleCatalog(
            publication_id=_publication_id(rules),
            rules=rules,
        ),
        affected_rule_versions=tuple(_rule_version(rule) for rule in rules),
    )


def _stopped(
    status: RulePublicationStatus,
    code: RulePublicationCode,
    admission: RuleAdmissionResult,
    versions: tuple[str, ...],
) -> RulePublicationResult:
    return RulePublicationResult(
        status=status,
        code=code,
        admission=admission,
        catalog=None,
        affected_rule_versions=versions,
    )


def _publication_id(rules: tuple[StructuredRule, ...]) -> str:
    payload = [asdict(rule) for rule in sorted(rules, key=_rule_sort_key)]
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _group_by_rule_id(
    rules: tuple[StructuredRule, ...],
) -> dict[str, tuple[StructuredRule, ...]]:
    return {
        rule_id: tuple(rule for rule in rules if rule.rule_id == rule_id)
        for rule_id in {rule.rule_id for rule in rules}
    }


def _identity(rule: StructuredRule) -> tuple[str, int]:
    return rule.rule_id, rule.version


def _rule_version(rule: StructuredRule) -> str:
    return f"{rule.rule_id}@{rule.version}"


def _rule_sort_key(rule: StructuredRule) -> tuple[str, int]:
    return rule.rule_id, rule.version
