"""Validate grounded model output against the authorized evidence set."""

from dataclasses import dataclass
from typing import Any

from medaudit.llm import LLMResponse
from medaudit.rag.models import (
    DecompositionEvidenceBundle,
    EvidenceLocation,
    RetrievalDecision,
)


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    """Validated answer whose citations resolve to retrieved evidence."""

    status: str
    answer: str
    citations: tuple[EvidenceLocation, ...]


@dataclass(frozen=True, slots=True)
class ClaimSupport:
    """Validated citations resolved within one decomposition step."""

    step_id: str
    citations: tuple[EvidenceLocation, ...]


@dataclass(frozen=True, slots=True)
class GroundedClaim:
    """Atomic claim paired with one or more step-scoped supports."""

    text: str
    supports: tuple[ClaimSupport, ...]


@dataclass(frozen=True, slots=True)
class DecomposedGroundedAnswer:
    """Validated multi-step answer that preserves claim provenance."""

    status: str
    claims: tuple[GroundedClaim, ...]


def validate_grounded_response(
    response: LLMResponse, decision: RetrievalDecision
) -> GroundedAnswer:
    """Reject malformed answers and citations outside the evidence package."""
    if not decision.can_generate or not decision.evidence:
        raise ValueError("response validation requires accepted evidence")
    status = response.data.get("status")
    answer = response.data.get("answer")
    evidence_ids = response.data.get("evidence_ids")
    if status not in {"answered", "insufficient_evidence"}:
        raise ValueError("unsupported grounded response status")
    if not isinstance(answer, str):
        raise ValueError("grounded answer must be text")
    if not isinstance(evidence_ids, list) or not all(
        isinstance(item, str) for item in evidence_ids
    ):
        raise ValueError("grounded response evidence_ids must be a string list")
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("grounded response contains duplicate citations")

    locations = {item.location.chunk_id: item.location for item in decision.evidence}
    unknown = set(evidence_ids) - locations.keys()
    if unknown:
        raise ValueError("grounded response cites unauthorized evidence")
    if status == "answered" and (not answer.strip() or not evidence_ids):
        raise ValueError("answered response requires text and citations")
    if status == "insufficient_evidence" and (answer.strip() or evidence_ids):
        raise ValueError("insufficient evidence response must be empty")
    return GroundedAnswer(
        status=status,
        answer=answer,
        citations=tuple(locations[item] for item in evidence_ids),
    )


def validate_decomposed_grounded_response(
    response: LLMResponse,
    bundle: DecompositionEvidenceBundle,
) -> DecomposedGroundedAnswer:
    """Validate claim citations against their exact step-scoped groups."""
    if not bundle.can_generate:
        raise ValueError("response validation requires complete grouped evidence")
    status = response.data.get("status")
    raw_claims = response.data.get("claims")
    if status not in {"answered", "insufficient_evidence"}:
        raise ValueError("unsupported decomposed response status")
    if not isinstance(raw_claims, list):
        raise ValueError("decomposed response claims must be a list")
    if status == "insufficient_evidence":
        if raw_claims:
            raise ValueError("insufficient evidence response must have no claims")
        return DecomposedGroundedAnswer(status=status, claims=())
    if not raw_claims:
        raise ValueError("answered decomposed response requires claims")

    authorized = {
        group.step.step_id: {
            evidence.location.chunk_id: evidence.location
            for evidence in group.evidence
        }
        for group in bundle.groups
    }
    used_steps: set[str] = set()
    claims: list[GroundedClaim] = []
    for raw_claim in raw_claims:
        if not isinstance(raw_claim, dict):
            raise ValueError("each decomposed claim must be an object")
        text = raw_claim.get("text")
        raw_supports = raw_claim.get("supports")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("each decomposed claim requires text")
        if not isinstance(raw_supports, list) or not raw_supports:
            raise ValueError("each decomposed claim requires supports")
        supports = tuple(
            _validate_claim_support(raw_support, authorized)
            for raw_support in raw_supports
        )
        support_steps = [support.step_id for support in supports]
        if len(support_steps) != len(set(support_steps)):
            raise ValueError("claim contains duplicate step supports")
        used_steps.update(support_steps)
        claims.append(GroundedClaim(text=text, supports=supports))
    if used_steps != set(authorized):
        raise ValueError("answered response must cite every evidence group")
    return DecomposedGroundedAnswer(status=status, claims=tuple(claims))


def _validate_claim_support(
    raw_support: Any,
    authorized: dict[str, dict[str, EvidenceLocation]],
) -> ClaimSupport:
    if not isinstance(raw_support, dict):
        raise ValueError("claim support must be an object")
    step_id = raw_support.get("step_id")
    evidence_ids = raw_support.get("evidence_ids")
    if not isinstance(step_id, str) or step_id not in authorized:
        raise ValueError("claim support references an unknown step")
    if not isinstance(evidence_ids, list) or not evidence_ids or not all(
        isinstance(item, str) for item in evidence_ids
    ):
        raise ValueError("claim support requires evidence_ids")
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("claim support contains duplicate citations")
    if set(evidence_ids) - authorized[step_id].keys():
        raise ValueError("claim cites evidence outside its step")
    return ClaimSupport(
        step_id=step_id,
        citations=tuple(authorized[step_id][item] for item in evidence_ids),
    )
