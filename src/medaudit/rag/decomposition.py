"""Execute deterministic plans without combining or generating answers."""

from collections.abc import Callable
from datetime import date
from typing import Protocol

from medaudit.query_understanding import (
    QueryPlan,
    QueryPlanStatus,
    QueryPlanStrategy,
)
from medaudit.rag.models import (
    DecompositionExecution,
    DecompositionExecutionStatus,
    ExecutedQueryStep,
    RetrievalDecision,
    RetrievalStatus,
)


class EvidenceRetriever(Protocol):
    """Minimal evidence-pipeline boundary required by step execution."""

    def retrieve(self, query: str, *, top_k: int = 5) -> RetrievalDecision:
        """Retrieve a gated evidence decision for one query."""
        ...


class DeterministicDecompositionExecutor:
    """Execute planned retrievals while preserving temporal and scope isolation."""

    def __init__(
        self,
        *,
        comparison_pipeline: EvidenceRetriever,
        temporal_pipeline_for: Callable[[date], EvidenceRetriever],
    ) -> None:
        self._comparison_pipeline = comparison_pipeline
        self._temporal_pipeline_for = temporal_pipeline_for

    def execute(
        self, plan: QueryPlan, *, top_k: int = 5
    ) -> DecompositionExecution:
        """Execute every ready step or preserve the clarification outcome."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if plan.status is QueryPlanStatus.NEEDS_CLARIFICATION:
            return DecompositionExecution(
                plan=plan,
                status=DecompositionExecutionStatus.NEEDS_CLARIFICATION,
            )

        executed = tuple(
            ExecutedQueryStep(
                step=step,
                retrieval=self._pipeline_for(
                    plan.strategy, step.reference_date
                ).retrieve(step.query, top_k=top_k),
            )
            for step in plan.steps
        )
        status = (
            DecompositionExecutionStatus.READY
            if all(
                item.retrieval.status is RetrievalStatus.READY for item in executed
            )
            else DecompositionExecutionStatus.INSUFFICIENT_EVIDENCE
        )
        return DecompositionExecution(plan=plan, status=status, steps=executed)

    def _pipeline_for(
        self,
        strategy: QueryPlanStrategy | None,
        reference_date: date | None,
    ) -> EvidenceRetriever:
        if strategy is QueryPlanStrategy.COMPARISON_SCOPES:
            return self._comparison_pipeline
        if strategy is QueryPlanStrategy.TEMPORAL_SNAPSHOTS:
            if reference_date is None:
                raise ValueError("temporal plan step requires a reference date")
            return self._temporal_pipeline_for(reference_date)
        raise ValueError("ready query plan has no supported strategy")
