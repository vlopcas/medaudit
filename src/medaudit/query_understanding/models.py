"""Typed output of deterministic query understanding."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class QueryIntent(StrEnum):
    """Small intent taxonomy used before retrieval."""

    AUDIT_CASE = "audit_case"
    COMPARISON = "comparison"
    DOCUMENT_LOOKUP = "document_lookup"
    EXTERNAL_LOOKUP = "external_lookup"
    GENERAL = "general"


@dataclass(frozen=True, slots=True)
class QueryAnalysis:
    """Interpretable signals extracted without calling an LLM."""

    original_query: str
    normalized_query: str
    intent: QueryIntent
    entities: tuple[str, ...]
    reference_date: date | None
    procedure: str | None
    plan: str | None
    requires_external_data: bool
    requires_decomposition: bool

