"""Provider-neutral deterministic context compilation."""

from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum
from typing import Protocol

from medaudit.rag.models import DecompositionEvidenceBundle, Evidence


class ContextStatus(StrEnum):
    """Decision produced before a context can reach a model."""

    READY = "ready"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    BUDGET_EXCEEDED = "budget_exceeded"
    NEEDS_REVIEW = "needs_review"


class ContextItemKind(StrEnum):
    """Structurally separated sources of model context."""

    INSTRUCTION = "instruction"
    QUERY = "query"
    EVIDENCE = "evidence"


class ContextTrust(StrEnum):
    """Whether an item may control behavior or is untrusted data."""

    TRUSTED_CONTROL = "trusted_control"
    UNTRUSTED_DATA = "untrusted_data"


class ContextExclusionReason(StrEnum):
    """Auditable reasons for leaving an item outside the compiled context."""

    DUPLICATE = "duplicate"
    TOKEN_BUDGET = "token_budget"
    REVIEW_REQUIRED = "review_required"
    CONFLICTING_IDENTITY = "conflicting_identity"


class TokenEstimator(Protocol):
    """Boundary for provider-specific or deterministic token estimation."""

    def estimate(self, text: str) -> int:
        """Return a positive token estimate for non-empty text."""
        ...


@dataclass(frozen=True, slots=True)
class Utf8ByteTokenEstimator:
    """Deterministic approximation usable without a model tokenizer."""

    bytes_per_token: int = 4

    def __post_init__(self) -> None:
        if self.bytes_per_token <= 0:
            raise ValueError("bytes_per_token must be positive")

    def estimate(self, text: str) -> int:
        if not text:
            return 0
        byte_count = len(text.encode("utf-8"))
        return max(1, (byte_count + self.bytes_per_token - 1) // self.bytes_per_token)


@dataclass(frozen=True, slots=True)
class ContextItem:
    """A typed context block with provenance and an explicit trust boundary."""

    item_id: str
    kind: ContextItemKind
    trust: ContextTrust
    text: str
    estimated_tokens: int
    step_ids: tuple[str, ...] = ()
    document_id: str | None = None
    page: int | None = None
    section: str | None = None


@dataclass(frozen=True, slots=True)
class CompiledContextGroup:
    """Content-free step metadata used to render selected evidence safely."""

    step_id: str
    scope: str | None
    reference_date: date | None
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContextExclusion:
    """Content-free audit record for an item not included in context."""

    item_id: str
    reason: ContextExclusionReason


@dataclass(frozen=True, slots=True)
class CompiledContext:
    """Bounded context candidate that has not yet been rendered for a provider."""

    status: ContextStatus
    token_budget: int
    estimated_tokens: int
    items: tuple[ContextItem, ...] = ()
    groups: tuple[CompiledContextGroup, ...] = ()
    exclusions: tuple[ContextExclusion, ...] = ()

    @property
    def can_generate(self) -> bool:
        return self.status is ContextStatus.READY


def _same_evidence_identity(left: Evidence, right: Evidence) -> bool:
    return (
        left.location.chunk_id,
        left.location.document_id,
        left.location.page,
        left.location.section,
        left.text,
    ) == (
        right.location.chunk_id,
        right.location.document_id,
        right.location.page,
        right.location.section,
        right.text,
    )


def compile_decomposed_context(
    bundle: DecompositionEvidenceBundle,
    *,
    instruction: str,
    token_budget: int,
    estimator: TokenEstimator | None = None,
    review_evidence_ids: frozenset[str] = frozenset(),
) -> CompiledContext:
    """Compile grouped evidence without merging it into trusted instructions."""
    if token_budget <= 0:
        raise ValueError("token_budget must be positive")
    if not instruction.strip():
        raise ValueError("instruction must not be blank")
    token_estimator = estimator or Utf8ByteTokenEstimator()
    query = bundle.execution.plan.original_query
    control_items = (
        ContextItem(
            item_id="instruction",
            kind=ContextItemKind.INSTRUCTION,
            trust=ContextTrust.TRUSTED_CONTROL,
            text=instruction,
            estimated_tokens=token_estimator.estimate(instruction),
        ),
        ContextItem(
            item_id="query",
            kind=ContextItemKind.QUERY,
            trust=ContextTrust.UNTRUSTED_DATA,
            text=query,
            estimated_tokens=token_estimator.estimate(query),
        ),
    )
    control_tokens = sum(item.estimated_tokens for item in control_items)
    if control_tokens > token_budget:
        return CompiledContext(
            status=ContextStatus.BUDGET_EXCEEDED,
            token_budget=token_budget,
            estimated_tokens=control_tokens,
            exclusions=(
                ContextExclusion("instruction", ContextExclusionReason.TOKEN_BUDGET),
                ContextExclusion("query", ContextExclusionReason.TOKEN_BUDGET),
            ),
        )
    if not bundle.can_generate or not bundle.groups:
        return CompiledContext(
            status=ContextStatus.INSUFFICIENT_EVIDENCE,
            token_budget=token_budget,
            estimated_tokens=control_tokens,
            items=control_items,
        )

    unique: dict[str, tuple[Evidence, ContextItem]] = {}
    exclusions: list[ContextExclusion] = []
    review_required = False
    for group in bundle.groups:
        for evidence in group.evidence:
            evidence_id = evidence.location.chunk_id
            if evidence_id in review_evidence_ids:
                review_required = True
                exclusions.append(
                    ContextExclusion(
                        evidence_id, ContextExclusionReason.REVIEW_REQUIRED
                    )
                )
                continue
            existing = unique.get(evidence_id)
            if existing:
                original, item = existing
                if not _same_evidence_identity(original, evidence):
                    review_required = True
                    exclusions.append(
                        ContextExclusion(
                            evidence_id,
                            ContextExclusionReason.CONFLICTING_IDENTITY,
                        )
                    )
                    continue
                if group.step.step_id not in item.step_ids:
                    unique[evidence_id] = (
                        original,
                        replace(item, step_ids=(*item.step_ids, group.step.step_id)),
                    )
                exclusions.append(
                    ContextExclusion(evidence_id, ContextExclusionReason.DUPLICATE)
                )
                continue
            unique[evidence_id] = (
                evidence,
                ContextItem(
                    item_id=evidence_id,
                    kind=ContextItemKind.EVIDENCE,
                    trust=ContextTrust.UNTRUSTED_DATA,
                    text=evidence.text,
                    estimated_tokens=token_estimator.estimate(evidence.text),
                    step_ids=(group.step.step_id,),
                    document_id=evidence.location.document_id,
                    page=evidence.location.page,
                    section=evidence.location.section,
                ),
            )
    if review_required:
        return CompiledContext(
            status=ContextStatus.NEEDS_REVIEW,
            token_budget=token_budget,
            estimated_tokens=control_tokens,
            items=control_items,
            exclusions=tuple(exclusions),
        )

    selected = list(control_items)
    used_tokens = control_tokens
    selected_steps: set[str] = set()
    for _, item in unique.values():
        if used_tokens + item.estimated_tokens > token_budget:
            exclusions.append(
                ContextExclusion(item.item_id, ContextExclusionReason.TOKEN_BUDGET)
            )
            continue
        selected.append(item)
        used_tokens += item.estimated_tokens
        selected_steps.update(item.step_ids)
    required_steps = {group.step.step_id for group in bundle.groups}
    status = (
        ContextStatus.READY
        if selected_steps == required_steps
        else ContextStatus.BUDGET_EXCEEDED
    )
    groups: tuple[CompiledContextGroup, ...] = ()
    if status is ContextStatus.READY:
        evidence_items = [
            item for item in selected if item.kind is ContextItemKind.EVIDENCE
        ]
        groups = tuple(
            CompiledContextGroup(
                step_id=group.step.step_id,
                scope=group.step.scope,
                reference_date=group.step.reference_date,
                evidence_ids=tuple(
                    item.item_id
                    for item in evidence_items
                    if group.step.step_id in item.step_ids
                ),
            )
            for group in bundle.groups
        )
    return CompiledContext(
        status=status,
        token_budget=token_budget,
        estimated_tokens=used_tokens,
        items=tuple(selected),
        groups=groups,
        exclusions=tuple(exclusions),
    )
