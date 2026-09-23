"""Deterministic publication of admitted graph catalog snapshots."""

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum

from medaudit.graph.catalog import (
    GraphAdmissionResult,
    GraphAdmissionStatus,
)
from medaudit.graph.models import GraphEdge, GraphEntity


class GraphPublicationStatus(StrEnum):
    """Whether a graph snapshot was published or stopped fail-closed."""

    PUBLISHED = "published"
    BLOCKED = "blocked"
    REVIEW = "review"


class GraphPublicationCode(StrEnum):
    """Content-free reason for graph publication outcome."""

    PUBLISHED = "published"
    CATALOG_NOT_ADMITTED = "catalog_not_admitted"
    INITIAL_VERSION_INVALID = "initial_version_invalid"
    VERSION_NOT_MONOTONIC = "version_not_monotonic"
    DESTRUCTIVE_CHANGE_REVIEW_REQUIRED = (
        "destructive_change_review_required"
    )


@dataclass(frozen=True, slots=True)
class PublishedGraphCatalog:
    """Immutable, ordered graph snapshot with deterministic identity."""

    publication_id: str
    version: int
    previous_publication_id: str | None
    relation_policy_id: str
    entities: tuple[GraphEntity, ...]
    edges: tuple[GraphEdge, ...]

    def __post_init__(self) -> None:
        if self.version < 1 or not self.entities:
            raise ValueError("published graph version and entities are required")
        expected = _publication_id(
            self.version,
            self.previous_publication_id,
            self.relation_policy_id,
            self.entities,
            self.edges,
        )
        if self.publication_id != expected:
            raise ValueError("published graph identity does not match its content")


@dataclass(frozen=True, slots=True)
class GraphPublicationResult:
    """Publication outcome with admission evidence and pending changes."""

    status: GraphPublicationStatus
    code: GraphPublicationCode
    admission: GraphAdmissionResult
    catalog: PublishedGraphCatalog | None
    affected_changes: tuple[str, ...]

    def __post_init__(self) -> None:
        published = self.status is GraphPublicationStatus.PUBLISHED
        if published != (self.catalog is not None):
            raise ValueError("only published outcomes may carry a graph catalog")
        if published != (self.code is GraphPublicationCode.PUBLISHED):
            raise ValueError("graph publication status and code are inconsistent")


def publish_graph_catalog(
    admission: GraphAdmissionResult,
    *,
    version: int,
    previous: PublishedGraphCatalog | None = None,
    reviewed_changes: frozenset[str] = frozenset(),
    review_previous_publication_id: str | None = None,
) -> GraphPublicationResult:
    """Publish admitted graphs with snapshot-bound destructive review."""
    if admission.status is not GraphAdmissionStatus.ADMITTED:
        status = (
            GraphPublicationStatus.REVIEW
            if admission.status is GraphAdmissionStatus.REVIEW
            else GraphPublicationStatus.BLOCKED
        )
        return GraphPublicationResult(
            status,
            GraphPublicationCode.CATALOG_NOT_ADMITTED,
            admission,
            None,
            (),
        )

    graph = admission.graph
    if graph is None:  # pragma: no cover - protected by admission invariants
        raise RuntimeError("admitted graph catalog omitted executable graph")
    entities = tuple(sorted(graph.entities, key=_entity_sort_key))
    edges = tuple(sorted(graph.edges, key=_edge_sort_key))

    if previous is None:
        if reviewed_changes or review_previous_publication_id is not None:
            raise ValueError("initial graph publication cannot review prior changes")
        if version != 1:
            return _stopped(
                GraphPublicationStatus.BLOCKED,
                GraphPublicationCode.INITIAL_VERSION_INVALID,
                admission,
                (),
            )
        return _published(
            admission,
            version,
            None,
            admission.relation_policy_id,
            entities,
            edges,
        )

    if version != previous.version + 1:
        return _stopped(
            GraphPublicationStatus.BLOCKED,
            GraphPublicationCode.VERSION_NOT_MONOTONIC,
            admission,
            (),
        )

    required_changes = _destructive_changes(
        previous, admission.relation_policy_id, entities, edges
    )
    if not reviewed_changes <= required_changes:
        raise ValueError("reviewed graph changes must reference current changes")
    if reviewed_changes and review_previous_publication_id != previous.publication_id:
        raise ValueError("graph change review must reference previous publication")
    if not reviewed_changes and review_previous_publication_id is not None:
        raise ValueError("graph publication reference requires reviewed changes")

    pending = required_changes - reviewed_changes
    if pending:
        return _stopped(
            GraphPublicationStatus.REVIEW,
            GraphPublicationCode.DESTRUCTIVE_CHANGE_REVIEW_REQUIRED,
            admission,
            tuple(sorted(pending)),
        )
    return _published(
        admission,
        version,
        previous.publication_id,
        admission.relation_policy_id,
        entities,
        edges,
    )


