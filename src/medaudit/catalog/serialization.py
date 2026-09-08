"""Load and serialize private catalog JSON."""

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from medaudit.catalog.models import Catalog, CatalogEntry, ReviewStatus
from medaudit.catalog.validation import validate_catalog

DATE_FIELDS = ("published_at", "effective_from", "effective_until")


def load_catalog(path: Path) -> Catalog:
    """Load and validate a private catalog."""
    with path.open(encoding="utf-8") as source:
        payload: dict[str, Any] = json.load(source)
    entries = []
    for raw_entry in payload["entries"]:
        values = dict(raw_entry)
        for field in DATE_FIELDS:
            values[field] = (
                date.fromisoformat(values[field]) if values.get(field) else None
            )
        values["relative_paths"] = tuple(values["relative_paths"])
        values["supersedes"] = tuple(values.get("supersedes", ()))
        values["review_status"] = ReviewStatus(values["review_status"])
        entries.append(CatalogEntry(**values))
    catalog = Catalog(payload["schema_version"], tuple(entries))
    validate_catalog(catalog)
    return catalog


def write_catalog(catalog: Catalog, output: Path) -> None:
    """Atomically write a catalog only to an ignored local filename."""
    if not output.name.endswith(".local.json"):
        raise ValueError("catalog output must end with .local.json")
    validate_catalog(catalog)
    payload = asdict(catalog)
    for entry in payload["entries"]:
        for field in DATE_FIELDS:
            if entry[field] is not None:
                entry[field] = entry[field].isoformat()
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)
