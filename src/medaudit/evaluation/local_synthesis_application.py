"""Benchmark the full synthesis application with a local model and synthetic data."""

import argparse
import asyncio
import hashlib
import json
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.evaluation.content_grade import grade_expected_content
from medaudit.evaluation.context_compilation import WordTokenEstimator
from medaudit.evaluation.local_llm_benchmark import verify_input, wait_until_ready
from medaudit.evaluation.private_bm25 import write_private_report
from medaudit.llm import LlamaCppClient, LLMClient, LLMRequest, LLMResponse
from medaudit.rag import (
    CompiledContextGateway,
    CompiledRequestMode,
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    GroundedSynthesisApplication,
    GroundedSynthesisOrchestrator,
    RoutedEvidenceFirstPipeline,
    SynthesisMode,
)
from medaudit.retrieval import BM25Index

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "local-synthesis-application-development-v1"


class CountingClient:
    """Count invocations while leaving request and response content unobserved."""

    def __init__(self, client: LLMClient) -> None:
        self._client = client
        self.call_count = 0

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        return await self._client.generate(request)


def load_dataset(path: Path) -> list[dict[str, Any]]:
    """Load the explicit, wholly synthetic application benchmark schema."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported local synthesis application schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("local synthesis application cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("case ids must be present and unique")
    for case in cases:
        chunks = case.get("chunks")
        expected = case.get("expected")
        if not isinstance(chunks, list) or len(chunks) < 2:
            raise ValueError("each case requires at least two synthetic chunks")
        if not isinstance(expected, dict) or expected.get("status") not in {
            "answered",
            "insufficient_evidence",
        }:
            raise ValueError("each case requires a supported expected status")
        if expected["status"] == "answered":
            grade_expected_content("validation placeholder", expected)
    return cases


def _application(
    case: dict[str, Any], client: LLMClient
) -> GroundedSynthesisApplication:
    chunks = [
        Chunk(item["chunk_id"], item["document_id"], item["text"])
        for item in case["chunks"]
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
    pipeline = RoutedEvidenceFirstPipeline(
        evidence_pipeline,
        decomposition_executor=executor,
        compiled_context_gateway=CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            token_budget=10_000,
            estimator=WordTokenEstimator(),
        ),
    )
    return GroundedSynthesisApplication(
        pipeline,
        orchestrator=GroundedSynthesisOrchestrator(
            mode=SynthesisMode.EXPERIMENTAL,
            client=client,
        ),
    )


def _answer_fingerprint(answer: Any) -> str:
    payload = {
        "status": answer.status,
        "claims": [
            {
                "text": claim.text,
                "supports": [
                    {
                        "step_id": support.step_id,
                        "evidence_ids": [
                            citation.chunk_id for citation in support.citations
                        ],
                    }
                    for support in claim.supports
                ],
            }
            for claim in answer.claims
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


async def run_benchmark(
    cases: list[dict[str, Any]],
    *,
    client: LLMClient,
    repetitions: int = 1,
) -> dict[str, Any]:
    """Measure the sealed application path without retaining generated text."""
    if repetitions < 1:
        raise ValueError("benchmark repetitions must be positive")
    attempts = len(cases) * repetitions
    answerable_attempts = (
        sum(case["expected"]["status"] == "answered" for case in cases)
        * repetitions
    )
    prepared = invoked = validated = status_correct = content_correct = 0
    matched_concepts = expected_concepts = 0
    input_tokens = output_tokens = 0
    latencies: list[float] = []
    outcomes: list[dict[str, Any]] = []
    category_attempts: Counter[str] = Counter()
    category_validated: Counter[str] = Counter()
    exact_stable = status_stable = content_stable = 0

    for case in cases:
        expected = case["expected"]
        concepts = expected.get("required_concepts", [])
        expected_concepts += len(concepts) * repetitions
        fingerprints: list[str] = []
        statuses: list[str] = []
        content_results: list[bool] = []
        case_prepared = case_invoked = case_validated = 0
        case_status_correct = case_content_correct = 0
        for _ in range(repetitions):
            counting_client = CountingClient(client)
            started_at = time.perf_counter()
            result = await _application(case, counting_client).execute(
                case["query"], top_k=1
            )
            latencies.append((time.perf_counter() - started_at) * 1_000)
            preparation = result.routed.compiled_request
            was_prepared = preparation is not None and preparation.is_prepared
            prepared += was_prepared
            case_prepared += was_prepared
            invoked += counting_client.call_count
            case_invoked += counting_client.call_count
            telemetry = result.synthesis.telemetry
            input_tokens += telemetry.input_tokens
            output_tokens += telemetry.output_tokens
            answer = result.synthesis.answer
            if answer is None:
                fingerprints.append(f"{telemetry.status.value}:{telemetry.failure_code}")
                statuses.append(telemetry.status.value)
                content_results.append(False)
                continue
            validated += 1
            case_validated += 1
            category_validated[str(case["category"])] += 1
            fingerprints.append(_answer_fingerprint(answer))
            statuses.append(answer.status)
            correct_status = answer.status == expected["status"]
            status_correct += correct_status
            case_status_correct += correct_status
            content_ok = False
            if answer.status == "answered" and expected["status"] == "answered":
                grade = grade_expected_content(
                    " ".join(claim.text for claim in answer.claims), expected
                )
                matched_concepts += grade.matched_concept_count
                content_ok = grade.correct
                content_correct += content_ok
                case_content_correct += content_ok
            content_results.append(content_ok)
        category_attempts[str(case["category"])] += repetitions
        exact_case_stable = len(set(fingerprints)) == 1
        status_case_stable = len(set(statuses)) == 1
        content_case_stable = len(set(content_results)) == 1
        exact_stable += exact_case_stable
        status_stable += status_case_stable
        content_stable += content_case_stable
        outcomes.append(
            {
                "case_id": case["id"],
                "category": case["category"],
                "attempt_count": repetitions,
                "prepared_count": case_prepared,
                "client_invocation_count": case_invoked,
                "validated_count": case_validated,
                "status_correct_count": case_status_correct,
                "content_correct_count": case_content_correct,
                "exact_response_stable": exact_case_stable,
                "status_stable": status_case_stable,
                "content_correctness_stable": content_case_stable,
            }
        )

    return {
        "schema_version": 1,
        "policy": _POLICY,
        "dataset": "wholly_synthetic",
        "case_count": len(cases),
        "repetitions_per_case": repetitions,
        "attempt_count": attempts,
        "metrics": {
            "preparation_rate": prepared / attempts,
            "single_invocation_rate": invoked / attempts,
            "validated_release_rate": validated / attempts,
            "response_status_accuracy": status_correct / attempts,
            "answer_content_accuracy": (
                content_correct / answerable_attempts if answerable_attempts else None
            ),
            "required_concept_recall": (
                matched_concepts / expected_concepts if expected_concepts else None
            ),
            "mean_application_latency_ms": sum(latencies) / attempts,
            "max_application_latency_ms": max(latencies),
            "mean_input_tokens": input_tokens / attempts,
            "mean_output_tokens": output_tokens / attempts,
            "exact_response_stability_rate": exact_stable / len(cases),
            "status_stability_rate": status_stable / len(cases),
            "content_correctness_stability_rate": content_stable / len(cases),
        },
        "by_category": {
            category: {
                "attempt_count": count,
                "validated_count": category_validated[category],
            }
            for category, count in sorted(category_attempts.items())
        },
        "cases": outcomes,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://llm-server:8080")
    parser.add_argument("--startup-timeout", type=float, default=180)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--max-output-tokens", type=int, default=512)
    args = parser.parse_args(argv)
    try:
        fingerprint = verify_input(args.dataset, None)
        cases = load_dataset(args.dataset)
        wait_until_ready(args.base_url, timeout_seconds=args.startup_timeout)
        client = LlamaCppClient(
            base_url=args.base_url,
            max_output_tokens=args.max_output_tokens,
            allowed_hosts=frozenset({"llm-server", "127.0.0.1", "localhost", "::1"}),
        )
        report = asyncio.run(
            run_benchmark(cases, client=client, repetitions=args.repetitions)
        )
        report["input_sha256"] = fingerprint
        report["max_output_tokens"] = args.max_output_tokens
        write_private_report(report, args.output)
    except (
        OSError,
        TimeoutError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(json.dumps({**report, "succeeded": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
