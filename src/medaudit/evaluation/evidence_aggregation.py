"""Evaluate deterministic grouping and gating of decomposed evidence."""

import argparse
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
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
    group_decomposition_evidence,
)
from medaudit.retrieval import ConfidenceSignals

_EMPTY_SIGNALS = ConfidenceSignals(0.0, 0.0, 0.0, None, 0.0, 0)


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != "decomposition-evidence-aggregation-v1"
        or payload.get("notice")
        != "Conteúdo integralmente sintético, sem reprodução de documentos reais."
    ):
        raise ValueError("unsupported evidence aggregation dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("at least one evidence aggregation case is required")
    identifiers = [case["id"] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("evidence aggregation case ids must be unique")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not cases:
        raise ValueError("at least one evidence aggregation case is required")
    outcomes: list[dict[str, Any]] = []
    context_correct = 0
    citation_correct = 0
    group_count = 0
    for case in cases:
        execution = _build_execution(case)
        bundle = group_decomposition_evidence(execution)
        actual = _observable_bundle(bundle)
        expected = case["expected"]
        exact = actual == expected
        for group, executed in zip(
            bundle.groups, execution.steps, strict=True
        ):
            context_correct += group.step == executed.step
            citation_correct += group.evidence == executed.retrieval.evidence
            group_count += 1
        outcomes.append(
            {
                "case_id": case["id"],
                "correct": exact,
                "generation_gate_correct": (
                    bundle.can_generate == expected["can_generate"]
                ),
            }
        )
    return {
        "schema_version": 1,
        "policy": "decomposition-evidence-aggregation-v1",
        "case_count": len(cases),
        "group_count": group_count,
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes)
            / len(outcomes),
            "context_preservation_accuracy": context_correct / group_count,
            "citation_preservation_accuracy": citation_correct / group_count,
            "generation_gate_accuracy": sum(
                item["generation_gate_correct"] for item in outcomes
            )
            / len(outcomes),
        },
        "cases": outcomes,
    }


def _build_execution(case: dict[str, Any]) -> DecompositionExecution:
    plan_status = QueryPlanStatus(case["plan_status"])
    strategy = (
        QueryPlanStrategy(case["strategy"])
        if case.get("strategy") is not None
        else None
    )
    steps = tuple(_build_plan_step(item) for item in case["steps"])
    plan = QueryPlan(
        original_query=case["query"],
        status=plan_status,
        strategy=strategy,
        steps=steps,
    )
    executed = tuple(
        ExecutedQueryStep(
            step=step,
            retrieval=RetrievalDecision(
                query=step.query,
                status=RetrievalStatus(raw["retrieval_status"]),
                signals=_EMPTY_SIGNALS,
                evidence=tuple(_build_evidence(item) for item in raw["evidence"]),
            ),
        )
        for step, raw in zip(steps, case["steps"], strict=True)
    )
    return DecompositionExecution(
        plan=plan,
        status=DecompositionExecutionStatus(case["execution_status"]),
        steps=executed,
    )


def _build_plan_step(item: dict[str, Any]) -> QueryPlanStep:
    raw_date = item.get("reference_date")
    return QueryPlanStep(
        step_id=item["step_id"],
        query=item["query"],
        reference_date=date.fromisoformat(raw_date) if raw_date else None,
        scope=item.get("scope"),
    )


def _build_evidence(item: dict[str, Any]) -> Evidence:
    return Evidence(
        location=EvidenceLocation(
            chunk_id=item["chunk_id"],
            document_id=item["document_id"],
            rank=item["rank"],
            score=item.get("score", 1.0),
            page=item.get("page"),
            section=item.get("section"),
        ),
        text=item.get("text", "evidência integralmente sintética"),
    )


def _observable_bundle(bundle: DecompositionEvidenceBundle) -> dict[str, Any]:
    return {
        "can_generate": bundle.can_generate,
        "groups": [
            {
                "step_id": group.step.step_id,
                "reference_date": (
                    group.step.reference_date.isoformat()
                    if group.step.reference_date
                    else None
                ),
                "scope": group.step.scope,
                "citations": [
                    {
                        "chunk_id": evidence.location.chunk_id,
                        "document_id": evidence.location.document_id,
                        "rank": evidence.location.rank,
                    }
                    for evidence in group.evidence
                ],
            }
            for group in bundle.groups
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--refuse-overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.output and args.refuse_overwrite and args.output.exists():
        raise FileExistsError("evidence aggregation output already exists")
    report = evaluate(load_cases(args.cases))
    report["input_sha256"] = verify_input(args.cases, args.expected_sha256)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
