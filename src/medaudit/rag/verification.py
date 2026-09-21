"""Independent release-verification contract for grounded synthesis."""

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from medaudit.rag.evidence_safety import assess_decomposed_evidence
from medaudit.rag.models import DecompositionEvidenceBundle
from medaudit.rag.validation import DecomposedGroundedAnswer


class VerificationDecision(StrEnum):
    """Allowed outcomes before a structurally valid answer can be released."""

    RELEASE = "release"
    REJECT = "reject"
    REVIEW = "review"


class VerificationCode(StrEnum):
    """Content-free reason codes safe for operational telemetry."""

    CLAIM_SUPPORT_FAILED = "claim_support_failed"
    UNTRUSTED_CONTENT = "untrusted_content"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """A verifier decision that never carries answer or evidence text."""

    decision: VerificationDecision
    code: VerificationCode | None = None

    def __post_init__(self) -> None:
        if self.decision is VerificationDecision.RELEASE and self.code is not None:
            raise ValueError("release verification cannot include a failure code")
        if self.decision is not VerificationDecision.RELEASE and self.code is None:
            raise ValueError("non-release verification requires a reason code")


class GroundedAnswerVerifier(Protocol):
    """Verify an answer independently from generation and structural parsing."""

    def verify(
        self,
        answer: DecomposedGroundedAnswer,
        evidence: DecompositionEvidenceBundle,
    ) -> VerificationResult: ...


_STOPWORDS = frozenset(
    {
        "a",
        "as",
        "com",
        "da",
        "das",
        "de",
        "do",
        "dos",
        "e",
        "em",
        "is",
        "o",
        "os",
        "para",
        "the",
        "um",
        "uma",
    }
)


def _content_tokens(text: str) -> frozenset[str]:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    normalized = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return frozenset(
        token
        for token in re.findall(r"[a-z0-9]+", normalized)
        if len(token) > 1 and token not in _STOPWORDS
    )


@dataclass(frozen=True, slots=True)
class ConservativeLexicalVerifier:
    """Review suspicious evidence and reject claims with weak cited overlap."""

    minimum_claim_coverage: float = 0.6

    def __post_init__(self) -> None:
        if not 0 < self.minimum_claim_coverage <= 1:
            raise ValueError("minimum claim coverage must be within (0, 1]")

    def verify(
        self,
        answer: DecomposedGroundedAnswer,
        evidence: DecompositionEvidenceBundle,
    ) -> VerificationResult:
        if answer.status == "insufficient_evidence":
            return VerificationResult(VerificationDecision.RELEASE)
        if not assess_decomposed_evidence(evidence).can_generate:
            return VerificationResult(
                VerificationDecision.REVIEW,
                VerificationCode.UNTRUSTED_CONTENT,
            )
        evidence_by_id = {
            item.location.chunk_id: item.text
            for group in evidence.groups
            for item in group.evidence
        }
        for claim in answer.claims:
            claim_tokens = _content_tokens(claim.text)
            cited_tokens = frozenset(
                token
                for support in claim.supports
                for citation in support.citations
                for token in _content_tokens(evidence_by_id[citation.chunk_id])
            )
            coverage = (
                len(claim_tokens & cited_tokens) / len(claim_tokens)
                if claim_tokens
                else 0.0
            )
            if coverage < self.minimum_claim_coverage:
                return VerificationResult(
                    VerificationDecision.REJECT,
                    VerificationCode.CLAIM_SUPPORT_FAILED,
                )
        return VerificationResult(VerificationDecision.RELEASE)
