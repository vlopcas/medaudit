"""Benchmark local synthesis over wholly synthetic grouped evidence."""

import argparse
import asyncio
import hashlib
import json
import time
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any, Literal

from medaudit.evaluation.content_grade import grade_expected_content
from medaudit.evaluation.local_llm_benchmark import verify_input, wait_until_ready
from medaudit.evaluation.private_bm25 import write_private_report
from medaudit.llm import LlamaCppClient, LLMClient, LLMRequest
from medaudit.query_understanding import (
    QueryPlan,
    QueryPlanStatus,
    QueryPlanStep,
    QueryPlanStrategy,
)
from medaudit.rag import (
    DecompositionEvidenceBundle,
    DecompositionExecution,
    DecompositionExecutionStatus,
    Evidence,
    EvidenceLocation,
    ExecutedQueryStep,
    RetrievalDecision,
    RetrievalStatus,
    build_decomposed_grounded_request,
    group_decomposition_evidence,
    validate_decomposed_grounded_response,
)
from medaudit.retrieval import ConfidenceSignals

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_SIGNALS = ConfidenceSignals(1.0, 1.0, 1.0, 1.0, 1.0, 1)
PromptPolicy = Literal["baseline", "answer-when-supported-v1"]


def apply_prompt_policy(request: LLMRequest, policy: PromptPolicy) -> LLMRequest:
    """Apply one isolated decision-policy change without touching input/schema."""
    if policy == "baseline":
        return request
    if policy != "answer-when-supported-v1":
        raise ValueError("unsupported decomposed grounding prompt policy")
    decision_instruction = (
        " When the supplied evidence directly contains every fact requested, "
        "you must return answered. Use insufficient_evidence only when at least "
        "one requested fact is absent. Multiple evidence groups alone are never "
        "a reason to abstain."
    )
    return replace(request, instruction=request.instruction + decision_instruction)


