"""Evaluate fail-closed admission of synthetic graph catalog candidates."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from medaudit.evaluation.query_understanding import verify_input
from medaudit.graph import (
    GraphCatalogDraft,
    GraphEdgeCandidate,
    GraphEntityCandidate,
    admit_graph_catalog,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "graph-catalog-admission-development-v1"


def load_dataset(path: Path) -> dict[str, Any]:
    payload = cast(
        dict[str, Any], json.loads(path.read_text(encoding="utf-8"))
    )
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported graph catalog admission schema")
    cases = payload.get("cases")
    relations = payload.get("allowed_relations")
    if not isinstance(cases, list) or not cases:
        raise ValueError("graph catalog admission cases are required")
    if not isinstance(relations, list) or not relations:
        raise ValueError("allowed graph relations are required")
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("graph catalog admission case ids must be unique")
    return payload


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    allowed_relations = frozenset(payload["allowed_relations"])
    outcomes = [
        _evaluate_case(case, allowed_relations=allowed_relations)
        for case in payload["cases"]
    ]
    passed = sum(item["passed"] for item in outcomes)
    return {
        "schema_version": 1,
        "policy": _POLICY,
        "case_count": len(outcomes),
        "metrics": {
            "exact_match": passed / len(outcomes),
            "passed": passed,
            "total": len(outcomes),
        },
        "cases": outcomes,
    }


def _evaluate_case(
    case: dict[str, Any], *, allowed_relations: frozenset[str]
) -> dict[str, Any]:
    draft = GraphCatalogDraft(
        entities=tuple(
            GraphEntityCandidate(
                entity_id=item["entity_id"],
                entity_type=item["entity_type"],
                aliases=tuple(item.get("aliases", [])),
            )
            for item in case["entities"]
        ),
        edges=tuple(
            GraphEdgeCandidate(
                source_id=item["source_id"],
                relation=item["relation"],
                target_id=item["target_id"],
                document_id=item["document_id"],
                chunk_id=item["chunk_id"],
            )
            for item in case["edges"]
        ),
    )
    result = admit_graph_catalog(draft, allowed_relations=allowed_relations)
    actual = {
        "status": result.status.value,
        "code": result.code.value,
        "finding_codes": [finding.code.value for finding in result.findings],
        "executable": result.graph is not None,
    }
    return {"case_id": case["case_id"], "passed": actual == case["expected"], **actual}


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
