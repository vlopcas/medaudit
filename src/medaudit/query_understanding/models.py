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


class QueryRoute(StrEnum):
    """Conservative action selected before retrieval."""

    DIRECT_RETRIEVAL = "direct_retrieval"
    REQUIRES_DECOMPOSITION = "requires_decomposition"
    REQUIRES_EXTERNAL_DATA = "requires_external_data"


class QueryPlanStatus(StrEnum):
    """Whether a deterministic decomposition plan is safe to execute."""

    READY = "ready"
    NEEDS_CLARIFICATION = "needs_clarification"


class QueryPlanStrategy(StrEnum):
    """Supported deterministic decomposition strategies."""

    TEMPORAL_SNAPSHOTS = "temporal_snapshots"
    COMPARISON_SCOPES = "comparison_scopes"


@dataclass(frozen=True, slots=True)
class QueryPlanStep:
    """One independently retrievable part of a decomposed query."""

    step_id: str
    query: str
    reference_date: date | None = None
    scope: str | None = None

    def __post_init__(self) -> None:
        if not self.step_id or not self.query.strip():
            raise ValueError("plan step id and query cannot be blank")
        if (self.reference_date is None) == (self.scope is None):
            raise ValueError("plan step requires exactly one temporal date or scope")


@dataclass(frozen=True, slots=True)
class QueryPlan:
    """Conservative result of planning an explicitly decomposable query."""

    original_query: str
    status: QueryPlanStatus
    strategy: QueryPlanStrategy | None
    steps: tuple[QueryPlanStep, ...]

    def __post_init__(self) -> None:
        if not self.original_query.strip():
            raise ValueError("original query cannot be blank")
        if self.status is QueryPlanStatus.READY:
            if self.strategy is None or len(self.steps) < 2:
                raise ValueError(
                    "ready plans require a strategy and at least two steps"
                )
        elif self.strategy is not None or self.steps:
            raise ValueError("clarification plans cannot contain strategy or steps")


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
