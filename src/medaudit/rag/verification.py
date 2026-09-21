"""Independent release-verification contract for grounded synthesis."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

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
