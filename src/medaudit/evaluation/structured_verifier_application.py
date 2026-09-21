"""Evaluate opt-in structured verification through the synthesis application."""

import argparse
import asyncio
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.evaluation.query_understanding import verify_input
from medaudit.llm import LLMRequest, LLMResponse, Usage
from medaudit.rag import (
    CompiledContextGateway,
    CompiledRequestMode,
    DecomposedGroundedAnswer,
    DecompositionEvidenceBundle,
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    GroundedSynthesisApplication,
    GroundedSynthesisOrchestrator,
    RoutedEvidenceFirstPipeline,
    StructuredFactVerifier,
    SynthesisMode,
    VerificationResult,
)
from medaudit.retrieval import BM25Index

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "structured-verifier-application-development-v1"
_HOLDOUT_POLICY = "structured-verifier-application-holdout-v1"


class SyntheticClient:
    """Return one deterministic, structurally valid synthetic response."""

    def __init__(self, behavior: str) -> None:
        self.behavior = behavior
        self.call_count = 0

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            data=_response_data(self.behavior),
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=12, output_tokens=7),
        )


class RecordingStructuredVerifier:
    """Record use while delegating every decision to the real verifier."""

    def __init__(self) -> None:
        self._delegate = StructuredFactVerifier()
        self.call_count = 0

    def verify(
        self,
        answer: DecomposedGroundedAnswer,
        evidence: DecompositionEvidenceBundle,
    ) -> VerificationResult:
        self.call_count += 1
        return self._delegate.verify(answer, evidence)


def load_dataset(
    path: Path, *, expected_policy: str = _POLICY
) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != expected_policy
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported structured verifier application schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("structured verifier application cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("case ids must be present and unique")
    return cases


async def evaluate(
    cases: list[dict[str, Any]], *, policy: str = _POLICY
) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in cases:
        client = SyntheticClient(case["client_behavior"])
        verifier = RecordingStructuredVerifier() if case["verifier_enabled"] else None
        application = GroundedSynthesisApplication(
            _pipeline(),
            orchestrator=GroundedSynthesisOrchestrator(
                mode=SynthesisMode.EXPERIMENTAL,
                client=client,
                verifier=verifier,
                clock=lambda: 1.0,
            ),
        )
        result = await application.execute(
            "Compare regra alfa com regra beta.", top_k=1
        )
        actual = {
            "status": result.synthesis.telemetry.status.value,
            "failure_code": result.synthesis.telemetry.failure_code,
            "client_called": client.call_count == 1,
            "verifier_called": verifier is not None and verifier.call_count == 1,
            "answer_present": result.synthesis.answer is not None,
        }
        correct = actual == case["expected"]
        category = str(case["category"])
        category_counts[category] += 1
        category_correct[category] += correct
        outcomes.append(
            {"case_id": case["id"], "category": category, "correct": correct, **actual}
        )
    return {
        "schema_version": 1,
        "policy": policy,
        "case_count": len(cases),
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


def _pipeline() -> RoutedEvidenceFirstPipeline:
    chunks = [
        Chunk(
            "chunk-alpha",
            "document-alpha",
            "A regra alfa, código AX-204, permite renovação por dez dias.",
        ),
        Chunk(
            "chunk-beta",
            "document-beta",
            "A regra beta, código BQ-510, proíbe renovação por vinte dias.",
        ),
    ]
    evidence_pipeline = EvidenceFirstPipeline(
        chunks=chunks,
        retriever=BM25Index(chunks),
        policy=FrozenTopScorePolicy(threshold=0.1),
    )
    executor = DeterministicDecompositionExecutor(
        comparison_pipeline=evidence_pipeline,
        temporal_pipeline_for=lambda _: evidence_pipeline,
    )
    return RoutedEvidenceFirstPipeline(
        evidence_pipeline,
        decomposition_executor=executor,
        compiled_context_gateway=CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            token_budget=1_000,
            clock=lambda: 1.0,
        ),
    )


def _response_data(behavior: str) -> dict[str, Any]:
    if behavior == "abstention":
        return {"status": "insufficient_evidence", "claims": []}
    claims = {
        "safe": (
            "A regra AX-204 autoriza renovação por 10 dias.",
            "A regra BQ-510 veda renovação por 20 dias.",
        ),
        "quantity_contradiction": (
            "A regra AX-204 autoriza renovação por 90 dias.",
            "A regra BQ-510 veda renovação por 20 dias.",
        ),
        "code_contradiction": (
            "A regra AX-209 autoriza renovação por 10 dias.",
            "A regra BQ-510 veda renovação por 20 dias.",
        ),
        "polarity_contradiction": (
            "A regra AX-204 proíbe renovação por 10 dias.",
            "A regra BQ-510 veda renovação por 20 dias.",
        ),
        "safe_reordered": (
            "Por 10 dias, a renovação é autorizada pela regra AX-204.",
            "Por 20 dias, a renovação é vedada pela regra BQ-510.",
        ),
        "unit_contradiction": (
            "A regra AX-204 autoriza renovação por 10 horas.",
            "A regra BQ-510 veda renovação por 20 dias.",
        ),
        "partial_unstructured": (
            "A regra AX-204 autoriza renovação por 10 dias.",
            "A regra beta possui prioridade comum.",
        ),
        "unstructured": (
            "A regra alfa possui prioridade especial.",
            "A regra beta possui prioridade comum.",
        ),
    }.get(behavior)
    if claims is None:
        raise ValueError("unsupported synthetic client behavior")
    return {
        "status": "answered",
        "claims": [
            {
                "text": claims[0],
                "supports": [
                    {"step_id": "comparison-1", "evidence_ids": ["chunk-alpha"]}
                ],
            },
            {
                "text": claims[1],
                "supports": [
                    {"step_id": "comparison-2", "evidence_ids": ["chunk-beta"]}
                ],
            },
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--dataset-policy",
        choices=(_POLICY, _HOLDOUT_POLICY),
        default=_POLICY,
    )
    parser.add_argument("--expected-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--refuse-overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.output and args.refuse_overwrite and args.output.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {args.output}")
    report = asyncio.run(
        evaluate(
            load_dataset(args.dataset, expected_policy=args.dataset_policy),
            policy=args.dataset_policy,
        )
    )
    report["input_sha256"] = verify_input(args.dataset, args.expected_sha256)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