def load_dataset(path: Path) -> list[dict[str, Any]]:
    """Load only the explicit synthetic benchmark schema."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != "local-decomposed-grounding-benchmark-v1"
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported local decomposed grounding schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("local decomposed grounding cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("case ids must be present and unique")
    return cases


def build_bundle(case: dict[str, Any]) -> DecompositionEvidenceBundle:
    """Construct a complete provider-neutral bundle from one synthetic case."""
    raw_groups = case.get("evidence_groups")
    if not isinstance(raw_groups, list) or len(raw_groups) < 2:
        raise ValueError("each case requires at least two evidence groups")
    is_temporal = all(group.get("reference_date") for group in raw_groups)
    if any(group.get("reference_date") for group in raw_groups) != is_temporal:
        raise ValueError("a case cannot mix temporal and scoped evidence groups")
    steps = tuple(
        QueryPlanStep(
            step_id=group["step_id"],
            query=case["question"] if is_temporal else group["scope"],
            scope=None if is_temporal else group["scope"],
            reference_date=(
                date.fromisoformat(group["reference_date"])
                if is_temporal
                else None
            ),
        )
        for group in raw_groups
    )
    plan = QueryPlan(
        original_query=case["question"],
        status=QueryPlanStatus.READY,
        strategy=(
            QueryPlanStrategy.TEMPORAL_SNAPSHOTS
            if is_temporal
            else QueryPlanStrategy.COMPARISON_SCOPES
        ),
        steps=steps,
    )
    executed = tuple(
        ExecutedQueryStep(
            step=step,
            retrieval=RetrievalDecision(
                query=step.query,
                status=RetrievalStatus.READY,
                signals=_SIGNALS,
                evidence=tuple(
                    Evidence(
                        location=EvidenceLocation(
                            chunk_id=item["evidence_id"],
                            document_id=item["document_id"],
                            rank=index,
                            score=1.0,
                            page=None,
                            section=None,
                        ),
                        text=item["text"],
                    )
                    for index, item in enumerate(group["evidence"], start=1)
                ),
            ),
        )
        for step, group in zip(steps, raw_groups, strict=True)
    )
    return group_decomposition_evidence(
        DecompositionExecution(
            plan=plan,
            status=DecompositionExecutionStatus.READY,
            steps=executed,
        )
    )


async def run_benchmark(
    cases: list[dict[str, Any]],
    *,
    client: LLMClient,
    repetitions: int = 1,
    prompt_policy: PromptPolicy = "baseline",
) -> dict[str, Any]:
    """Measure local generation without retaining questions or model text."""
    if repetitions < 1:
        raise ValueError("benchmark repetitions must be positive")
    structured = grounded = status_correct = content_correct = 0
    grounded_answered = 0
    matched_concepts = expected_concepts = 0
    successful_latencies: list[float] = []
    attempt_latencies: list[float] = []
    outcomes: list[dict[str, Any]] = []
    categories: defaultdict[str, dict[str, int]] = defaultdict(
        lambda: {
            "case_count": 0,
            "attempt_count": 0,
            "grounded_contract_valid": 0,
            "status_correct": 0,
        }
    )
    exact_stable = status_stable = content_stable = 0
    for case in cases:
        expected = case.get("expected")
        if not isinstance(expected, dict) or expected.get("status") not in {
            "answered",
            "insufficient_evidence",
        }:
            raise ValueError("each case requires a supported expected status")
        if expected["status"] == "answered":
            concepts = expected.get("required_concepts")
            if not isinstance(concepts, list) or not concepts:
                raise ValueError("answered cases require expected concepts")
            expected_concepts += len(concepts) * repetitions
        bundle = build_bundle(case)
        request = apply_prompt_policy(
            build_decomposed_grounded_request(bundle), prompt_policy
        )
        category = categories[str(case["category"])]
        category["case_count"] += 1
        category["attempt_count"] += repetitions
        fingerprints: list[str] = []
        observed_statuses: list[str] = []
        observed_content: list[bool] = []
        valid_attempts = correct_attempts = correct_content_attempts = 0
        for _ in range(repetitions):
            response = None
            content_ok = False
            attempt_started = time.perf_counter()
            try:
                response = await client.generate(request)
                structured += 1
                fingerprints.append(
                    hashlib.sha256(
                        json.dumps(
                            response.data,
                            ensure_ascii=False,
                            sort_keys=True,
                        ).encode()
                    ).hexdigest()
                )
                answer = validate_decomposed_grounded_response(response, bundle)
                valid_attempts += 1
                grounded += 1
                observed_statuses.append(answer.status)
                actual_status = answer.status == expected["status"]
                correct_attempts += actual_status
                status_correct += actual_status
                category["grounded_contract_valid"] += 1
                category["status_correct"] += actual_status
                if answer.status == "answered" and expected["status"] == "answered":
                    grounded_answered += 1
                    grade = grade_expected_content(
                        " ".join(claim.text for claim in answer.claims), expected
                    )
                    content_ok = grade.correct
                    correct_content_attempts += content_ok
                    content_correct += content_ok
                    matched_concepts += grade.matched_concept_count
                observed_content.append(content_ok)
            except ValueError:
                fingerprints.append("invalid")
                observed_statuses.append("invalid")
                observed_content.append(False)
            finally:
                attempt_latencies.append(
                    (time.perf_counter() - attempt_started) * 1000
                )
            if response is not None:
                successful_latencies.append(response.latency_ms)
        exact_case_stable = len(set(fingerprints)) == 1
        status_case_stable = len(set(observed_statuses)) == 1
        content_case_stable = len(set(observed_content)) == 1
        exact_stable += exact_case_stable
        status_stable += status_case_stable
        content_stable += content_case_stable
        outcomes.append(
            {
                "case_id": case["id"],
                "category": case["category"],
                "attempt_count": repetitions,
                "grounded_contract_valid_count": valid_attempts,
                "status_correct_count": correct_attempts,
                "content_correct_count": correct_content_attempts,
                "exact_response_stable": exact_case_stable,
                "status_stable": status_case_stable,
                "content_correctness_stable": content_case_stable,
            }
        )
    answerable = sum(case["expected"]["status"] == "answered" for case in cases)
    attempt_count = len(cases) * repetitions
    answerable_attempts = answerable * repetitions
    return {
        "schema_version": 1,
        "dataset": "wholly_synthetic",
        "prompt_policy": prompt_policy,
        "case_count": len(cases),
        "repetitions_per_case": repetitions,
        "attempt_count": attempt_count,
        "metrics": {
            "structured_output_rate": structured / attempt_count,
            "grounded_contract_rate": grounded / attempt_count,
            "authorized_citation_rate": 1.0 if grounded_answered else None,
            "complete_group_coverage_rate": 1.0 if grounded_answered else None,
            "response_status_accuracy": status_correct / attempt_count,
            "answer_content_accuracy": content_correct / answerable_attempts,
            "required_concept_recall": (
                matched_concepts / expected_concepts if expected_concepts else None
            ),
            "mean_successful_generation_latency_ms": (
                sum(successful_latencies) / len(successful_latencies)
                if successful_latencies
                else None
            ),
            "mean_attempt_latency_ms": sum(attempt_latencies) / attempt_count,
            "max_attempt_latency_ms": max(attempt_latencies),
            "exact_response_stability_rate": exact_stable / len(cases),
            "status_stability_rate": status_stable / len(cases),
            "content_correctness_stability_rate": content_stable / len(cases),
        },
        "by_category": dict(sorted(categories.items())),
        "cases": outcomes,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://llm-server:8080")
    parser.add_argument("--startup-timeout", type=float, default=180)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--max-output-tokens", type=int)
    parser.add_argument(
        "--prompt-policy",
        choices=("baseline", "answer-when-supported-v1"),
        default="baseline",
    )
    parser.add_argument("--expected-sha256")
    parser.add_argument("--refuse-overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.refuse_overwrite and args.output.exists():
            raise FileExistsError("benchmark output already exists")
        fingerprint = verify_input(args.dataset, args.expected_sha256)
        cases = load_dataset(args.dataset)
        wait_until_ready(args.base_url, timeout_seconds=args.startup_timeout)
        client = LlamaCppClient(
            base_url=args.base_url,
            max_output_tokens=args.max_output_tokens,
            allowed_hosts=frozenset(
                {"llm-server", "127.0.0.1", "localhost", "::1"}
            ),
        )
        report = asyncio.run(
            run_benchmark(
                cases,
                client=client,
                repetitions=args.repetitions,
                prompt_policy=args.prompt_policy,
            )
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
