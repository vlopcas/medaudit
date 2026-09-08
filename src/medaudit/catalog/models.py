"""Models for human-reviewed private document metadata."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class ReviewStatus(StrEnum):
    """Human-review lifecycle for catalog entries."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Private metadata for one unique document content hash."""

    document_id: str
    content_sha256: str
    relative_paths: tuple[str, ...]
    media_type: str
    size_bytes: int
    review_status: ReviewStatus = ReviewStatus.PENDING
    title: str | None = None
    family: str | None = None
    organization: str | None = None
    version: str | None = None
    published_at: date | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    supersedes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Catalog:
    """Versioned collection of private catalog entries."""

    schema_version: int
    entries: tuple[CatalogEntry, ...]
