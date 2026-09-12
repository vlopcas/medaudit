"""Loopback-only adapter for a local llama.cpp chat completion server."""

import asyncio
import json
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse

from medaudit.llm.models import LLMRequest, LLMResponse, Usage

MODEL_ID = "Qwen/Qwen3-4B-GGUF"
MODEL_REVISION = "3b6d9922d71c6d316a0c9de39a95fbe8594b9a0b"
MODEL_FILE = "Qwen3-4B-Q4_K_M.gguf"


class JSONTransport(Protocol):
    """Injectable JSON transport used to keep the adapter testable."""

    async def post(
        self, url: str, payload: dict[str, Any], *, timeout_seconds: float
    ) -> tuple[dict[str, Any], Mapping[str, str]]: ...


class LoopbackHTTPTransport:
    """Minimal standard-library HTTP transport for a local inference server."""

    async def post(
        self, url: str, payload: dict[str, Any], *, timeout_seconds: float
    ) -> tuple[dict[str, Any], Mapping[str, str]]:
        return await asyncio.to_thread(
            self._post_sync, url, payload, timeout_seconds=timeout_seconds
        )

    @staticmethod
    def _post_sync(
        url: str, payload: dict[str, Any], *, timeout_seconds: float
    ) -> tuple[dict[str, Any], Mapping[str, str]]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body = json.loads(response.read().decode())
                return body, dict(response.headers.items())
        except urllib.error.URLError as error:
            raise RuntimeError("local inference server request failed") from error


@dataclass(frozen=True, slots=True)
class LlamaCppClient:
    """Structured chat client that refuses non-local inference endpoints."""

    base_url: str = "http://127.0.0.1:8080"
    model: str = MODEL_FILE
    timeout_seconds: float = 120.0
    transport: JSONTransport = field(default_factory=LoopbackHTTPTransport)

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.scheme != "http" or parsed.hostname not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ValueError("local LLM endpoint must use loopback HTTP")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("local LLM endpoint cannot contain credentials or extras")
        if self.timeout_seconds <= 0:
            raise ValueError("LLM timeout must be positive")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate constrained JSON without logging prompt or response content."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.instruction},
                {"role": "user", "content": request.input_text},
            ],
            "temperature": request.temperature,
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "grounded_answer",
                    "strict": True,
                    "schema": request.response_schema,
                },
            },
        }
        started = time.perf_counter()
        response, headers = await self.transport.post(
            f"{self.base_url.rstrip('/')}/v1/chat/completions",
            payload,
            timeout_seconds=self.timeout_seconds,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        try:
            content = response["choices"][0]["message"]["content"]
            data = json.loads(content)
            usage = response.get("usage", {})
            input_tokens = int(usage.get("prompt_tokens", 0))
            output_tokens = int(usage.get("completion_tokens", 0))
        except (
            IndexError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise ValueError(
                "local LLM returned an invalid structured response"
            ) from error
        if not isinstance(data, dict):
            raise ValueError("local LLM structured response must be an object")
        request_id = response.get("id")
        return LLMResponse(
            data=data,
            model=str(response.get("model", self.model)),
            latency_ms=latency_ms,
            usage=Usage(input_tokens=input_tokens, output_tokens=output_tokens),
            request_id=request_id if isinstance(request_id, str) else None,
            metadata={
                "backend": "llama.cpp",
                "server": headers.get("Server", "local"),
            },
        )
