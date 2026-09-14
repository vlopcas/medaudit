"""Deterministic signals for instruction-shaped content inside evidence."""

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from medaudit.rag.models import DecompositionEvidenceBundle


class EvidenceSafetySignal(StrEnum):
    """Auditable reasons to quarantine an evidence passage."""

    ROLE_MARKER = "role_marker"
    INSTRUCTION_OVERRIDE = "instruction_override"
    RESPONSE_SHAPED = "response_shaped"
    CITATION_MANIPULATION = "citation_manipulation"


@dataclass(frozen=True, slots=True)
class EvidenceSafetyFinding:
    """A signal tied to an identifier without retaining private text."""

    evidence_id: str
    signal: EvidenceSafetySignal


@dataclass(frozen=True, slots=True)
class EvidenceSafetyAssessment:
    """Pre-generation decision that can route suspicious evidence to review."""

    findings: tuple[EvidenceSafetyFinding, ...] = ()

    @property
    def can_generate(self) -> bool:
        return not self.findings


_PATTERNS = {
    EvidenceSafetySignal.ROLE_MARKER: re.compile(
        r"(?:\[(?:system|assistant|developer)\]|"
        r"<(?:system|assistant|developer)>|"
        r"(?:^|\n)(?:system|assistant|developer)\s*:)",
        re.IGNORECASE,
    ),
    EvidenceSafetySignal.INSTRUCTION_OVERRIDE: re.compile(
        r"(?:ignore\s+(?:a\s+pergunta|as\s+instrucoes|instrucoes\s+anteriores|"
        r"previous\s+instructions)|retorne\s+insufficient[_ ]evidence|"
        r"return\s+insufficient[_ ]evidence|responda\s+[a-z0-9_-]+|"
        r"output\s+[a-z0-9_-]+)",
        re.IGNORECASE,
    ),
    EvidenceSafetySignal.RESPONSE_SHAPED: re.compile(
        r'\{[^{}]{0,500}"(?:status|claims|answer|text)"\s*:',
        re.IGNORECASE,
    ),
    EvidenceSafetySignal.CITATION_MANIPULATION: re.compile(
        r"(?:cite|citar|use)\s+(?:o\s+)?evidence[_ -]?id\b",
        re.IGNORECASE,
    ),
}


def inspect_evidence_text(text: str) -> tuple[EvidenceSafetySignal, ...]:
    """Return signal codes only; never retain or return the inspected text."""
    decomposed = unicodedata.normalize("NFKD", text)
    normalized = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return tuple(
        signal for signal, pattern in _PATTERNS.items() if pattern.search(normalized)
    )


def assess_decomposed_evidence(
    bundle: DecompositionEvidenceBundle,
) -> EvidenceSafetyAssessment:
    """Inspect every grouped passage before any decomposed generation call."""
    findings = tuple(
        EvidenceSafetyFinding(
            evidence_id=evidence.location.chunk_id,
            signal=signal,
        )
        for group in bundle.groups
        for evidence in group.evidence
        for signal in inspect_evidence_text(evidence.text)
    )
    return EvidenceSafetyAssessment(findings=findings)
