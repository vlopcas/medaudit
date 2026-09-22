"""Evaluate fail-closed admission of synthetic structured rule sets."""

import argparse
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.rules import (
    RuleDecision,
    RuleSet,
    StructuredRule,
    admit_rule_set,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "structured-rule-admission-development-v1"
_HOLDOUT_POLICY = "structured-rule-admission-holdout-v1"


def load_dataset(
    path: Path, *, expected_policy: str = _POLICY
) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != expected_policy
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported structured rule admission schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("structured rule admission cases are required")
    return cases


def evaluate(
    cases: list[dict[str, Any]], *, policy: str = _POLICY
) -> dict[str, Any]:
    results = [_evaluate_case(case) for case in cases]
    passed = sum(result["passed"] for result in results)
    return {
        "schema_version": 1,
        "policy": policy,
        "case_count": len(results),
        "metrics": {
            "exact_match": passed == len(results),
            "passed": passed,
            "total": len(results),
        },
        "cases": results,
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    rule_set = RuleSet(
        schema_version=1,
        rules=tuple(_parse_rule(rule) for rule in case["rules"]),
    )
    reviewed = frozenset(
        tuple(pair) for pair in case.get("reviewed_redundancies", [])
    )
    result = admit_rule_set(rule_set, reviewed_redundancies=reviewed)
    actual = {
        "status": result.status.value,
        "code": result.code.value,
        "finding_count": len(result.findings),
    }
    return {
        "case_id": case["case_id"],
        "passed": actual == case["expected"],
        **actual,
    }


def _parse_rule(payload: dict[str, Any]) -> StructuredRule:
    return StructuredRule(
        rule_id=payload["rule_id"],
        version=payload["version"],
        subject=payload["subject"],
        action=payload["action"],
        decision=RuleDecision(payload["decision"]),
        effective_from=date.fromisoformat(payload["effective_from"]),
        effective_until=(
            date.fromisoformat(payload["effective_until"])
            if payload.get("effective_until")
            else None
        ),
        priority=payload["priority"],
        conditions=tuple(sorted(payload.get("conditions", {}).items())),
        source_document_id=payload["source_document_id"],
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--dataset-policy",
        choices=(_POLICY, _HOLDOUT_POLICY),
        default=_POLICY,
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
    report["input_sha256"] = verify_input(
        args.dataset, args.expected_sha256
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
