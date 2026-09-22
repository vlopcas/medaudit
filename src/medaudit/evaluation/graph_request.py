"""Evaluate conservative compilation of explicit graph traversal requests."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from medaudit.evaluation.query_understanding import verify_input
from medaudit.graph import ExplicitGraphRequestCompiler, GraphEntity

_NOTICE = "Conteúdo integralmente sintético, sem reprodução de documentos reais."
_POLICY = "graph-request-development-v1"


def load_dataset(path: Path) -> dict[str, Any]:
    payload = cast(
        dict[str, Any], json.loads(path.read_text(encoding="utf-8"))
    )
    if (
        payload.get("schema_version") != 1
        or payload.get("policy") != _POLICY
        or payload.get("notice") != _NOTICE
    ):
        raise ValueError("unsupported graph request schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("graph request cases are required")
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("graph request case ids must be unique")
    return payload


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    compiler = ExplicitGraphRequestCompiler(
        entities=tuple(
            GraphEntity(
                entity_id=item["entity_id"],
                entity_type=item["entity_type"],
                aliases=tuple(item.get("aliases", [])),
            )
            for item in payload["entities"]
        )
    )
    outcomes = []
    for case in payload["cases"]:
        result = compiler.compile(case["query"])
        actual: dict[str, Any] = {
            "status": result.status.value,
            "review_references": list(result.review_references),
        }
        if result.request is not None:
            actual["request"] = {
                "start_id": result.request.start_id,
                "target_id": result.request.target_id,
                "direction": result.request.direction.value,
                "max_hops": result.request.max_hops,
            }
        outcomes.append(
            {
                "case_id": case["case_id"],
                "passed": actual == case["expected"],
                "actual": actual,
            }
        )
    return {
        "schema_version": 1,
        "policy": _POLICY,
        "case_count": len(outcomes),
        "metrics": {
            "exact_match": sum(item["passed"] for item in outcomes)
            / len(outcomes)
        },
        "cases": outcomes,
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
