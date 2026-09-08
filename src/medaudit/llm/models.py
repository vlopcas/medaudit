"""Provider-neutral LLM request and response models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """A structured request sent through an LLM adapter."""

    instruction: str
    input_text: str
    response_schema: dict[str, Any]
    temperature: float = 0.0


@dataclass(frozen=True, slots=True)
class Usage:
    """Provider-reported token consumption."""

    input_tokens: int
    output_tokens: int


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Validated structured data and operational metadata."""

    data: dict[str, Any]
    model: str
    latency_ms: float
    usage: Usage
    request_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

