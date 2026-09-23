"""Raw reviewed candidates and fail-closed graph catalog admission."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import StrEnum

from medaudit.graph.models import GraphEdge, GraphEntity
from medaudit.graph.traversal import InMemoryKnowledgeGraph


@dataclass(frozen=True, slots=True)
class GraphEntityCandidate:
    """Entity candidate before graph invariants are trusted."""

    entity_id: str
    entity_type: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GraphEdgeCandidate:
    """Relation candidate before graph and provenance checks."""

    source_id: str
    relation: str
    target_id: str
    document_id: str
    chunk_id: str


@dataclass(frozen=True, slots=True)
class GraphCatalogDraft:
    """Untrusted candidate collection awaiting deterministic admission."""

    entities: tuple[GraphEntityCandidate, ...]
    edges: tuple[GraphEdgeCandidate, ...]


class GraphAuditSeverity(StrEnum):
    """Effect of one finding on catalog admission."""

    ERROR = "error"
    REVIEW = "review"


class GraphAuditCode(StrEnum):
    """Closed classes of graph catalog defects."""

    AMBIGUOUS_REFERENCE = "ambiguous_reference"
    DUPLICATE_EDGE = "duplicate_edge"
    DUPLICATE_ENTITY_ID = "duplicate_entity_id"
    EMPTY_CATALOG = "empty_catalog"
    EMPTY_EDGE_FIELD = "empty_edge_field"
    EMPTY_ENTITY_FIELD = "empty_entity_field"
    ORPHAN_EDGE = "orphan_edge"
    SELF_EDGE = "self_edge"
    UNKNOWN_RELATION = "unknown_relation"


@dataclass(frozen=True, slots=True)
class GraphAuditFinding:
    """Deterministic content-light finding for catalog review."""

    code: GraphAuditCode
    severity: GraphAuditSeverity
    references: tuple[str, ...]


class GraphAdmissionStatus(StrEnum):
    """Whether a candidate catalog may become executable."""

    ADMITTED = "admitted"
    REJECTED = "rejected"
    REVIEW = "review"


class GraphAdmissionCode(StrEnum):
    """Content-free reason for a graph admission outcome."""

    CLEAN_CATALOG = "clean_catalog"
    INVALID_CATALOG = "invalid_catalog"
    REVIEW_REQUIRED = "review_required"


@dataclass(frozen=True, slots=True)
class GraphAdmissionResult:
    """Admission outcome with an executable graph only when clean."""

    status: GraphAdmissionStatus
    code: GraphAdmissionCode
    findings: tuple[GraphAuditFinding, ...]
    graph: InMemoryKnowledgeGraph | None = None

    def __post_init__(self) -> None:
        admitted = self.status is GraphAdmissionStatus.ADMITTED
        if admitted != (self.graph is not None):
            raise ValueError("only admitted graph catalogs may be executable")
        if admitted != (not self.findings):
            raise ValueError("only admitted graph catalogs may be finding-free")


def audit_graph_catalog(
    draft: GraphCatalogDraft,
    *,
    allowed_relations: frozenset[str],
) -> tuple[GraphAuditFinding, ...]:
    """Audit raw graph candidates without constructing executable models."""
    if not allowed_relations or any(not relation for relation in allowed_relations):
        raise ValueError("allowed graph relations must be non-empty")

    findings: list[GraphAuditFinding] = []
    if not draft.entities:
        findings.append(
            GraphAuditFinding(
                GraphAuditCode.EMPTY_CATALOG,
                GraphAuditSeverity.ERROR,
                ("entities",),
            )
        )

    entity_counts = Counter(entity.entity_id for entity in draft.entities)
    for entity_id, count in entity_counts.items():
        if entity_id and count > 1:
            findings.append(
                GraphAuditFinding(
                    GraphAuditCode.DUPLICATE_ENTITY_ID,
                    GraphAuditSeverity.ERROR,
                    (entity_id,),
                )
            )

    reference_owners: dict[str, set[str]] = defaultdict(set)
    for entity in draft.entities:
        if not entity.entity_id or not entity.entity_type:
            findings.append(
                GraphAuditFinding(
                    GraphAuditCode.EMPTY_ENTITY_FIELD,
                    GraphAuditSeverity.ERROR,
                    (entity.entity_id or "<missing-entity-id>",),
                )
            )
        for reference in (entity.entity_id, *entity.aliases):
            if reference:
                reference_owners[reference.casefold()].add(entity.entity_id)
            else:
                findings.append(
                    GraphAuditFinding(
                        GraphAuditCode.EMPTY_ENTITY_FIELD,
                        GraphAuditSeverity.ERROR,
                        (entity.entity_id or "<missing-entity-id>",),
                    )
                )
    for reference, owners in reference_owners.items():
        if len(owners) > 1:
            findings.append(
                GraphAuditFinding(
                    GraphAuditCode.AMBIGUOUS_REFERENCE,
                    GraphAuditSeverity.REVIEW,
                    (reference, *sorted(owners)),
                )
            )

    known_ids = {entity.entity_id for entity in draft.entities if entity.entity_id}
    semantic_edges: dict[tuple[str, str, str], int] = Counter()
    for index, edge in enumerate(draft.edges, start=1):
        edge_ref = f"edge-{index}"
        if not all(
            (
                edge.source_id,
                edge.relation,
                edge.target_id,
                edge.document_id,
                edge.chunk_id,
            )
        ):
            findings.append(
                GraphAuditFinding(
                    GraphAuditCode.EMPTY_EDGE_FIELD,
                    GraphAuditSeverity.ERROR,
                    (edge_ref,),
                )
            )
        if edge.source_id not in known_ids or edge.target_id not in known_ids:
            findings.append(
                GraphAuditFinding(
                    GraphAuditCode.ORPHAN_EDGE,
                    GraphAuditSeverity.ERROR,
                    (edge_ref,),
                )
            )
        if edge.source_id and edge.source_id == edge.target_id:
            findings.append(
                GraphAuditFinding(
                    GraphAuditCode.SELF_EDGE,
                    GraphAuditSeverity.ERROR,
                    (edge_ref,),
                )
            )
        if edge.relation and edge.relation not in allowed_relations:
            findings.append(
                GraphAuditFinding(
                    GraphAuditCode.UNKNOWN_RELATION,
                    GraphAuditSeverity.REVIEW,
                    (edge_ref, edge.relation),
                )
            )
        semantic_edges[(edge.source_id, edge.relation, edge.target_id)] += 1

    for semantic_edge, count in semantic_edges.items():
        if all(semantic_edge) and count > 1:
            findings.append(
                GraphAuditFinding(
                    GraphAuditCode.DUPLICATE_EDGE,
                    GraphAuditSeverity.REVIEW,
                    semantic_edge,
                )
            )

    return tuple(
        sorted(
            findings,
            key=lambda item: (
                item.severity.value,
                item.code.value,
                item.references,
            ),
        )
    )


def admit_graph_catalog(
    draft: GraphCatalogDraft,
    *,
    allowed_relations: frozenset[str],
) -> GraphAdmissionResult:
    """Construct an executable graph only from a clean candidate catalog."""
    findings = audit_graph_catalog(draft, allowed_relations=allowed_relations)
    errors = tuple(
        finding
        for finding in findings
        if finding.severity is GraphAuditSeverity.ERROR
    )
    if errors:
        return GraphAdmissionResult(
            GraphAdmissionStatus.REJECTED,
            GraphAdmissionCode.INVALID_CATALOG,
            errors,
        )
    if findings:
        return GraphAdmissionResult(
            GraphAdmissionStatus.REVIEW,
            GraphAdmissionCode.REVIEW_REQUIRED,
            findings,
        )

    graph = InMemoryKnowledgeGraph(
        entities=tuple(
            GraphEntity(entity.entity_id, entity.entity_type, entity.aliases)
            for entity in draft.entities
        ),
        edges=tuple(
            GraphEdge(
                edge.source_id,
                edge.relation,
                edge.target_id,
                edge.document_id,
                edge.chunk_id,
            )
            for edge in draft.edges
        ),
    )
    return GraphAdmissionResult(
        GraphAdmissionStatus.ADMITTED,
        GraphAdmissionCode.CLEAN_CATALOG,
        (),
        graph,
    )
