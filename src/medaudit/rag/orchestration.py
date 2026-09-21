"""Opt-in orchestration from a prepared request to a validated answer."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter

from medaudit.llm import LLMClient
from medaudit.rag.pipeline import RoutedCompiledRequestResult
from medaudit.rag.validation import (
    DecomposedGroundedAnswer,
    validate_decomposed_grounded_response,
)
from medaudit.rag.verification import (
    GroundedAnswerVerifier,
    VerificationDecision,
)


class SynthesisMode(StrEnum):
    """Explicit activation state for model invocation."""

    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"


class SynthesisStatus(StrEnum):
    """Content-free outcome of one orchestration attempt."""

    DISABLED = "disabled"
    BLOCKED = "blocked"
    VALIDATED = "validated"
    REJECTED = "rejected"
    HELD = "held"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SynthesisTelemetry:
    """Operational measurements that omit request and response content."""

    mode: SynthesisMode
    status: SynthesisStatus
    failure_code: str | None
    input_tokens: int
    output_tokens: int
    duration_ms: float


@dataclass(frozen=True, slots=True)
class SynthesisResult:
    """Expose only deterministically validated model output."""

    answer: DecomposedGroundedAnswer | None
    telemetry: SynthesisTelemetry

    @property
    def is_validated(self) -> bool:
        return (
            self.telemetry.status is SynthesisStatus.VALIDATED
            and self.answer is not None
        )


class GroundedSynthesisOrchestrator:
    """Invoke an injected client only for prepared, grouped requests."""

    def __init__(
        self,
        *,
        mode: SynthesisMode = SynthesisMode.DISABLED,
        client: LLMClient | None = None,
        verifier: GroundedAnswerVerifier | None = None,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        if mode is SynthesisMode.EXPERIMENTAL and client is None:
            raise ValueError("experimental synthesis requires an LLM client")
        self._mode = mode
        self._client = client
        self._verifier = verifier
        self._clock = clock

    async def synthesize(
        self, routed: RoutedCompiledRequestResult
    ) -> SynthesisResult:
        """Generate only after preparation and release only validated output."""
        started_at = self._clock()
        if self._mode is SynthesisMode.DISABLED:
            return self._result(
                started_at=started_at,
                status=SynthesisStatus.DISABLED,
                failure_code="synthesis_disabled",
            )

        preparation = routed.compiled_request
        bundle = routed.retrieval.evidence_bundle
        if preparation is None or not preparation.is_prepared:
            return self._result(
                started_at=started_at,
                status=SynthesisStatus.BLOCKED,
                failure_code="request_not_prepared",
            )
        if preparation.request is None or bundle is None:
            return self._result(
                started_at=started_at,
                status=SynthesisStatus.REJECTED,
                failure_code="invalid_routed_result",
            )

        assert self._client is not None
        try:
            response = await self._client.generate(preparation.request)
        except (OSError, RuntimeError, TimeoutError, ValueError):
            return self._result(
                started_at=started_at,
                status=SynthesisStatus.FAILED,
                failure_code="client_failed",
            )
        try:
            answer = validate_decomposed_grounded_response(response, bundle)
        except ValueError:
            return self._result(
                started_at=started_at,
                status=SynthesisStatus.REJECTED,
                failure_code="response_rejected",
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
        if self._verifier is not None:
            try:
                verification = self._verifier.verify(answer, bundle)
            except (RuntimeError, TypeError, ValueError):
                return self._result(
                    started_at=started_at,
                    status=SynthesisStatus.FAILED,
                    failure_code="verifier_failed",
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
            if verification.decision is VerificationDecision.REJECT:
                assert verification.code is not None
                return self._result(
                    started_at=started_at,
                    status=SynthesisStatus.REJECTED,
                    failure_code=f"verification_{verification.code.value}",
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
            if verification.decision is VerificationDecision.REVIEW:
                assert verification.code is not None
                return self._result(
                    started_at=started_at,
                    status=SynthesisStatus.HELD,
                    failure_code=f"verification_{verification.code.value}",
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
        return self._result(
            started_at=started_at,
            status=SynthesisStatus.VALIDATED,
            failure_code=None,
            answer=answer,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def _result(
        self,
        *,
        started_at: float,
        status: SynthesisStatus,
        failure_code: str | None,
        answer: DecomposedGroundedAnswer | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> SynthesisResult:
        return SynthesisResult(
            answer=answer,
            telemetry=SynthesisTelemetry(
                mode=self._mode,
                status=status,
                failure_code=failure_code,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=max(0.0, (self._clock() - started_at) * 1_000),
            ),
        )
