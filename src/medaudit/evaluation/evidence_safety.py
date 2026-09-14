"""Evaluate deterministic quarantine signals on wholly synthetic evidence."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.rag import inspect_evidence_text

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."


def load_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != "evidence-instruction-safety-v1"
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported evidence safety dataset schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("evidence safety cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("evidence safety case ids must be present and unique")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    if not cases:
        raise ValueError("evidence safety cases are required")
    outcomes: list[dict[str, Any]] = []
    true_positive = true_negative = attack_count = legitimate_count = 0
    exact = 0
    for case in cases:
        expected_suspicious = case.get("suspicious")
        expected_signals = case.get("expected_signals")
        if not isinstance(expected_suspicious, bool) or not isinstance(
            expected_signals, list
        ):
            raise ValueError("each safety case requires expected labels")
        actual_signals = sorted(
            signal.value for signal in inspect_evidence_text(case["text"])
        )
        actual_suspicious = bool(actual_signals)
        attack_count += expected_suspicious
        legitimate_count += not expected_suspicious
        true_positive += expected_suspicious and actual_suspicious
        true_negative += not expected_suspicious and not actual_suspicious
        correct = actual_signals == sorted(expected_signals)
        exact += correct
        outcomes.append(
            {
                "case_id": case["id"],
                "category": case["category"],
                "correct": correct,
                "quarantine_correct": actual_suspicious == expected_suspicious,
                "signal_count": len(actual_signals),
            }
        )
    if not attack_count or not legitimate_count:
        raise ValueError("safety evaluation requires attack and legitimate cases")
    return {
        "schema_version": 1,
        "policy": "evidence-instruction-safety-v1",
        "case_count": len(cases),
        "metrics": {
            "exact_signal_match": exact / len(cases),
            "attack_recall": true_positive / attack_count,
            "legitimate_specificity": true_negative / legitimate_count,
            "quarantine_accuracy": (true_positive + true_negative) / len(cases),
        },
        "cases": outcomes,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = evaluate(load_cases(args.cases))
    report["input_sha256"] = verify_input(args.cases, None)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
