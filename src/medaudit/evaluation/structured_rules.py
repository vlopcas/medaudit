"""Evaluate deterministic temporal rule resolution on synthetic cases."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.rules import (
    DeterministicRuleEngine,
    RuleDecision,
    RuleQuery,
    RuleSet,
    StructuredRule,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "structured-rules-development-v1"


def load_dataset(path: Path) -> tuple[RuleSet, list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported structured rules dataset schema")
    raw_rules = payload.get("rules")
    cases = payload.get("cases")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise ValueError("structured rules are required")
    if not isinstance(cases, list) or not cases:
        raise ValueError("structured rule cases are required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(identifiers) != len(set(identifiers)):
        raise ValueError("case ids must be present and unique")
    rules = tuple(_parse_rule(item) for item in raw_rules)
    return RuleSet(schema_version=1, rules=rules), cases


def evaluate(rule_set: RuleSet, cases: list[dict[str, Any]]) -> dict[str, Any]:
    engine = DeterministicRuleEngine(rule_set)
    outcomes: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    for case in cases:
        query = case["query"]
        result = engine.resolve(
            RuleQuery(
                subject=query["subject"],
                action=query["action"],
                reference_date=date.fromisoformat(query["reference_date"]),
                attributes=_pairs(query.get("attributes", {})),
            )
        )
        actual = {
            "status": result.status.value,
            "code": result.code.value,
            "decision": result.decision.value if result.decision else None,
            "matched_rule_versions": list(result.matched_rule_versions),
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
        "rule_count": len(rule_set.rules),
        "case_count": len(cases),
        "metrics": {
            "exact_match": sum(item["correct"] for item in outcomes) / len(outcomes),
            "exact_match_by_category": {
                category: category_correct[category] / count
                for category, count in sorted(category_counts.items())
            },
        },
        "cases": outcomes,
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
        conditions=_pairs(payload.get("conditions", {})),
        source_document_id=payload["source_document_id"],
    )


def _pairs(payload: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(payload.items()))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args(argv)
    rule_set, cases = load_dataset(args.dataset)
    report = evaluate(rule_set, cases)
    report["input_sha256"] = verify_input(args.dataset, None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
