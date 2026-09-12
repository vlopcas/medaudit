import asyncio
import json
import unittest
from collections.abc import Mapping
from typing import Any

from medaudit.llm import LlamaCppClient, LLMRequest
from medaudit.llm.local_http import MODEL_FILE, MODEL_ID, MODEL_REVISION


class FakeTransport:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any], float]] = []

    async def post(
        self, url: str, payload: dict[str, Any], *, timeout_seconds: float
    ) -> tuple[dict[str, Any], Mapping[str, str]]:
        self.calls.append((url, payload, timeout_seconds))
        return self.response, {"Server": "synthetic-llama.cpp"}


def request() -> LLMRequest:
    return LLMRequest(
        instruction="Use only synthetic evidence.",
        input_text='{"question":"synthetic"}',
        response_schema={"type": "object"},
    )


class LlamaCppClientTest(unittest.TestCase):
    def test_model_artifact_is_pinned(self) -> None:
        self.assertEqual(MODEL_ID, "Qwen/Qwen3-4B-GGUF")
        self.assertEqual(MODEL_FILE, "Qwen3-4B-Q4_K_M.gguf")
        self.assertRegex(MODEL_REVISION, r"^[0-9a-f]{40}$")

    def test_rejects_remote_or_encrypted_endpoint(self) -> None:
        for endpoint in ("https://localhost:8080", "http://example.com:8080"):
            with self.subTest(endpoint=endpoint):
                with self.assertRaisesRegex(ValueError, "loopback"):
                    LlamaCppClient(base_url=endpoint)

    def test_sends_json_schema_and_parses_response(self) -> None:
        transport = FakeTransport(
            {
                "id": "synthetic-request",
                "model": MODEL_FILE,
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "status": "answered",
                                    "answer": "Synthetic answer.",
                                    "evidence_ids": ["synthetic-chunk"],
                                }
                            )
                        }
                    }
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 8},
            }
        )
        client = LlamaCppClient(transport=transport)

        response = asyncio.run(client.generate(request()))

        url, payload, timeout = transport.calls[0]
        self.assertEqual(url, "http://127.0.0.1:8080/v1/chat/completions")
        self.assertEqual(payload["response_format"]["type"], "json_schema")
        self.assertFalse(payload["stream"])
        self.assertEqual(timeout, 120)
        self.assertEqual(response.data["status"], "answered")
        self.assertEqual(response.usage.input_tokens, 12)
        self.assertEqual(response.metadata["backend"], "llama.cpp")

    def test_rejects_non_json_model_content(self) -> None:
        transport = FakeTransport(
            {"choices": [{"message": {"content": "not json"}}]}
        )
        client = LlamaCppClient(transport=transport)

        with self.assertRaisesRegex(ValueError, "invalid structured response"):
            asyncio.run(client.generate(request()))
