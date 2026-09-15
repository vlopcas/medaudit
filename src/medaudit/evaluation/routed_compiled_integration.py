"""Evaluate the routed pipeline and opt-in compiled gateway together."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.evaluation.context_compilation import WordTokenEstimator
from medaudit.evaluation.query_understanding import verify_input
from medaudit.rag import (
    CompiledContextGateway,
    CompiledRequestMode,
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    RoutedEvidenceFirstPipeline,
)
from medaudit.retrieval import BM25Index

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "routed-compiled-integration-development-v1"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported routed compiled integration dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("routed compiled integration cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("routed compiled integration ids must be present and unique")
    return cases


def _pipeline(case: dict[str, Any]) -> RoutedEvidenceFirstPipeline:
    chunks = [
        Chunk("chunk-alpha", "document-alpha", "regra alfa sintética"),
        Chunk("chunk-beta", "document-beta", "regra beta sintética"),
    ]
    evidence_pipeline = EvidenceFirstPipeline(
        chunks=chunks,
        retriever=BM25Index(chunks),
        policy=FrozenTopScorePolicy(threshold=case.get("threshold", 0.1)),
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
        token_budget=case.get("token_budget", 100),
        estimator=WordTokenEstimator(),
        clock=lambda: 1.0,
    )
    return RoutedEvidenceFirstPipeline(
        evidence_pipeline,
        decomposition_executor=executor,
        compiled_context_gateway=gateway,
    )


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not cases:
        raise ValueError("routed compiled integration cases are required")
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in cases:
        result = _pipeline(case).retrieve_with_compiled_request(
            case["query"],
            top_k=case.get("top_k", 1),
            reviewed_evidence_ids=case.get("review_evidence_ids", []),
        )
        preparation = result.compiled_request
        actual = {
            "route": result.retrieval.route.value,
            "execution_present": result.retrieval.execution is not None,
            "bundle_present": result.retrieval.evidence_bundle is not None,
            "preparation_present": preparation is not None,
            "preparation_status": (
                preparation.telemetry.status.value if preparation else None
            ),
            "context_status": (
                preparation.telemetry.context_status.value
                if preparation and preparation.telemetry.context_status
                else None
            ),
            "request_present": (
                preparation.request is not None if preparation else False
            ),
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
            "request_safety": sum(
                item["request_present"]
                == (item["preparation_status"] == "prepared")
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    report = evaluate(load_dataset(args.dataset))
    report["input_sha256"] = verify_input(args.dataset, args.expected_sha256)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
