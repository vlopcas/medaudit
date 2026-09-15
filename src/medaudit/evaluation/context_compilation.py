"""Evaluate deterministic context compilation on wholly synthetic bundles."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from medaudit.evaluation.local_decomposed_grounding import build_bundle
from medaudit.evaluation.query_understanding import verify_input
from medaudit.rag import (
    ContextItemKind,
    ContextTrust,
    DecompositionEvidenceBundle,
    DecompositionExecutionStatus,
    RetrievalStatus,
    compile_decomposed_context,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."


class WordTokenEstimator:
    """Stable estimator used only by the synthetic evaluation protocol."""

    def estimate(self, text: str) -> int:
        return len(text.split())


def load_dataset(
    path: Path, *, expected_policy: str = "context-compilation-development-v1"
) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != expected_policy
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported context compilation dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("context compilation cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("context compilation case ids must be present and unique")
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
    cases: list[dict[str, Any]], *, policy: str = "context-compilation-development-v1"
) -> dict[str, Any]:
    if not cases:
        raise ValueError("context compilation cases are required")
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in cases:
        expected = case["expected"]
        context = compile_decomposed_context(
            _make_bundle(case),
            instruction=case["instruction"],
            token_budget=case["token_budget"],
            estimator=WordTokenEstimator(),
            review_evidence_ids=frozenset(case.get("review_evidence_ids", [])),
        )
        evidence_items = [
            item for item in context.items if item.kind is ContextItemKind.EVIDENCE
        ]
        actual_ids = [item.item_id for item in evidence_items]
        actual_steps = {
            item.item_id: list(item.step_ids) for item in evidence_items
        }
        actual_reasons = [item.reason.value for item in context.exclusions]
        trust_boundary_valid = all(
            (item.kind is ContextItemKind.INSTRUCTION)
            == (item.trust is ContextTrust.TRUSTED_CONTROL)
            for item in context.items
        )
        correct = (
            context.status.value == expected["status"]
            and actual_ids == expected["included_evidence_ids"]
            and actual_steps == expected["evidence_steps"]
            and actual_reasons == expected["exclusion_reasons"]
            and trust_boundary_valid
        )
        category = case["category"]
        category_counts[category] += 1
        category_correct[category] += correct
        outcomes.append(
            {
                "case_id": case["id"],
                "category": category,
                "correct": correct,
                "actual_status": context.status.value,
                "included_evidence_ids": actual_ids,
                "excluded_item_count": len(context.exclusions),
                "estimated_tokens": context.estimated_tokens,
                "trust_boundary_valid": trust_boundary_valid,
            }
        )
    return {
        "schema_version": 1,
        "policy": policy,
        "case_count": len(cases),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes) / len(cases),
            "trust_boundary_valid": sum(
                item["trust_boundary_valid"] for item in outcomes
            )
            / len(cases),
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
        choices=(
            "context-compilation-development-v1",
            "context-compilation-holdout-v1",
        ),
        default="context-compilation-development-v1",
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
