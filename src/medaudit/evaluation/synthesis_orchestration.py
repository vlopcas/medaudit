"""Evaluate opt-in synthesis orchestration with synthetic fake clients."""

import argparse
import asyncio
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.evaluation.context_compilation import WordTokenEstimator
from medaudit.evaluation.query_understanding import verify_input
from medaudit.llm import LLMRequest, LLMResponse, Usage
from medaudit.rag import (
    CompiledContextGateway,
    CompiledRequestMode,
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    GroundedSynthesisOrchestrator,
    RoutedEvidenceFirstPipeline,
    SynthesisMode,
)
from medaudit.retrieval import BM25Index

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "synthesis-orchestration-development-v1"


class SyntheticClient:
    """Return one deterministic response or a synthetic operational error."""

    def __init__(self, behavior: str) -> None:
        self.behavior = behavior
        self.call_count = 0

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        if self.behavior == "failure":
            raise RuntimeError("synthetic client failure")
        data = _response_data(self.behavior)
        return LLMResponse(
            data=data,
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=12, output_tokens=7),
        )


def load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported synthesis orchestration dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("synthesis orchestration cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("synthesis orchestration ids must be present and unique")
    return cases


async def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not cases:
        raise ValueError("synthesis orchestration cases are required")
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in cases:
        client = SyntheticClient(case.get("client_behavior", "valid"))
        routed = _pipeline(case).retrieve_with_compiled_request(
            case["query"], top_k=1
        )
        result = await GroundedSynthesisOrchestrator(
            mode=SynthesisMode(case.get("synthesis_mode", "disabled")),
            client=(client if case.get("synthesis_mode") == "experimental" else None),
            clock=lambda: 1.0,
        ).synthesize(routed)
        actual = {
            "status": result.telemetry.status.value,
            "failure_code": result.telemetry.failure_code,
            "client_called": client.call_count == 1,
            "answer_present": result.answer is not None,
            "answer_status": result.answer.status if result.answer else None,
            "claim_count": len(result.answer.claims) if result.answer else 0,
        }
        correct = actual == case["expected"]
        category = case["category"]
        category_counts[category] += 1
        category_correct[category] += correct
        outcomes.append(
            {
                "case_id": case["id"],
                "category": category,
                "correct": correct,
                **actual,
            }
        )
    return {
        "schema_version": 1,
        "policy": _POLICY,
        "case_count": len(outcomes),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes) / len(outcomes),
            "release_safety": sum(
                item["answer_present"] == (item["status"] == "validated")
                for item in outcomes
            )
            / len(outcomes),
            "exact_match_by_category": {
                category: category_correct[category] / count
                for category, count in sorted(category_counts.items())
            },
        },
        "cases": outcomes,
    }


def _pipeline(case: dict[str, Any]) -> RoutedEvidenceFirstPipeline:
    chunks = [
        Chunk("chunk-alpha", "document-alpha", "regra alfa sintética"),
        Chunk("chunk-beta", "document-beta", "regra beta sintética"),
    ]
    evidence_pipeline = EvidenceFirstPipeline(
        chunks=chunks,
        retriever=BM25Index(chunks),
        policy=FrozenTopScorePolicy(threshold=0.1),
    )
    executor = (
        DeterministicDecompositionExecutor(
            comparison_pipeline=evidence_pipeline,
            temporal_pipeline_for=lambda _: evidence_pipeline,
        )
        if case.get("executor", False)
        else None
    )
    gateway = CompiledContextGateway(
        mode=CompiledRequestMode(case.get("gateway_mode", "disabled")),
        token_budget=100,
        estimator=WordTokenEstimator(),
        clock=lambda: 1.0,
    )
    return RoutedEvidenceFirstPipeline(
        evidence_pipeline,
        decomposition_executor=executor,
        compiled_context_gateway=gateway,
    )


def _response_data(behavior: str) -> dict[str, Any]:
    if behavior == "abstention":
        return {"status": "insufficient_evidence", "claims": []}
    if behavior == "cross_group":
        return {
            "status": "answered",
            "claims": [
                {
                    "text": "Afirmação sintética inválida.",
                    "supports": [
                        {
                            "step_id": "comparison-1",
                            "evidence_ids": ["chunk-beta"],
                        }
                    ],
                }
            ],
        }
    if behavior != "valid":
        raise ValueError("unsupported synthetic client behavior")
    return {
        "status": "answered",
        "claims": [
            {
                "text": "A regra alfa possui suporte sintético.",
                "supports": [
                    {
                        "step_id": "comparison-1",
                        "evidence_ids": ["chunk-alpha"],
                    }
                ],
            },
            {
                "text": "A regra beta possui suporte sintético.",
                "supports": [
                    {
                        "step_id": "comparison-2",
                        "evidence_ids": ["chunk-beta"],
                    }
                ],
            },
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    report = asyncio.run(evaluate(load_dataset(args.dataset)))
    report["input_sha256"] = verify_input(args.dataset, args.expected_sha256)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
