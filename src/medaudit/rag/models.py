"""Models for gated retrieval and traceable evidence."""

from dataclasses import dataclass
from enum import StrEnum

from medaudit.query_understanding import (
    QueryPlan,
    QueryPlanStatus,
    QueryPlanStep,
    QueryRoute,
)
from medaudit.retrieval import ConfidenceSignals


class RetrievalStatus(StrEnum):
    """Outcome decided before any generative model is called."""

    READY = "ready"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class DecompositionExecutionStatus(StrEnum):
    """Aggregate outcome of executing a deterministic query plan."""

    READY = "ready"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NEEDS_CLARIFICATION = "needs_clarification"


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


@dataclass(frozen=True, slots=True)
class ExecutedQueryStep:
    """A planned step paired with its independent retrieval decision."""

    step: QueryPlanStep
    retrieval: RetrievalDecision


@dataclass(frozen=True, slots=True)
class DecompositionExecution:
    """Non-generative execution result that preserves step boundaries."""

    plan: QueryPlan
    status: DecompositionExecutionStatus
    steps: tuple[ExecutedQueryStep, ...] = ()

    def __post_init__(self) -> None:
        is_clarification = (
            self.status is DecompositionExecutionStatus.NEEDS_CLARIFICATION
        )
        plan_needs_clarification = (
            self.plan.status is QueryPlanStatus.NEEDS_CLARIFICATION
        )
        if is_clarification != plan_needs_clarification:
            raise ValueError("execution and plan clarification status must agree")
        if is_clarification != (not self.steps):
            raise ValueError("only clarification executions can omit step results")
        if self.steps and len(self.steps) != len(self.plan.steps):
            raise ValueError("every planned step must have one retrieval result")
        if self.steps:
            all_ready = all(
                item.retrieval.status is RetrievalStatus.READY
                for item in self.steps
            )
            if (
                self.status is DecompositionExecutionStatus.READY
            ) != all_ready:
                raise ValueError("aggregate status must reflect every step result")


@dataclass(frozen=True, slots=True)
class RoutedRetrievalDecision:
    """Pre-retrieval route paired with evidence or a non-executed plan."""

    query: str
    route: QueryRoute
    retrieval: RetrievalDecision | None = None
    plan: QueryPlan | None = None
    execution: DecompositionExecution | None = None

    def __post_init__(self) -> None:
        has_retrieval = self.retrieval is not None
        if (self.route is QueryRoute.DIRECT_RETRIEVAL) != has_retrieval:
            raise ValueError("only direct retrieval routes can contain evidence")
        has_plan = self.plan is not None
        if (self.route is QueryRoute.REQUIRES_DECOMPOSITION) != has_plan:
            raise ValueError("only decomposition routes require a query plan")
        if self.execution is not None:
            if self.route is not QueryRoute.REQUIRES_DECOMPOSITION:
                raise ValueError("only decomposition routes can contain execution")
            if self.execution.plan != self.plan:
                raise ValueError(
                    "decomposition execution must belong to the route plan"
                )
