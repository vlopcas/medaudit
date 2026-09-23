"""Compare BM25 and explicit graph-assisted retrieval on identical queries."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from medaudit.documents import Chunk
from medaudit.evaluation.query_understanding import verify_input
from medaudit.graph import (
    ExplicitGraphGateway,
    GraphEdge,
    GraphEntity,
    InMemoryKnowledgeGraph,
)
from medaudit.retrieval import BM25Index

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "graph-assisted-retrieval-development-v1"
_HOLDOUT_POLICY = "graph-assisted-retrieval-holdout-v1"


def load_dataset(
    path: Path, *, expected_policy: str = _POLICY
) -> list[dict[str, Any]]:
    payload = cast(
        dict[str, Any], json.loads(path.read_text(encoding="utf-8"))
    )
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != expected_policy
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported graph-assisted retrieval schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("graph-assisted retrieval cases are required")
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("graph-assisted retrieval case ids must be unique")
    return cases


def evaluate(
    cases: list[dict[str, Any]], *, policy: str = _POLICY
) -> dict[str, Any]:
    outcomes = [_evaluate_case(case) for case in cases]
    chain_cases = [item for item in outcomes if item["expected_chain"]]
    control_cases = [item for item in outcomes if not item["expected_chain"]]
    if not chain_cases or not control_cases:
        raise ValueError("evaluation requires chain and control cases")
    return {
        "schema_version": 1,
        "policy": policy,
        "case_count": len(outcomes),
        "metrics": {
            "bm25_complete_chain_rate": sum(
                item["bm25_complete_chain"] for item in chain_cases
            )
            / len(chain_cases),
            "graph_complete_chain_rate": sum(
                item["graph_complete_chain"] for item in chain_cases
            )
            / len(chain_cases),
            "control_exact_match": sum(
                item["gateway_status_matches"] for item in control_cases
            )
            / len(control_cases),
            "graph_provenance_complete": all(
                item["graph_provenance_complete"] for item in chain_cases
            ),
            "exact_match": sum(item["passed"] for item in outcomes)
            / len(outcomes),
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
    bm25_results = BM25Index(chunks).search(case["query"], top_k=case["top_k"])
    bm25_chunks = [item.chunk.chunk_id for item in bm25_results]

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
    graph_result = ExplicitGraphGateway(graph).retrieve(case["query"])
    graph_chunks = (
        [edge.chunk_id for edge in graph_result.path.edges]
        if graph_result.path
        else []
    )
    expected_chain = case["expected_chain"]
    graph_provenance_complete = graph_result.path is None or all(
        edge.document_id and edge.chunk_id for edge in graph_result.path.edges
    )
    chain_passed = (
        not expected_chain
        or (
            graph_result.status.value == "path_found"
            and graph_chunks == expected_chain
            and graph_provenance_complete
        )
    )
    control_passed = bool(expected_chain) or (
        graph_result.status.value == case["expected_gateway_status"]
        and not graph_chunks
    )
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "expected_chain": expected_chain,
        "bm25_chunks": bm25_chunks,
        "bm25_complete_chain": bool(expected_chain)
        and set(expected_chain) <= set(bm25_chunks),
        "gateway_status": graph_result.status.value,
        "gateway_status_matches": (
            graph_result.status.value == case["expected_gateway_status"]
        ),
        "graph_chunks": graph_chunks,
        "graph_complete_chain": bool(expected_chain)
        and graph_chunks == expected_chain,
        "graph_provenance_complete": graph_provenance_complete,
        "passed": (
            graph_result.status.value == case["expected_gateway_status"]
            and chain_passed
            and control_passed
        ),
    }


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
    report["input_sha256"] = verify_input(args.dataset, args.expected_sha256)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
