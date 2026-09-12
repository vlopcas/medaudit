"""Structural signals for multi-part and multi-source queries."""

import re
import unicodedata

_SOURCE = r"(?:documento|fonte|manual|norma|regra|versao)"
_SOURCE_PLURAL = r"(?:documentos|fontes|manuais|normas|regras|versoes)"
_EXPLICIT_SCOPE = re.compile(
    rf"\b(?:ambos|ambas|nos dois|nas duas|em cada {_SOURCE}|de cada {_SOURCE})\b"
)
_REPEATED_SOURCES = re.compile(
    rf"\b{_SOURCE}\b.{{0,50}}\b(?:e|com|entre)\b.{{0,50}}\b{_SOURCE}\b"
)
_LABELED_PAIR = re.compile(
    rf"\b{_SOURCE_PLURAL}\b.{{0,50}}\b"
    r"(?:alfa e beta|beta e alfa|primeiro e segundo|segunda e primeira)\b"
)
_SEPARATE_PARTS = re.compile(r"\b(?:separadamente|respectivamente)\b")


def requires_structural_decomposition(query: str) -> bool:
    """Detect explicit multi-source structure without relying on action verbs."""
    folded = _fold(" ".join(query.split()))
    return any(
        pattern.search(folded)
        for pattern in (
            _EXPLICIT_SCOPE,
            _REPEATED_SOURCES,
            _LABELED_PAIR,
            _SEPARATE_PARTS,
        )
    )


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

