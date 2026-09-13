"""Deterministically group decomposed evidence without synthesizing it."""

from medaudit.rag.models import (
    DecompositionEvidenceBundle,
    DecompositionExecution,
    StepEvidenceGroup,
)


def group_decomposition_evidence(
    execution: DecompositionExecution,
) -> DecompositionEvidenceBundle:
    """Preserve step order, context and citations in an inspectable bundle."""
    return DecompositionEvidenceBundle(
        execution=execution,
        groups=tuple(
            StepEvidenceGroup(
                step=executed.step,
                evidence=executed.retrieval.evidence,
            )
            for executed in execution.steps
        ),
    )
