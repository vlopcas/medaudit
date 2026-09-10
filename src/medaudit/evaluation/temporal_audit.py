"""Audit golden-set references against reviewed document effective periods."""

import argparse
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.catalog.models import Catalog
from medaudit.catalog.serialization import load_catalog


def audit_temporal_references(
    golden_sets: list[dict[str, Any]], catalog: Catalog
) -> dict[str, Any]:
    """Return private case-level conflicts and aggregate counts."""
    by_id = {entry.document_id: entry for entry in catalog.entries}
    conflicts: list[dict[str, str]] = []
    case_count = 0
    reference_count = 0
    for golden_set in golden_sets:
        reference_date = date.fromisoformat(golden_set["reference_date"])
        for case in golden_set["cases"]:
            case_count += 1
            for document_id in case.get("relevant_document_ids", []):
                reference_count += 1
                entry = by_id.get(document_id)
                if entry is None:
                    reason = "unknown_document"
                elif (
                    entry.effective_from is None
                    or reference_date < entry.effective_from
                ):
                    reason = "not_yet_effective"
                elif (
                    entry.effective_until is not None
                    and reference_date > entry.effective_until
                ):
                    reason = "expired"
                else:
                    continue
                conflicts.append(
                    {
                        "case_id": case["id"],
                        "document_id": document_id,
                        "reference_date": reference_date.isoformat(),
                        "reason": reason,
                    }
                )
    return {
        "schema_version": 1,
        "snapshot_count": len(golden_sets),
        "case_count": case_count,
        "reference_count": reference_count,
        "conflict_count": len(conflicts),
        "ready": not conflicts,
        "conflicts": conflicts,
    }


def load_golden_sets(directory: Path) -> list[dict[str, Any]]:
    paths = sorted(directory.glob("retrieval-*.local.json"))
    if not paths:
        raise ValueError("no golden sets found")
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def write_private_audit(report: dict[str, Any], output: Path) -> None:
    if not output.name.endswith(".local.json"):
        raise ValueError("temporal audit output must end with .local.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-sets", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = audit_temporal_references(
            load_golden_sets(args.golden_sets), load_catalog(args.catalog)
        )
        write_private_audit(report, args.output)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": type(error).__name__, "ready": False}))
        return 2
    summary = {key: value for key, value in report.items() if key != "conflicts"}
    print(json.dumps(summary, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
