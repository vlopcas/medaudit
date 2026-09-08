"""Deterministic validation for document catalog metadata."""

from medaudit.catalog.models import Catalog, ReviewStatus


def validate_catalog(catalog: Catalog) -> None:
    """Validate identity, temporal metadata and supersession relationships."""
    if catalog.schema_version != 1:
        raise ValueError(f"unsupported catalog schema: {catalog.schema_version}")
    ids = [entry.document_id for entry in catalog.entries]
    hashes = [entry.content_sha256 for entry in catalog.entries]
    _reject_duplicates(ids, "document_id")
    _reject_duplicates(hashes, "content_sha256")
    known_ids = set(ids)

    for entry in catalog.entries:
        if len(entry.content_sha256) != 64:
            raise ValueError(f"invalid SHA-256 for {entry.document_id}")
        if entry.size_bytes < 0:
            raise ValueError(f"negative file size for {entry.document_id}")
        if not entry.relative_paths:
            raise ValueError(f"missing local path for {entry.document_id}")
        if entry.effective_from and entry.effective_until:
            if entry.effective_until < entry.effective_from:
                raise ValueError(f"invalid effective period for {entry.document_id}")
        if entry.review_status is ReviewStatus.REVIEWED:
            required = {
                "title": entry.title,
                "family": entry.family,
                "organization": entry.organization,
                "version": entry.version,
                "effective_from": entry.effective_from,
            }
            missing = sorted(name for name, value in required.items() if not value)
            if missing:
                fields = ", ".join(missing)
                raise ValueError(
                    f"reviewed entry {entry.document_id} is missing: {fields}"
                )
        unknown = set(entry.supersedes) - known_ids
        if unknown:
            values = ", ".join(sorted(unknown))
            raise ValueError(f"{entry.document_id} supersedes unknown ids: {values}")
        if entry.document_id in entry.supersedes:
            raise ValueError(f"{entry.document_id} cannot supersede itself")

    graph = {entry.document_id: entry.supersedes for entry in catalog.entries}
    _reject_cycles(graph)


def _reject_duplicates(values: list[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"duplicate {label}: {value}")
        seen.add(value)


def _reject_cycles(graph: dict[str, tuple[str, ...]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(document_id: str) -> None:
        if document_id in visiting:
            raise ValueError("supersession relationship contains a cycle")
        if document_id in visited:
            return
        visiting.add(document_id)
        for target in graph[document_id]:
            visit(target)
        visiting.remove(document_id)
        visited.add(document_id)

    for document_id in graph:
        visit(document_id)
