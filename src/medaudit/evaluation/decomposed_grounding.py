"""Adversarial evaluation of the decomposed grounded-response validator."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.llm import LLMResponse, Usage
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
    validate_decomposed_grounded_response,
)
from medaudit.retrieval import ConfidenceSignals

_SIGNALS = ConfidenceSignals(1.0, 1.0, 1.0, 1.0, 1.0, 1)


def load_dataset(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != "decomposed-grounding-validation-v1"
        or payload.get("notice")
        != "Conteúdo integralmente sintético, sem reprodução de documentos reais."
    ):
        raise ValueError("unsupported decomposed grounding dataset schema")
    cases = payload.get("cases")
    groups = payload.get("evidence_groups")
    if not isinstance(cases, list) or not cases or not isinstance(groups, list):
        raise ValueError("evidence groups and validation cases are required")
    identifiers = [case["id"] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("decomposed grounding case ids must be unique")
    return payload


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    bundle = _build_bundle(payload)
    expected_counts: Counter[str] = Counter()
    correct_counts: Counter[str] = Counter()
    outcomes: list[dict[str, Any]] = []
    for case in payload["cases"]:
        expected = case["expected"]
        category = expected["category"]
        expected_counts[category] += 1
        try:
            validate_decomposed_grounded_response(
                LLMResponse(
                    data=case["response"],
                    model="synthetic-model",
                    latency_ms=1,
                    usage=Usage(input_tokens=1, output_tokens=1),
                ),
                bundle,
            )
            actual_valid = True
            actual_error = None
        except ValueError as error:
            actual_valid = False
            actual_error = str(error)
        correct = (
            actual_valid == expected["valid"]
            and actual_error == expected.get("error")
        )
        correct_counts[category] += correct
        outcomes.append(
            {
                "case_id": case["id"],
                "category": category,
                "correct": correct,
                "actual_valid": actual_valid,
            }
        )
    return {
        "schema_version": 1,
        "policy": "decomposed-grounding-validation-v1",
        "case_count": len(outcomes),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes)
            / len(outcomes),
            "exact_match_by_category": {
                category: correct_counts[category] / count
                for category, count in sorted(expected_counts.items())
            },
        },
        "cases": outcomes,
    }


def _build_bundle(payload: dict[str, Any]) -> DecompositionEvidenceBundle:
    steps = tuple(
        QueryPlanStep(
            step_id=group["step_id"],
            query=group["scope"],
            scope=group["scope"],
        )
        for group in payload["evidence_groups"]
    )
    plan = QueryPlan(
        original_query=payload["query"],
        status=QueryPlanStatus.READY,
        strategy=QueryPlanStrategy.COMPARISON_SCOPES,
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
                        text="evidência integralmente sintética",
                    )
                    for index, item in enumerate(group["evidence"], start=1)
                ),
            ),
        )
        for step, group in zip(
            steps, payload["evidence_groups"], strict=True
        )
    )
    return group_decomposition_evidence(
        DecompositionExecution(
            plan=plan,
            status=DecompositionExecutionStatus.READY,
            steps=executed,
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--refuse-overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.output and args.refuse_overwrite and args.output.exists():
        raise FileExistsError("decomposed grounding output already exists")
    report = evaluate(load_dataset(args.dataset))
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
