"""Opt-in boundary from grouped evidence to a sealed model request."""

from collections.abc import Callable, Collection
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter

from medaudit.llm import LLMRequest
from medaudit.rag.context import (
    ContextStatus,
    TokenEstimator,
    compile_decomposed_context,
)
from medaudit.rag.models import DecompositionEvidenceBundle
from medaudit.rag.prompt import (
    ANSWER_WHEN_SUPPORTED_INSTRUCTION,
    DECOMPOSED_GROUNDED_INSTRUCTION,
    build_compiled_decomposed_grounded_request,
)


class CompiledRequestMode(StrEnum):
    """Explicit activation state for the experimental integration."""

    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"


class CompiledInstructionPolicy(StrEnum):
    """Explicit trusted instruction selected before context compilation."""

    BASELINE = "baseline"
    ANSWER_WHEN_SUPPORTED_V1 = "answer-when-supported-v1"


class CompiledSchemaPolicy(StrEnum):
    """Explicit structured-output limits selected by the gateway."""

    BASELINE = "baseline"
    BOUNDED_V1 = "bounded-v1"


class CompiledRequestStatus(StrEnum):
    """Safe outcome codes that do not expose query or evidence content."""

    DISABLED = "disabled"
    PREPARED = "prepared"
    BLOCKED = "blocked"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class CompiledRequestTelemetry:
    """Content-free measurements for one request-preparation attempt."""

    mode: CompiledRequestMode
    status: CompiledRequestStatus
    context_status: ContextStatus | None
    failure_code: str | None
    item_count: int
    group_count: int
    exclusion_count: int
    estimated_tokens: int
    token_budget: int
    duration_ms: float


@dataclass(frozen=True, slots=True)
class CompiledRequestResult:
    """A request is present only after compilation and rendering both pass."""

    request: LLMRequest | None
    telemetry: CompiledRequestTelemetry

    @property
    def is_prepared(self) -> bool:
        return (
            self.telemetry.status is CompiledRequestStatus.PREPARED
            and self.request is not None
        )


class CompiledContextGateway:
    """Prepare sealed requests only when explicitly enabled."""

    def __init__(
        self,
        *,
        mode: CompiledRequestMode = CompiledRequestMode.DISABLED,
        instruction_policy: CompiledInstructionPolicy = (
            CompiledInstructionPolicy.BASELINE
        ),
        schema_policy: CompiledSchemaPolicy = CompiledSchemaPolicy.BASELINE,
        token_budget: int = 8_192,
        estimator: TokenEstimator | None = None,
        clock: Callable[[], float] = perf_counter,
    ) -> None:
        if token_budget <= 0:
            raise ValueError("compiled request token budget must be positive")
        self._mode = mode
        self._instruction_policy = instruction_policy
        self._schema_policy = schema_policy
        self._token_budget = token_budget
        self._estimator = estimator
        self._clock = clock

    def prepare(
        self,
        bundle: DecompositionEvidenceBundle,
        *,
        reviewed_evidence_ids: Collection[str] = (),
    ) -> CompiledRequestResult:
        """Compile and render without invoking a model or logging content."""
        started_at = self._clock()
        if self._mode is CompiledRequestMode.DISABLED:
            return self._result(
                started_at=started_at,
                status=CompiledRequestStatus.DISABLED,
                context_status=None,
                failure_code="integration_disabled",
            )

        try:
            context = compile_decomposed_context(
                bundle,
                instruction=self._instruction(),
                token_budget=self._token_budget,
                estimator=self._estimator,
                review_evidence_ids=frozenset(reviewed_evidence_ids),
            )
        except ValueError:
            return self._result(
                started_at=started_at,
                status=CompiledRequestStatus.REJECTED,
                context_status=None,
                failure_code="compiler_rejected_input",
            )
        if not context.can_generate:
            return self._result(
                started_at=started_at,
                status=CompiledRequestStatus.BLOCKED,
                context_status=context.status,
                failure_code=f"context_{context.status.value}",
                item_count=len(context.items),
                group_count=len(context.groups),
                exclusion_count=len(context.exclusions),
                estimated_tokens=context.estimated_tokens,
            )
        try:
            request = build_compiled_decomposed_grounded_request(
                context,
                bounded_schema=(
                    self._schema_policy is CompiledSchemaPolicy.BOUNDED_V1
                ),
            )
        except ValueError:
            return self._result(
                started_at=started_at,
                status=CompiledRequestStatus.REJECTED,
                context_status=context.status,
                failure_code="renderer_rejected_context",
                item_count=len(context.items),
                group_count=len(context.groups),
                exclusion_count=len(context.exclusions),
                estimated_tokens=context.estimated_tokens,
            )
        return self._result(
            started_at=started_at,
            status=CompiledRequestStatus.PREPARED,
            context_status=context.status,
            failure_code=None,
            request=request,
            item_count=len(context.items),
            group_count=len(context.groups),
            exclusion_count=len(context.exclusions),
            estimated_tokens=context.estimated_tokens,
        )

    def _instruction(self) -> str:
        if (
            self._instruction_policy
            is CompiledInstructionPolicy.ANSWER_WHEN_SUPPORTED_V1
        ):
            return ANSWER_WHEN_SUPPORTED_INSTRUCTION
        return DECOMPOSED_GROUNDED_INSTRUCTION

    def _result(
        self,
        *,
        started_at: float,
        status: CompiledRequestStatus,
        context_status: ContextStatus | None,
        failure_code: str | None,
        request: LLMRequest | None = None,
        item_count: int = 0,
        group_count: int = 0,
        exclusion_count: int = 0,
        estimated_tokens: int = 0,
    ) -> CompiledRequestResult:
        duration_ms = max(0.0, (self._clock() - started_at) * 1_000)
        return CompiledRequestResult(
            request=request,
            telemetry=CompiledRequestTelemetry(
                mode=self._mode,
                status=status,
                context_status=context_status,
                failure_code=failure_code,
                item_count=item_count,
                group_count=group_count,
                exclusion_count=exclusion_count,
                estimated_tokens=estimated_tokens,
                token_budget=self._token_budget,
                duration_ms=duration_ms,
            ),
        )