def _destructive_changes(
    previous: PublishedGraphCatalog,
    relation_policy_id: str,
    entities: tuple[GraphEntity, ...],
    edges: tuple[GraphEdge, ...],
) -> frozenset[str]:
    current_entities = {entity.entity_id: entity for entity in entities}
    entity_changes = {
        f"entity:{entity.entity_id}"
        for entity in previous.entities
        if current_entities.get(entity.entity_id) != entity
    }
    current_edges = set(edges)
    edge_changes = {
        _edge_reference(edge) for edge in previous.edges if edge not in current_edges
    }
    policy_changes = (
        {f"relation-policy:{previous.relation_policy_id}"}
        if previous.relation_policy_id != relation_policy_id
        else set()
    )
    return frozenset(entity_changes | edge_changes | policy_changes)


def _published(
    admission: GraphAdmissionResult,
    version: int,
    previous_publication_id: str | None,
    relation_policy_id: str,
    entities: tuple[GraphEntity, ...],
    edges: tuple[GraphEdge, ...],
) -> GraphPublicationResult:
    catalog = PublishedGraphCatalog(
        publication_id=_publication_id(
            version,
            previous_publication_id,
            relation_policy_id,
            entities,
            edges,
        ),
        version=version,
        previous_publication_id=previous_publication_id,
        relation_policy_id=relation_policy_id,
        entities=entities,
        edges=edges,
    )
    return GraphPublicationResult(
        GraphPublicationStatus.PUBLISHED,
        GraphPublicationCode.PUBLISHED,
        admission,
        catalog,
        (),
    )


def _stopped(
    status: GraphPublicationStatus,
    code: GraphPublicationCode,
    admission: GraphAdmissionResult,
    changes: tuple[str, ...],
) -> GraphPublicationResult:
    return GraphPublicationResult(status, code, admission, None, changes)


def _publication_id(
    version: int,
    previous_publication_id: str | None,
    relation_policy_id: str,
    entities: tuple[GraphEntity, ...],
    edges: tuple[GraphEdge, ...],
) -> str:
    payload = {
        "version": version,
        "previous_publication_id": previous_publication_id,
        "relation_policy_id": relation_policy_id,
        "entities": [asdict(entity) for entity in entities],
        "edges": [asdict(edge) for edge in edges],
    }
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _edge_reference(edge: GraphEdge) -> str:
    return "edge:" + "|".join(
        (
            edge.source_id,
            edge.relation,
            edge.target_id,
            edge.document_id,
            edge.chunk_id,
        )
    )


def _entity_sort_key(entity: GraphEntity) -> tuple[str, str, tuple[str, ...]]:
    return entity.entity_id, entity.entity_type, entity.aliases


def _edge_sort_key(edge: GraphEdge) -> tuple[str, str, str, str, str]:
    return (
        edge.source_id,
        edge.relation,
        edge.target_id,
        edge.document_id,
        edge.chunk_id,
    )
