"""Evaluate the independent synthesis release-verification boundary."""

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
    GroundedSynthesisOrchestrator,
    SynthesisMode,
    VerificationCode,
    VerificationDecision,
    VerificationResult,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "release-verification-development-v1"


class SyntheticVerifier:
    """Return a configured content-free decision or synthetic failure."""

    def __init__(self, behavior: str) -> None:
        self.behavior = behavior
        self.call_count = 0

    def verify(self, answer: object, evidence: object) -> VerificationResult:
        self.call_count += 1
        if self.behavior == "failure":
            raise RuntimeError("synthetic verifier failure")
        if self.behavior == "release":
            return VerificationResult(VerificationDecision.RELEASE)
        if self.behavior == "reject_support":
            return VerificationResult(
                VerificationDecision.REJECT,
                VerificationCode.CLAIM_SUPPORT_FAILED,
            )
        if self.behavior == "reject_untrusted":
            return VerificationResult(
                VerificationDecision.REJECT,
                VerificationCode.UNTRUSTED_CONTENT,
            )
        if self.behavior == "review":
            return VerificationResult(
                VerificationDecision.REVIEW,
                VerificationCode.REVIEW_REQUIRED,
            )
        raise ValueError("unsupported synthetic verifier behavior")


def load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported release verification dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("release verification cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("case ids must be present and unique")
    return cases


async def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in cases:
        client = SyntheticClient(case.get("client_behavior", "valid"))
        verifier = None
        if behavior := case.get("verifier_behavior"):
            verifier = SyntheticVerifier(behavior)
        result = await GroundedSynthesisOrchestrator(
            mode=SynthesisMode.EXPERIMENTAL,
            client=client,
            verifier=verifier,
            clock=lambda: 1.0,
        ).synthesize(_pipeline(case).retrieve_with_compiled_request(
            case["query"], top_k=1
        ))
        actual = {
            "synthesis_status": result.telemetry.status.value,
            "failure_code": result.telemetry.failure_code,
            "client_called": client.call_count == 1,
            "verifier_called": verifier is not None and verifier.call_count == 1,
            "answer_present": result.answer is not None,
            "answer_status": result.answer.status if result.answer else None,
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
        "policy": _POLICY,
        "case_count": len(cases),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes) / len(outcomes),
            "release_safety": sum(
                item["answer_present"]
                == (item["synthesis_status"] == "validated")
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
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = asyncio.run(evaluate(load_dataset(args.dataset)))
    report["input_sha256"] = verify_input(args.dataset, None)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
