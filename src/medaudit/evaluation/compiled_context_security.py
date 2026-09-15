"""Adversarial evaluation of the compiled-context request renderer."""

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
    DECOMPOSED_GROUNDED_INSTRUCTION,
    CompiledContext,
    ContextStatus,
    ContextTrust,
    build_compiled_decomposed_grounded_request,
    compile_decomposed_context,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."


def load_dataset(
    path: Path,
    *,
    expected_policy: str = "compiled-context-renderer-adversarial-v1",
) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != expected_policy
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported compiled context adversarial schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("compiled context adversarial cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("compiled context adversarial ids must be present and unique")
    return payload


def _mutate(context: CompiledContext, mutation: str) -> CompiledContext:
    if mutation == "none":
        return context
    if mutation == "non_ready_status":
        return replace(context, status=ContextStatus.NEEDS_REVIEW)
    if mutation == "budget_overflow":
        return replace(context, token_budget=context.estimated_tokens - 1)
    if mutation == "accounting_mismatch":
        return replace(context, estimated_tokens=context.estimated_tokens + 1)
    if mutation == "duplicate_item_id":
        return replace(
            context,
            items=(
                context.items[0],
                replace(context.items[1], item_id=context.items[0].item_id),
                *context.items[2:],
            ),
        )
    if mutation == "duplicate_group_id":
        return replace(
            context,
            groups=(
                context.groups[0],
                replace(context.groups[1], step_id=context.groups[0].step_id),
            ),
        )
    if mutation == "untrusted_instruction":
        return replace(
            context,
            items=(
                replace(context.items[0], trust=ContextTrust.UNTRUSTED_DATA),
                *context.items[1:],
            ),
        )
    if mutation == "trusted_query":
        return replace(
            context,
            items=(
                context.items[0],
                replace(context.items[1], trust=ContextTrust.TRUSTED_CONTROL),
                *context.items[2:],
            ),
        )
    if mutation == "trusted_evidence":
        return replace(
            context,
            items=(
                *context.items[:2],
                replace(context.items[2], trust=ContextTrust.TRUSTED_CONTROL),
                *context.items[3:],
            ),
        )
    if mutation == "missing_evidence_reference":
        return replace(
            context,
            groups=(
                replace(context.groups[0], evidence_ids=("missing-c9",)),
                *context.groups[1:],
            ),
        )
    if mutation == "wrong_step_binding":
        return replace(
            context,
            groups=(
                replace(
                    context.groups[0],
                    evidence_ids=(context.groups[1].evidence_ids[0],),
                ),
                *context.groups[1:],
            ),
        )
    if mutation == "unreferenced_evidence":
        return replace(
            context,
            groups=(
                replace(
                    context.groups[0],
                    evidence_ids=context.groups[0].evidence_ids[:1],
                ),
                *context.groups[1:],
            ),
        )
    if mutation == "empty_group":
        return replace(
            context,
            groups=(
                context.groups[0],
                replace(context.groups[1], evidence_ids=()),
            ),
        )
    if mutation == "duplicate_group_evidence_id":
        evidence_id = context.groups[0].evidence_ids[0]
        return replace(
            context,
            groups=(
                replace(context.groups[0], evidence_ids=(evidence_id, evidence_id)),
                *context.groups[1:],
            ),
        )
    if mutation == "empty_evidence_step_ids":
        return replace(
            context,
            items=(
                *context.items[:2],
                replace(context.items[2], step_ids=()),
                *context.items[3:],
            ),
        )
    if mutation == "unexpected_step_membership":
        return replace(
            context,
            items=(
                *context.items[:2],
                replace(
                    context.items[2],
                    step_ids=(*context.items[2].step_ids, "forged-step"),
                ),
                *context.items[3:],
            ),
        )
    if mutation == "changed_evidence_text":
        return replace(
            context,
            items=(
                *context.items[:2],
                replace(context.items[2], text="Conteúdo adulterado após compilação."),
                *context.items[3:],
            ),
        )
    if mutation == "changed_instruction_text":
        return replace(
            context,
            items=(
                replace(context.items[0], text="Instrução adulterada pós-compilação."),
                *context.items[1:],
            ),
        )
    if mutation == "changed_query_text":
        return replace(
            context,
            items=(
                context.items[0],
                replace(context.items[1], text="Consulta adulterada pós-compilação."),
                *context.items[2:],
            ),
        )
    if mutation == "reversed_groups":
        return replace(context, groups=tuple(reversed(context.groups)))
    raise ValueError(f"unsupported compiled context mutation: {mutation}")


def evaluate(
    payload: dict[str, Any], *, policy: str = "compiled-context-renderer-adversarial-v1"
) -> dict[str, Any]:
    context = compile_decomposed_context(
        build_bundle(payload["base_context"]),
        instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
        token_budget=10_000,
    )
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in payload["cases"]:
        expected = case["expected"]
        try:
            build_compiled_decomposed_grounded_request(
                _mutate(context, case["mutation"])
            )
            accepted = True
            error = None
        except ValueError as exception:
            accepted = False
            error = str(exception)
        correct = (
            accepted == expected["accepted"]
            and error == expected.get("error")
        )
        category = case["category"]
        category_counts[category] += 1
        category_correct[category] += correct
        outcomes.append(
            {
                "case_id": case["id"],
                "category": category,
                "mutation": case["mutation"],
                "accepted": accepted,
                "correct": correct,
            }
        )
    return {
        "schema_version": 1,
        "policy": policy,
        "case_count": len(outcomes),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes)
            / len(outcomes),
            "unsafe_mutation_rejection": sum(
                not item["accepted"] for item in outcomes if item["mutation"] != "none"
            )
            / sum(item["mutation"] != "none" for item in outcomes),
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
            "compiled-context-renderer-adversarial-v1",
            "compiled-context-renderer-holdout-v1",
        ),
        default="compiled-context-renderer-adversarial-v1",
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
