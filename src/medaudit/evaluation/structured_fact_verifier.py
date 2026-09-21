"""Evaluate typed deterministic fact verification on synthetic cases."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.local_decomposed_grounding import build_bundle
from medaudit.evaluation.query_understanding import verify_input
from medaudit.llm import LLMResponse, Usage
from medaudit.rag import StructuredFactVerifier, validate_decomposed_grounded_response

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "structured-fact-verifier-development-v1"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported structured fact verifier schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("structured fact verifier cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("case ids must be present and unique")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    verifier = StructuredFactVerifier()
    outcomes: list[dict[str, Any]] = []
    label_counts: Counter[str] = Counter()
    label_correct: Counter[str] = Counter()
    for case in cases:
        bundle = build_bundle(case)
        answer = validate_decomposed_grounded_response(
            LLMResponse(
                data=case["response"],
                model="synthetic-model",
                latency_ms=1,
                usage=Usage(input_tokens=1, output_tokens=1),
            ),
            bundle,
        )
        result = verifier.verify(answer, bundle)
        actual = {
            "decision": result.decision.value,
            "code": result.code.value if result.code else None,
        }
        correct = actual == case["expected"]
        label = str(case["risk_label"])
        label_counts[label] += 1
        label_correct[label] += correct
        outcomes.append(
            {
                "case_id": case["id"],
                "category": case["category"],
                "risk_label": label,
                "correct": correct,
                **actual,
            }
        )
    return {
        "schema_version": 1,
        "policy": _POLICY,
        "case_count": len(cases),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes) / len(outcomes),
            "exact_match_by_risk_label": {
                label: label_correct[label] / count
                for label, count in sorted(label_counts.items())
            },
        },
        "cases": outcomes,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args(argv)
    report = evaluate(load_dataset(args.dataset))
    report["input_sha256"] = verify_input(args.dataset, None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
