"""Fail-closed access to human-reviewed catalog entries."""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from medaudit.catalog.models import CatalogEntry, ReviewStatus
from medaudit.documents import Document


class CatalogRejection(StrEnum):
    """Stable reasons why a catalog entry cannot enter retrieval."""

    PENDING_REVIEW = "pending_review"
    MISSING_SOURCE = "missing_source"
    NOT_YET_EFFECTIVE = "not_yet_effective"
    EXPIRED = "expired"
    CONTENT_MISMATCH = "content_mismatch"


@dataclass(frozen=True, slots=True)
class CatalogAccessError(ValueError):
    """Safe rejection that does not reveal private document metadata."""

    reason: CatalogRejection

    def __str__(self) -> str:
        return f"catalog entry rejected: {self.reason.value}"


def document_from_reviewed_entry(
    entry: CatalogEntry,
    content: bytes,
    reference_date: date,
) -> Document:
    """Verify an entry and convert it to the parser-facing domain model."""
    if entry.review_status is ReviewStatus.MISSING:
        raise CatalogAccessError(CatalogRejection.MISSING_SOURCE)
    if entry.review_status is not ReviewStatus.REVIEWED:
        raise CatalogAccessError(CatalogRejection.PENDING_REVIEW)
    if entry.effective_from is None:
        raise ValueError("reviewed catalog entry is missing effective_from")
    if reference_date < entry.effective_from:
        raise CatalogAccessError(CatalogRejection.NOT_YET_EFFECTIVE)
    if entry.effective_until is not None and reference_date > entry.effective_until:
        raise CatalogAccessError(CatalogRejection.EXPIRED)

    actual_hash = hashlib.sha256(content).hexdigest()
    if not hmac.compare_digest(actual_hash, entry.content_sha256):
        raise CatalogAccessError(CatalogRejection.CONTENT_MISMATCH)

    if entry.title is None or entry.version is None:
        raise ValueError("reviewed catalog entry is missing document metadata")
    metadata = {
        "family": entry.family or "",
        "organization": entry.organization or "",
        "content_sha256": entry.content_sha256,
    }
    if entry.published_at is not None:
        metadata["published_at"] = entry.published_at.isoformat()
    return Document(
        document_id=entry.document_id,
        title=entry.title,
        version=entry.version,
        effective_from=entry.effective_from,
        effective_until=entry.effective_until,
        metadata=metadata,
    )
