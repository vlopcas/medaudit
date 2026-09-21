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

_NUMBER_WORDS = {
    "zero": "0",
    "um": "1",
    "uma": "1",
    "dois": "2",
    "duas": "2",
    "tres": "3",
    "quatro": "4",
    "cinco": "5",
    "seis": "6",
    "sete": "7",
    "oito": "8",
    "nove": "9",
    "dez": "10",
    "quatorze": "14",
    "vinte": "20",
    "trinta": "30",
    "noventa": "90",
}
_UNITS = {
    "dia": "day",
    "dias": "day",
    "hora": "hour",
    "horas": "hour",
    "minuto": "minute",
    "minutos": "minute",
}
_CODE_PATTERN = re.compile(r"\b(?=[A-Z0-9-]*\d)[A-Z]{1,8}-?\d{2,}\b")


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


def _normalized_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )


def _structured_facts(text: str) -> frozenset[tuple[str, ...]]:
    normalized = _normalized_text(text)
    facts: set[tuple[str, ...]] = set()
    number = r"\d+|" + "|".join(_NUMBER_WORDS)
    unit = "|".join(_UNITS)
    for match in re.finditer(rf"\b({number})\s+({unit})\b", normalized):
        raw_number, raw_unit = match.groups()
        facts.add(
            (
                "quantity",
                _NUMBER_WORDS.get(raw_number, raw_number),
                _UNITS[raw_unit],
            )
        )
    for code in _CODE_PATTERN.findall(text.upper()):
        facts.add(("code", code))
    if re.search(
        r"\b(?:proibe|proibido|proibida|veda|vedado|vedada|"
        r"nao permite|nao autoriza)\b",
        normalized,
    ):
        facts.add(("polarity", "deny"))
    elif re.search(
        r"\b(?:permite|autoriza|permitido|permitida|autorizado|autorizada)\b",
        normalized,
    ):
        facts.add(("polarity", "allow"))
    return frozenset(facts)


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


@dataclass(frozen=True, slots=True)
class StructuredFactVerifier:
    """Verify only narrow typed facts and defer unrecognized claims to review."""

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
            claim_facts = _structured_facts(claim.text)
            if not claim_facts:
                return VerificationResult(
                    VerificationDecision.REVIEW,
                    VerificationCode.REVIEW_REQUIRED,
                )
            cited_facts = frozenset(
                fact
                for support in claim.supports
                for citation in support.citations
                for fact in _structured_facts(evidence_by_id[citation.chunk_id])
            )
            if not claim_facts <= cited_facts:
                return VerificationResult(
                    VerificationDecision.REJECT,
                    VerificationCode.CLAIM_SUPPORT_FAILED,
                )
        return VerificationResult(VerificationDecision.RELEASE)
