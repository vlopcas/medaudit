"""Models for gated retrieval and traceable evidence."""

from dataclasses import dataclass
from enum import StrEnum

from medaudit.retrieval import ConfidenceSignals


class RetrievalStatus(StrEnum):
    """Outcome decided before any generative model is called."""

    READY = "ready"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class EvidenceLocation:
    """Stable source coordinates exposed as a citation."""

    chunk_id: str
    document_id: str
    rank: int
    score: float
    page: int | None
    section: str | None


@dataclass(frozen=True, slots=True)
class Evidence:
    """Private passage paired with its source coordinates."""

    location: EvidenceLocation
    text: str


@dataclass(frozen=True, slots=True)
class RetrievalDecision:
    """Gated evidence package produced before grounded generation."""

    query: str
    status: RetrievalStatus
    signals: ConfidenceSignals
    evidence: tuple[Evidence, ...] = ()

    @property
    def can_generate(self) -> bool:
        """Return whether grounded generation is permitted."""
        return self.status is RetrievalStatus.READY
