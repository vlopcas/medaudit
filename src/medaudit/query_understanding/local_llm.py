"""Hybrid query analysis with deterministic extraction and local semantics."""

import json
from dataclasses import replace
from typing import Any

from medaudit.llm import LLMClient, LLMRequest, LLMResponse
from medaudit.query_understanding.analyzer import DeterministicQueryAnalyzer
from medaudit.query_understanding.models import QueryAnalysis, QueryIntent

_REQUIRED_FIELDS = {
    "intent",
    "requires_external_data",
    "requires_decomposition",
}


class LocalLLMQueryAnalyzer:
    """Use a local LLM only for semantic routing fields."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client
        self._deterministic = DeterministicQueryAnalyzer()

    async def analyze(self, query: str) -> tuple[QueryAnalysis, LLMResponse]:
        """Combine deterministic entities with validated semantic signals."""
        baseline = self._deterministic.analyze(query)
        response = await self._client.generate(build_query_analysis_request(query))
        semantic = validate_semantic_response(response)
        return (
            replace(
                baseline,
                intent=semantic["intent"],
                requires_external_data=semantic["requires_external_data"],
                requires_decomposition=semantic["requires_decomposition"],
            ),
            response,
        )


def build_query_analysis_request(query: str) -> LLMRequest:
    """Build a constrained request that contains only the user query."""
    return LLMRequest(
        instruction=(
            "/no_think\n"
            "Classify the Portuguese query for routing. Return exactly one JSON "
            "object. intent meanings: audit_case for coverage, billing, denial "
            "or procedure auditing; comparison for differences or changes "
            "between sources or versions; document_lookup for questions answered "
            "from rules, manuals or documents; external_lookup only when current "
            "information must be obtained from a portal, system, API or live "
            "source; general otherwise. requires_external_data is true only when "
            "the local document corpus is insufficient because a live source is "
            "required. requires_decomposition is true when answering requires "
            "separate retrieval for multiple sources, versions, dates or explicit "
            "subquestions. Do not answer the query and do not add explanations."
        ),
        input_text=json.dumps({"query": query}, ensure_ascii=False),
        response_schema={
            "type": "object",
            "additionalProperties": False,
            "required": sorted(_REQUIRED_FIELDS),
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": [intent.value for intent in QueryIntent],
                },
                "requires_external_data": {"type": "boolean"},
                "requires_decomposition": {"type": "boolean"},
            },
        },
    )


def validate_semantic_response(response: LLMResponse) -> dict[str, Any]:
    """Reject missing, extra or incorrectly typed routing fields."""
    if set(response.data) != _REQUIRED_FIELDS:
        raise ValueError("query analysis response has unexpected fields")
    try:
        intent = QueryIntent(response.data["intent"])
    except (TypeError, ValueError) as error:
        raise ValueError("query analysis response has invalid intent") from error
    external = response.data["requires_external_data"]
    decomposition = response.data["requires_decomposition"]
    if not isinstance(external, bool) or not isinstance(decomposition, bool):
        raise ValueError("query analysis routing signals must be boolean")
    return {
        "intent": intent,
        "requires_external_data": external,
        "requires_decomposition": decomposition,
    }

