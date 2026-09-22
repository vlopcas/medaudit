"""Typed contracts for reviewed synthetic graph traversal."""

from dataclasses import dataclass
from enum import StrEnum


class TraversalDirection(StrEnum):
    """Allowed direction for one bounded traversal."""

    FORWARD = "forward"
    REVERSE = "reverse"


class TraversalStatus(StrEnum):
    """Closed outcomes for exact-entity graph traversal."""

    PATH_FOUND = "path_found"
    NO_PATH = "no_path"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class GraphEntity:
    """Reviewed entity with explicit aliases."""

    entity_id: str
    entity_type: str
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.entity_id or not self.entity_type:
            raise ValueError("graph entity id and type are required")
        if any(not alias for alias in self.aliases):
            raise ValueError("graph entity aliases cannot be empty")


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """Reviewed directed relation with source provenance."""

    source_id: str
    relation: str
    target_id: str
    document_id: str
    chunk_id: str

    def __post_init__(self) -> None:
        if not all(
            (
                self.source_id,
                self.relation,
                self.target_id,
                self.document_id,
                self.chunk_id,
            )
        ):
            raise ValueError("graph edge and provenance fields are required")
        if self.source_id == self.target_id:
            raise ValueError("graph self edges are not supported")


@dataclass(frozen=True, slots=True)
class TraversalPath:
    """One ordered path with provenance preserved on every edge."""

    entity_ids: tuple[str, ...]
    edges: tuple[GraphEdge, ...]

    def __post_init__(self) -> None:
        if len(self.entity_ids) != len(self.edges) + 1:
            raise ValueError("path entities and edges are inconsistent")


@dataclass(frozen=True, slots=True)
class TraversalResult:
    """Result for one exact start and target reference."""

    status: TraversalStatus
    path: TraversalPath | None
    ambiguous_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        found = self.status is TraversalStatus.PATH_FOUND
        if found != (self.path is not None):
            raise ValueError("only path-found results may carry a path")
        if self.status is TraversalStatus.REVIEW and not self.ambiguous_references:
            raise ValueError("review result requires ambiguous references")
        if self.status is not TraversalStatus.REVIEW and self.ambiguous_references:
            raise ValueError("only review results may carry ambiguous references")
