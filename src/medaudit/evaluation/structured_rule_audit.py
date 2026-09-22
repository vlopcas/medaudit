"""Evaluate static overlap auditing for synthetic structured rules."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.rules import RuleDecision, RuleSet, StructuredRule, audit_rule_set

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "structured-rule-audit-development-v1"


def load_dataset(path: Path) -> tuple[RuleSet, list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported structured rule audit schema")
    raw_rules = payload.get("rules")
    expected = payload.get("expected_findings")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise ValueError("structured rules are required")
    if not isinstance(expected, list):
        raise ValueError("expected audit findings are required")
    rules = tuple(_parse_rule(item) for item in raw_rules)
    return RuleSet(schema_version=1, rules=rules), expected


def evaluate(
    rule_set: RuleSet, expected: list[dict[str, Any]]
) -> dict[str, Any]:
    findings = [
        {"code": item.code.value, "rule_versions": list(item.rule_versions)}
        for item in audit_rule_set(rule_set)
    ]
    expected_normalized = sorted(
        expected,
        key=lambda item: (item["code"], item["rule_versions"]),
    )
    code_counts = Counter(item["code"] for item in findings)
    return {
        "schema_version": 1,
        "policy": _POLICY,
        "rule_count": len(rule_set.rules),
        "finding_count": len(findings),
        "metrics": {
            "exact_match": findings == expected_normalized,
            "finding_count_by_code": dict(sorted(code_counts.items())),
        },
        "findings": findings,
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
    args = parser.parse_args(argv)
    rule_set, expected = load_dataset(args.dataset)
    report = evaluate(rule_set, expected)
    report["input_sha256"] = verify_input(args.dataset, None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
