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
from medaudit.rag.prompt import build_grounded_request
from medaudit.rag.validation import GroundedAnswer, validate_grounded_response

__all__ = [
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
    "RetrievalDecision",
    "RetrievalStatus",
    "RoutedEvidenceFirstPipeline",
    "RoutedRetrievalDecision",
    "StepEvidenceGroup",
    "build_grounded_request",
    "group_decomposition_evidence",
    "validate_grounded_response",
]
