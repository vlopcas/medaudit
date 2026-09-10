"""Finalize approved review cases into date-specific private golden sets."""

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any


def finalize_review(
    review: dict[str, Any], default_date: date
) -> dict[date, dict[str, Any]]:
    """Validate approvals and group evaluator-compatible cases by snapshot date."""
    if review.get("schema_version") != 1:
        raise ValueError("unsupported review schema")
    if review.get("review_status") != "reviewed":
        raise ValueError("review queue is not complete")
    cases = review.get("cases", [])
    if not cases:
        raise ValueError("at least one reviewed case is required")

    grouped: defaultdict[date, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[str] = set()
    for case in cases:
        if case.get("review_status") != "approved":
            raise ValueError("all finalized cases must be approved")
        case_id = case["candidate_id"]
        if case_id in seen_ids:
            raise ValueError("duplicate reviewed case id")
        seen_ids.add(case_id)
        snapshot_date = (
            date.fromisoformat(case["reference_date"])
            if case.get("reference_date")
            else default_date
        )
        answerable = case["answerability"] == "answerable"
        relevant_documents = case.get("proposed_relevant_document_ids", [])
        if answerable and not relevant_documents:
            raise ValueError("answerable case has no relevant documents")
        grouped[snapshot_date].append(
            {
                "id": case_id,
                "question": case["question"],
                "category": case["category"],
                "relevant_document_ids": relevant_documents if answerable else [],
            }
        )

    return {
        snapshot_date: {
            "schema_version": 1,
            "reference_date": snapshot_date.isoformat(),
            "relevance_level": "document",
            "cases": grouped_cases,
        }
        for snapshot_date, grouped_cases in sorted(grouped.items())
    }


def write_golden_sets(golden_sets: dict[date, dict[str, Any]], output: Path) -> None:
    """Write private golden sets without overwriting an existing snapshot."""
    output.mkdir(parents=True, exist_ok=True)
    targets = {
        snapshot_date: output / f"retrieval-{snapshot_date.isoformat()}.local.json"
        for snapshot_date in golden_sets
    }
    if any(path.exists() for path in targets.values()):
        raise FileExistsError("a golden set already exists for a snapshot date")
    for snapshot_date, payload in golden_sets.items():
        target = targets[snapshot_date]
        rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(rendered + "\n", encoding="utf-8")
        temporary.replace(target)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--default-date", type=date.fromisoformat, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        review: dict[str, Any] = json.loads(args.review.read_text(encoding="utf-8"))
        golden_sets = finalize_review(review, args.default_date)
        write_golden_sets(golden_sets, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    print(
        json.dumps(
            {
                "case_count": sum(
                    len(payload["cases"]) for payload in golden_sets.values()
                ),
                "snapshot_count": len(golden_sets),
                "relevance_level": "document",
                "succeeded": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
