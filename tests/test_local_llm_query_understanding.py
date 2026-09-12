import asyncio
import json
import unittest
from datetime import date

from medaudit.llm import LLMRequest, LLMResponse, Usage
from medaudit.query_understanding import (
    LocalLLMQueryAnalyzer,
    QueryIntent,
    build_query_analysis_request,
    validate_semantic_response,
)


class FakeClient:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = data
        self.requests: list[LLMRequest] = []

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return response(self.data)


def response(data: dict[str, object]) -> LLMResponse:
    return LLMResponse(
        data=data,
        model="synthetic-model",
        latency_ms=1,
        usage=Usage(input_tokens=1, output_tokens=1),
    )


class LocalLLMQueryAnalyzerTest(unittest.TestCase):
    def test_keeps_deterministic_extraction_and_uses_semantic_routing(self) -> None:
        client = FakeClient(
            {
                "intent": "comparison",
                "requires_external_data": False,
                "requires_decomposition": True,
            }
        )
        analyzer = LocalLLMQueryAnalyzer(client)

        analysis, _ = asyncio.run(
            analyzer.analyze("Contraste o procedimento 12345678 em 12/06/2026.")
        )

        self.assertEqual(analysis.intent, QueryIntent.COMPARISON)
        self.assertEqual(analysis.procedure, "12345678")
        self.assertEqual(analysis.reference_date, date(2026, 6, 12))
        self.assertTrue(analysis.requires_decomposition)
        self.assertEqual(len(client.requests), 1)

    def test_request_contains_no_document_evidence(self) -> None:
        request = build_query_analysis_request("Pergunta sintética")

        self.assertEqual(
            json.loads(request.input_text), {"query": "Pergunta sintética"}
        )
        self.assertEqual(request.temperature, 0.0)
        self.assertEqual(
            set(request.response_schema["required"]),
            {
                "intent",
                "requires_external_data",
                "requires_decomposition",
            },
        )

    def test_rejects_extra_or_invalid_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "unexpected fields"):
            validate_semantic_response(
                response(
                    {
                        "intent": "general",
                        "requires_external_data": False,
                        "requires_decomposition": False,
                        "explanation": "not allowed",
                    }
                )
            )
        with self.assertRaisesRegex(ValueError, "must be boolean"):
            validate_semantic_response(
                response(
                    {
                        "intent": "general",
                        "requires_external_data": "false",
                        "requires_decomposition": False,
                    }
                )
            )
