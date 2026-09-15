"""Evaluate the opt-in compiled-context gateway on synthetic bundles."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from medaudit.evaluation.context_compilation import WordTokenEstimator
from medaudit.evaluation.local_decomposed_grounding import build_bundle
from medaudit.evaluation.query_understanding import verify_input
from medaudit.rag import (
    CompiledContextGateway,
    CompiledRequestMode,
    DecompositionEvidenceBundle,
    DecompositionExecutionStatus,
    RetrievalStatus,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_DEVELOPMENT_POLICY = "compiled-context-gateway-development-v1"
_HOLDOUT_POLICY = "compiled-context-gateway-holdout-v1"


class RejectingTokenEstimator:
    """Exercise the gateway's fail-closed compiler boundary."""

    def estimate(self, text: str) -> int:
        raise ValueError("synthetic estimator rejection")


def load_dataset(
    path: Path, *, expected_policy: str = _DEVELOPMENT_POLICY
) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != expected_policy
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported compiled context gateway dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("compiled context gateway cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("compiled context gateway ids must be present and unique")
    return cases


def _make_bundle(case: dict[str, Any]) -> DecompositionEvidenceBundle:
    bundle = build_bundle(case)
    if case.get("bundle_ready", True):
        return bundle
    final_step = bundle.execution.steps[-1]
    incomplete_step = replace(
        final_step,
        retrieval=replace(
            final_step.retrieval,
            status=RetrievalStatus.INSUFFICIENT_EVIDENCE,
            evidence=(),
        ),
    )
    execution = replace(
        bundle.execution,
        status=DecompositionExecutionStatus.INSUFFICIENT_EVIDENCE,
        steps=(*bundle.execution.steps[:-1], incomplete_step),
    )
    return replace(
        bundle,
        execution=execution,
        groups=(*bundle.groups[:-1], replace(bundle.groups[-1], evidence=())),
    )


def evaluate(
    cases: list[dict[str, Any]], *, policy: str = _DEVELOPMENT_POLICY
) -> dict[str, Any]:
    if not cases:
        raise ValueError("compiled context gateway cases are required")
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in cases:
        estimator = (
            RejectingTokenEstimator()
            if case.get("estimator") == "rejecting"
            else WordTokenEstimator()
        )
        gateway = CompiledContextGateway(
            mode=CompiledRequestMode(case["mode"]),
            token_budget=case["token_budget"],
            estimator=estimator,
            clock=lambda: 1.0,
        )
        result = gateway.prepare(
            _make_bundle(case),
            reviewed_evidence_ids=case.get("review_evidence_ids", []),
        )
        telemetry = result.telemetry
        actual = {
            "status": telemetry.status.value,
            "context_status": (
                telemetry.context_status.value if telemetry.context_status else None
            ),
            "failure_code": telemetry.failure_code,
            "request_present": result.request is not None,
            "item_count": telemetry.item_count,
            "group_count": telemetry.group_count,
            "exclusion_count": telemetry.exclusion_count,
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
                "estimated_tokens": telemetry.estimated_tokens,
                "token_budget": telemetry.token_budget,
                "duration_ms": telemetry.duration_ms,
            }
        )
    return {
        "schema_version": 1,
        "policy": policy,
        "case_count": len(cases),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes) / len(outcomes),
            "request_safety": sum(
                item["request_present"] == (item["status"] == "prepared")
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
    parser.add_argument(
        "--dataset-policy",
        choices=(_DEVELOPMENT_POLICY, _HOLDOUT_POLICY),
        default=_DEVELOPMENT_POLICY,
    )
    parser.add_argument("--expected-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--refuse-overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.output and args.refuse_overwrite and args.output.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {args.output}")
    report = evaluate(
        load_dataset(args.dataset, expected_policy=args.dataset_policy),
        policy=args.dataset_policy,
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
