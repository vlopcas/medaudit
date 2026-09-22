"""Measure whether current baselines leave a relational retrieval gap."""

import argparse
import json
from collections import Counter
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.documents import Chunk
from medaudit.evaluation.query_understanding import verify_input
from medaudit.query_understanding import (
    DeterministicQueryPlanner,
    ExplicitQueryRouter,
    QueryPlanStatus,
    QueryRoute,
)
from medaudit.retrieval import BM25Index
from medaudit.rules import (
    DeterministicRuleEngine,
    RuleDecision,
    RuleQuery,
    RuleResolutionStatus,
    RuleSet,
    StructuredRule,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "graph-necessity-development-v1"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported graph necessity schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("graph necessity cases are required")
    identifiers = [case.get("case_id") for case in cases]
    if len(identifiers) != len(set(identifiers)) or any(
        not identifier for identifier in identifiers
    ):
        raise ValueError("graph necessity case ids must be present and unique")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes = [_evaluate_case(case) for case in cases]
    chain_cases = [item for item in outcomes if item["expected_outcome"] == "chain"]
    gap_cases = [item for item in outcomes if item["candidate_graph_gap"]]
    category_counts = Counter(item["category"] for item in gap_cases)
    return {
        "schema_version": 1,
        "policy": _POLICY,
        "case_count": len(outcomes),
        "metrics": {
            "bm25_complete_chain_rate": (
                sum(item["bm25_complete_chain"] for item in chain_cases)
                / len(chain_cases)
            ),
            "existing_baseline_resolution_rate": (
                sum(item["resolved_by_existing_baseline"] for item in chain_cases)
                / len(chain_cases)
            ),
            "candidate_graph_gap_count": len(gap_cases),
            "candidate_graph_gap_by_category": dict(sorted(category_counts.items())),
        },
        "cases": outcomes,
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    chunks = [
        Chunk(
            chunk_id=item["chunk_id"],
            document_id=item["document_id"],
            text=item["text"],
        )
        for item in case["chunks"]
    ]
    retrieved = BM25Index(chunks).search(case["query"], top_k=case["top_k"])
    retrieved_ids = tuple(item.chunk.chunk_id for item in retrieved)
    expected_chain = tuple(case["expected_chain"])
    bm25_complete = bool(expected_chain) and set(expected_chain) <= set(retrieved_ids)

    route = ExplicitQueryRouter().route(case["query"])
    planner_ready = False
    if route is QueryRoute.REQUIRES_DECOMPOSITION:
        planner_ready = (
            DeterministicQueryPlanner().plan(case["query"]).status
            is QueryPlanStatus.READY
        )

    rule_applied = _rule_baseline_applied(case.get("rule_baseline"))
    expected_outcome = case["expected_outcome"]
    resolved = bm25_complete or rule_applied or planner_ready
    candidate_gap = expected_outcome == "chain" and not resolved
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "expected_outcome": expected_outcome,
        "bm25_retrieved": list(retrieved_ids),
        "bm25_complete_chain": bm25_complete,
        "query_route": route.value,
        "planner_ready": planner_ready,
        "rule_applied": rule_applied,
        "resolved_by_existing_baseline": resolved,
        "candidate_graph_gap": candidate_gap,
    }


def _rule_baseline_applied(payload: dict[str, Any] | None) -> bool:
    if payload is None:
        return False
    rule_set = RuleSet(
        schema_version=1,
        rules=tuple(_parse_rule(item) for item in payload["rules"]),
    )
    query_payload = payload["query"]
    result = DeterministicRuleEngine(rule_set).resolve(
        RuleQuery(
            subject=query_payload["subject"],
            action=query_payload["action"],
            reference_date=date.fromisoformat(query_payload["reference_date"]),
            attributes=tuple(sorted(query_payload.get("attributes", {}).items())),
        )
    )
    return result.status is RuleResolutionStatus.APPLIED


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
