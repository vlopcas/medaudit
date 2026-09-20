"""Evaluate the routed synthesis application with synthetic fake clients."""

import argparse
import asyncio
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.evaluation.synthesis_orchestration import SyntheticClient, _pipeline
from medaudit.rag import (
    GroundedSynthesisApplication,
    GroundedSynthesisOrchestrator,
    SynthesisMode,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_DEVELOPMENT_POLICY = "synthesis-application-development-v1"
_HOLDOUT_POLICY = "synthesis-application-holdout-v1"


def load_dataset(
    path: Path, *, expected_policy: str = _DEVELOPMENT_POLICY
) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != expected_policy
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported synthesis application dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("synthesis application cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("synthesis application ids must be present and unique")
    return cases


async def evaluate(
    cases: list[dict[str, Any]], *, policy: str = _DEVELOPMENT_POLICY
) -> dict[str, Any]:
    if not cases:
        raise ValueError("synthesis application cases are required")
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in cases:
        client = SyntheticClient(case.get("client_behavior", "valid"))
        orchestrator = None
        if case.get("synthesis_mode") == "experimental":
            orchestrator = GroundedSynthesisOrchestrator(
                mode=SynthesisMode.EXPERIMENTAL,
                client=client,
                clock=lambda: 1.0,
            )
        result = await GroundedSynthesisApplication(
            _pipeline(case), orchestrator=orchestrator
        ).execute(
            case["query"],
            top_k=1,
            reviewed_evidence_ids=case.get("review_evidence_ids", []),
        )
        preparation = result.routed.compiled_request
        answer = result.synthesis.answer
        actual = {
            "route": result.routed.retrieval.route.value,
            "preparation_status": (
                preparation.telemetry.status.value if preparation else None
            ),
            "synthesis_status": result.synthesis.telemetry.status.value,
            "failure_code": result.synthesis.telemetry.failure_code,
            "client_called": client.call_count == 1,
            "answer_present": answer is not None,
            "answer_status": answer.status if answer else None,
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
        "policy": policy,
        "case_count": len(outcomes),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes) / len(outcomes),
            "invocation_safety": sum(
                not item["client_called"]
                or item["preparation_status"] == "prepared"
                for item in outcomes
            )
            / len(outcomes),
            "release_safety": sum(
                item["answer_present"] == (item["synthesis_status"] == "validated")
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
