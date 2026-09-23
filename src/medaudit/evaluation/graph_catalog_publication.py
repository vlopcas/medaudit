"""Evaluate versioned publication of admitted synthetic graph catalogs."""

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
    GraphRelationPolicy,
    PublishedGraphCatalog,
    admit_graph_catalog,
    publish_graph_catalog,
)

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "graph-catalog-publication-development-v1"


def load_dataset(path: Path) -> dict[str, Any]:
    payload = cast(
        dict[str, Any], json.loads(path.read_text(encoding="utf-8"))
    )
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported graph catalog publication schema")
    cases = payload.get("cases")
    relations = payload.get("allowed_relations")
    if not isinstance(cases, list) or not cases:
        raise ValueError("graph catalog publication cases are required")
    if not isinstance(relations, list) or not relations:
        raise ValueError("allowed graph relations are required")
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("graph catalog publication case ids must be unique")
    return payload


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    relation_policy = _relation_policy(payload)
    outcomes = [
        _evaluate_case(case, relation_policy=relation_policy)
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
    case: dict[str, Any], *, relation_policy: GraphRelationPolicy
) -> dict[str, Any]:
    previous_policy = relation_policy
    if "previous_relation_policy" in case:
        previous_policy = _relation_policy(case["previous_relation_policy"])
    previous = _previous_catalog(case, relation_policy=previous_policy)
    admission = admit_graph_catalog(
        _parse_draft(case["current"]), relation_policy=relation_policy
    )
    review_reference = case.get("review_snapshot")
    if review_reference == "previous":
        if previous is None:
            raise ValueError("synthetic case cannot reference missing snapshot")
        review_reference = previous.publication_id
    reviewed_changes = set(case.get("reviewed_changes", []))
    if "$previous_relation_policy" in reviewed_changes:
        if previous is None:
            raise ValueError("synthetic case cannot review missing policy")
        reviewed_changes.remove("$previous_relation_policy")
        reviewed_changes.add(f"relation-policy:{previous.relation_policy_id}")
    try:
        result = publish_graph_catalog(
            admission,
            version=case["version"],
            previous=previous,
            reviewed_changes=frozenset(reviewed_changes),
            review_previous_publication_id=review_reference,
        )
        actual = {
            "status": result.status.value,
            "code": result.code.value,
            "affected_count": len(result.affected_changes),
            "published_version": result.catalog.version if result.catalog else None,
        }
    except ValueError:
        actual = {
            "status": "error",
            "code": "invalid_review",
            "affected_count": 0,
            "published_version": None,
        }
    return {"case_id": case["case_id"], "passed": actual == case["expected"], **actual}


def _previous_catalog(
    case: dict[str, Any], *, relation_policy: GraphRelationPolicy
) -> PublishedGraphCatalog | None:
    previous_payload = case.get("previous")
    if previous_payload is None:
        return None
    admission = admit_graph_catalog(
        _parse_draft(previous_payload), relation_policy=relation_policy
    )
    result = publish_graph_catalog(
        admission, version=case.get("previous_version", 1)
    )
    if result.catalog is None:
        raise ValueError("previous synthetic graph catalog must be publishable")
    return result.catalog


def _relation_policy(payload: dict[str, Any]) -> GraphRelationPolicy:
    policy = payload if "name" in payload else payload.get("relation_policy")
    if policy is None:
        return GraphRelationPolicy(
            name=str(payload.get("policy", _POLICY)),
            version=1,
            allowed_relations=frozenset(payload["allowed_relations"]),
        )
    return GraphRelationPolicy(
        name=policy["name"],
        version=policy["version"],
        allowed_relations=frozenset(policy["allowed_relations"]),
    )


def _parse_draft(payload: dict[str, Any]) -> GraphCatalogDraft:
    return GraphCatalogDraft(
        entities=tuple(
            GraphEntityCandidate(
                entity_id=item["entity_id"],
                entity_type=item["entity_type"],
                aliases=tuple(item.get("aliases", [])),
            )
            for item in payload["entities"]
        ),
        edges=tuple(
            GraphEdgeCandidate(
                source_id=item["source_id"],
                relation=item["relation"],
                target_id=item["target_id"],
                document_id=item["document_id"],
                chunk_id=item["chunk_id"],
            )
            for item in payload["edges"]
        ),
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
