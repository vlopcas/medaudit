"""Prepare a private human-review queue from generated evaluation candidates."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from medaudit.catalog.models import Catalog
from medaudit.catalog.serialization import load_catalog


def prepare_review_queue(
    candidates: dict[str, Any],
    catalog: Catalog,
    existing_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map new candidates while preserving previously reviewed cases."""
    label_map: dict[str, set[str]] = {}
    for entry in catalog.entries:
        labels = [entry.title or "", *entry.relative_paths]
        for label in labels:
            for value in (label, Path(label).stem):
                normalized = _normalize(value)
                if normalized:
                    label_map.setdefault(normalized, set()).add(entry.document_id)

    review_cases = _existing_cases(existing_review)
    seen_ids = {case["candidate_id"] for case in review_cases}
    for candidate in candidates["cases"]:
        if candidate["candidate_id"] in seen_ids:
            raise ValueError("candidate id already exists in review queue")
        seen_ids.add(candidate["candidate_id"])
        source_labels = candidate.get("required_source_labels", [])
        mapped_sets = [
            label_map.get(_normalize(label), set()) for label in source_labels
        ]
        if any(len(matches) != 1 for matches in mapped_sets):
            raise ValueError("candidate source label mapping is missing or ambiguous")
        answerable = candidate["answerability"] == "answerable"
        document_ids = sorted({next(iter(matches)) for matches in mapped_sets})
        review_cases.append(
            {
                **candidate,
                "proposed_relevant_document_ids": document_ids if answerable else [],
                "review_status": "pending",
                "review_comment": None,
            }
        )
    return {
        "schema_version": 1,
        "review_status": "requires_human_review",
        "cases": review_cases,
    }


def _existing_cases(existing_review: dict[str, Any] | None) -> list[dict[str, Any]]:
    if existing_review is None:
        return []
    if existing_review.get("schema_version") != 1:
        raise ValueError("unsupported existing review schema")
    cases = existing_review.get("cases", [])
    identifiers = [case["candidate_id"] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate case id in existing review")
    return [dict(case) for case in cases]


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    ascii_value = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", ascii_value).strip()


def write_review_queue(queue: dict[str, Any], output: Path) -> None:
    if not output.name.endswith(".local.json"):
        raise ValueError("review queue output must end with .local.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--existing-review", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        candidates: dict[str, Any] = json.loads(
            args.candidates.read_text(encoding="utf-8")
        )
        existing_review: dict[str, Any] | None = (
            json.loads(args.existing_review.read_text(encoding="utf-8"))
            if args.existing_review
            else None
        )
        queue = prepare_review_queue(
            candidates, load_catalog(args.catalog), existing_review
        )
        write_review_queue(queue, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "succeeded": False}))
        return 2
    counts = Counter(case["review_status"] for case in queue["cases"])
    print(
        json.dumps(
            {"case_count": len(queue["cases"]), "status_counts": counts},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
