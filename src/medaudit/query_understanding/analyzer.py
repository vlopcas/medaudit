"""Deterministic and interpretable query-understanding baseline."""

import re
import unicodedata
from datetime import date

from medaudit.query_understanding.models import QueryAnalysis, QueryIntent

_ISO_DATE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
_BR_DATE = re.compile(r"(?<!\d)(\d{2})/(\d{2})/(\d{4})(?!\d)")
_PROCEDURE_CODE = re.compile(r"(?<!\d)(\d{8})(?!\d)")

_EXTERNAL_SIGNALS = (
    "cotacao atual",
    "dados em tempo real",
    "preco atual",
    "portal externo",
    "sistema externo",
)
_EXTERNAL_SOURCES = ("api", "portal", "sistema externo")
_FRESHNESS_SIGNALS = ("atual", "hoje", "mais recente", "tempo real")
_COMPARISON_SIGNALS = (
    "compare",
    "comparar",
    "comparacao",
    "diferenca entre",
    "mudancas",
    "versus",
)
_AUDIT_SIGNALS = (
    "auditar",
    "auditoria",
    "cobranca",
    "cobertura",
    "glosa",
    "procedimento",
)
_DOCUMENT_SIGNALS = (
    "diretriz",
    "documento",
    "manual",
    "norma",
    "regra",
)
_DECOMPOSITION_SIGNALS = (
    "cruze",
    "e tambem",
    "em ambos",
    "mais de um documento",
    "relacione",
    *_COMPARISON_SIGNALS,
)


class DeterministicQueryAnalyzer:
    """Extract conservative query signals with explicit lexical rules."""

    def analyze(self, query: str) -> QueryAnalysis:
        """Normalize and classify a non-empty query."""
        normalized = " ".join(query.split())
        if not normalized:
            raise ValueError("query cannot be blank")

        folded = _fold(normalized)
        procedure = _first_match(_PROCEDURE_CODE, normalized)
        reference_dates = _extract_dates(normalized)
        requires_external_data = _contains_any(folded, _EXTERNAL_SIGNALS) or (
            _contains_any(folded, _EXTERNAL_SOURCES)
            and _contains_any(folded, _FRESHNESS_SIGNALS)
        )
        requires_decomposition = len(reference_dates) > 1 or _contains_any(
            folded, _DECOMPOSITION_SIGNALS
        )
        intent = _classify_intent(folded, requires_external_data)
        entities = (f"procedure:{procedure}",) if procedure else ()

        return QueryAnalysis(
            original_query=query,
            normalized_query=normalized,
            intent=intent,
            entities=entities,
            reference_date=reference_dates[0] if len(reference_dates) == 1 else None,
            procedure=procedure,
            plan=None,
            requires_external_data=requires_external_data,
            requires_decomposition=requires_decomposition,
        )


def _classify_intent(folded: str, requires_external_data: bool) -> QueryIntent:
    if requires_external_data:
        return QueryIntent.EXTERNAL_LOOKUP
    if _contains_any(folded, _COMPARISON_SIGNALS):
        return QueryIntent.COMPARISON
    if _contains_any(folded, _AUDIT_SIGNALS):
        return QueryIntent.AUDIT_CASE
    if _contains_any(folded, _DOCUMENT_SIGNALS):
        return QueryIntent.DOCUMENT_LOOKUP
    return QueryIntent.GENERAL


def _extract_dates(query: str) -> tuple[date, ...]:
    matches: list[tuple[int, date]] = []
    for match in _ISO_DATE.finditer(query):
        matches.append((match.start(), _build_date(*map(int, match.groups()))))
    for match in _BR_DATE.finditer(query):
        day, month, year = map(int, match.groups())
        matches.append((match.start(), _build_date(year, month, day)))
    return tuple(value for _, value in sorted(matches))


def _build_date(year: int, month: int, day: int) -> date:
    try:
        return date(year, month, day)
    except ValueError as error:
        raise ValueError("query contains an invalid date") from error


def _first_match(pattern: re.Pattern[str], value: str) -> str | None:
    match = pattern.search(value)
    return match.group(1) if match else None


def _contains_any(value: str, signals: tuple[str, ...]) -> bool:
    return any(signal in value for signal in signals)


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
