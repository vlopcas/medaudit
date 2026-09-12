"""Validate grounded model output against the authorized evidence set."""

from dataclasses import dataclass

from medaudit.llm import LLMResponse
from medaudit.rag.models import EvidenceLocation, RetrievalDecision


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    """Validated answer whose citations resolve to retrieved evidence."""

    status: str
    answer: str
    citations: tuple[EvidenceLocation, ...]


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
