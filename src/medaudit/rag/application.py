"""Application composition for routed, guarded synthesis."""

from collections.abc import Collection
from dataclasses import dataclass

from medaudit.rag.orchestration import (
    GroundedSynthesisOrchestrator,
    SynthesisResult,
)
from medaudit.rag.pipeline import (
    RoutedCompiledRequestResult,
    RoutedEvidenceFirstPipeline,
)


@dataclass(frozen=True, slots=True)
class RoutedSynthesisResult:
    """Preserve both the routed trace and guarded synthesis outcome."""

    routed: RoutedCompiledRequestResult
    synthesis: SynthesisResult


class GroundedSynthesisApplication:
    """Compose the pipeline and orchestrator without changing either API."""

    def __init__(
        self,
        pipeline: RoutedEvidenceFirstPipeline,
        *,
        orchestrator: GroundedSynthesisOrchestrator | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._orchestrator = orchestrator or GroundedSynthesisOrchestrator()

    async def execute(
        self,
        query: str,
        *,
        top_k: int = 5,
        reviewed_evidence_ids: Collection[str] = (),
    ) -> RoutedSynthesisResult:
        """Route, prepare and synthesize through the guarded boundaries."""
        routed = self._pipeline.retrieve_with_compiled_request(
            query,
            top_k=top_k,
            reviewed_evidence_ids=reviewed_evidence_ids,
        )
        synthesis = await self._orchestrator.synthesize(routed)
        return RoutedSynthesisResult(routed=routed, synthesis=synthesis)
