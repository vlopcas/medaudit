"""Evaluate bounded in-memory traversal on reviewed synthetic relations."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.evaluation.query_understanding import verify_input
from medaudit.graph import (
    GraphEdge,
    GraphEntity,
    InMemoryKnowledgeGraph,
    TraversalDirection,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "graph-traversal-development-v1"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported graph traversal schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("graph traversal cases are required")
    return cases


def evaluate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes = [_evaluate_case(case) for case in cases]
    gap_cases = [item for item in outcomes if item["baseline_gap"]]
    return {
        "schema_version": 1,
        "policy": _POLICY,
        "case_count": len(outcomes),
        "metrics": {
            "exact_match": sum(item["passed"] for item in outcomes) / len(outcomes),
            "candidate_gap_recovery": (
                sum(item["passed"] for item in gap_cases) / len(gap_cases)
            ),
            "provenance_complete": all(
                item["provenance_complete"] for item in outcomes
            ),
        },
        "cases": outcomes,
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    graph = InMemoryKnowledgeGraph(
        entities=tuple(
            GraphEntity(
                entity_id=item["entity_id"],
                entity_type=item["entity_type"],
                aliases=tuple(item.get("aliases", [])),
            )
            for item in case["entities"]
        ),
        edges=tuple(
            GraphEdge(
                source_id=item["source_id"],
                relation=item["relation"],
                target_id=item["target_id"],
                document_id=item["document_id"],
                chunk_id=item["chunk_id"],
            )
            for item in case["edges"]
        ),
    )
    actual_queries = []
    provenance_complete = True
    for query in case["queries"]:
        result = graph.find_path(
            query["start"],
            query["target"],
            direction=TraversalDirection(query.get("direction", "forward")),
            max_hops=query.get("max_hops", 4),
        )
        path_chunks = (
            [edge.chunk_id for edge in result.path.edges] if result.path else []
        )
        if result.path:
            provenance_complete = provenance_complete and all(
                edge.document_id and edge.chunk_id for edge in result.path.edges
            )
        actual_queries.append(
            {
                "status": result.status.value,
                "path_chunks": path_chunks,
                "ambiguous_references": list(result.ambiguous_references),
            }
        )
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "baseline_gap": case["baseline_gap"],
        "passed": actual_queries == case["expected"],
        "provenance_complete": provenance_complete,
        "queries": actual_queries,
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
