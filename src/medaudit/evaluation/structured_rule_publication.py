"""Evaluate synthetic structured rule publication boundaries."""

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
    publish_rule_set,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "structured-rule-publication-development-v1"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported structured rule publication schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("structured rule publication cases are required")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    results = [_evaluate_case(case) for case in cases]
    passed = sum(result["passed"] for result in results)
    return {
        "schema_version": 1,
        "policy": _POLICY,
        "case_count": len(results),
        "metrics": {
            "exact_match": passed == len(results),
            "passed": passed,
            "total": len(results),
        },
        "cases": results,
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    previous = None
    if case.get("previous_rules"):
        previous_result = publish_rule_set(_parse_rule_set(case["previous_rules"]))
        previous = previous_result.catalog
        if previous is None:
            raise ValueError("previous synthetic catalog must be publishable")
    result = publish_rule_set(
        _parse_rule_set(case["current_rules"]),
        reviewed_redundancies=frozenset(
            tuple(pair) for pair in case.get("reviewed_redundancies", [])
        ),
        previous=previous,
        reviewed_replacements=frozenset(
            tuple(pair) for pair in case.get("reviewed_replacements", [])
        ),
    )
    actual = {
        "status": result.status.value,
        "code": result.code.value,
        "published_rule_versions": (
            [
                f"{rule.rule_id}@{rule.version}"
                for rule in result.catalog.rules
            ]
            if result.catalog
            else []
        ),
    }
    return {
        "case_id": case["case_id"],
        "passed": actual == case["expected"],
        **actual,
    }


def _parse_rule_set(payloads: list[dict[str, Any]]) -> RuleSet:
    return RuleSet(
        schema_version=1,
        rules=tuple(_parse_rule(payload) for payload in payloads),
    )


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
    args = parser.parse_args(argv)
    report = evaluate(load_dataset(args.dataset))
    report["input_sha256"] = verify_input(args.dataset, None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
