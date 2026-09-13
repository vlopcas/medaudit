"""Evidence-first retrieval-augmented generation boundaries."""

from medaudit.rag.aggregation import group_decomposition_evidence
from medaudit.rag.decomposition import DeterministicDecompositionExecutor
from medaudit.rag.models import (
    DecompositionEvidenceBundle,
    DecompositionExecution,
    DecompositionExecutionStatus,
    Evidence,
    EvidenceLocation,
    ExecutedQueryStep,
    RetrievalDecision,
    RetrievalStatus,
    RoutedRetrievalDecision,
    StepEvidenceGroup,
)
from medaudit.rag.pipeline import (
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    RoutedEvidenceFirstPipeline,
)
from medaudit.rag.prompt import (
    build_decomposed_grounded_request,
    build_grounded_request,
)
from medaudit.rag.validation import (
    ClaimSupport,
    DecomposedGroundedAnswer,
    GroundedAnswer,
    GroundedClaim,
    validate_decomposed_grounded_response,
    validate_grounded_response,
)

__all__ = [
    "ClaimSupport",
    "DecomposedGroundedAnswer",
    "DecompositionEvidenceBundle",
    "DecompositionExecution",
    "DecompositionExecutionStatus",
    "DeterministicDecompositionExecutor",
    "Evidence",
    "EvidenceFirstPipeline",
    "EvidenceLocation",
    "ExecutedQueryStep",
    "FrozenTopScorePolicy",
    "GroundedAnswer",
    "GroundedClaim",
    "RetrievalDecision",
    "RetrievalStatus",
    "RoutedEvidenceFirstPipeline",
    "RoutedRetrievalDecision",
    "StepEvidenceGroup",
    "build_decomposed_grounded_request",
    "build_grounded_request",
    "group_decomposition_evidence",
    "validate_decomposed_grounded_response",
    "validate_grounded_response",
]
