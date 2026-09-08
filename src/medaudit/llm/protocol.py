"""Contract implemented by concrete LLM providers."""

from typing import Protocol

from medaudit.llm.models import LLMRequest, LLMResponse


class LLMClient(Protocol):
    """Minimal async interface for structured LLM calls."""

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return a validated structured response or raise an adapter error."""
        ...

