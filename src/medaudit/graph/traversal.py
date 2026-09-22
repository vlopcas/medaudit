"""Small deterministic in-memory graph for bounded reviewed traversal."""

from collections import deque
from dataclasses import dataclass

from medaudit.graph.models import (
    GraphEdge,
    GraphEntity,
    TraversalDirection,
    TraversalPath,
    TraversalResult,
    TraversalStatus,
)


@dataclass(frozen=True, slots=True)
class InMemoryKnowledgeGraph:
    """Traverse reviewed relations without storage or extraction dependencies."""

    entities: tuple[GraphEntity, ...]
    edges: tuple[GraphEdge, ...]

    def __post_init__(self) -> None:
        if not self.entities:
            raise ValueError("knowledge graph requires entities")
        identities = [entity.entity_id for entity in self.entities]
        if len(identities) != len(set(identities)):
            raise ValueError("graph entity ids must be unique")
        known = set(identities)
        if any(
            edge.source_id not in known or edge.target_id not in known
            for edge in self.edges
        ):
            raise ValueError("graph edges must reference known entities")

    def find_path(
        self,
        start_reference: str,
        target_reference: str,
        *,
        direction: TraversalDirection = TraversalDirection.FORWARD,
        max_hops: int = 4,
    ) -> TraversalResult:
        """Return the deterministic shortest path within a strict hop limit."""
        if not 1 <= max_hops <= 4:
            raise ValueError("graph traversal max_hops must be between 1 and 4")
        start_matches = self._resolve(start_reference)
        target_matches = self._resolve(target_reference)
        ambiguous = tuple(
            reference
            for reference, matches in (
                (start_reference, start_matches),
                (target_reference, target_matches),
            )
            if len(matches) != 1
        )
        if ambiguous:
            return TraversalResult(
                status=TraversalStatus.REVIEW,
                path=None,
                ambiguous_references=ambiguous,
            )
        start = start_matches[0]
        target = target_matches[0]
        queue: deque[tuple[str, tuple[str, ...], tuple[GraphEdge, ...]]] = deque(
            [(start, (start,), ())]
        )
        while queue:
            current, entity_ids, path_edges = queue.popleft()
            if current == target and path_edges:
                return TraversalResult(
                    status=TraversalStatus.PATH_FOUND,
                    path=TraversalPath(entity_ids=entity_ids, edges=path_edges),
                )
            if len(path_edges) == max_hops:
                continue
            for next_id, edge in self._neighbors(current, direction):
                if next_id in entity_ids:
                    continue
                queue.append(
                    (next_id, (*entity_ids, next_id), (*path_edges, edge))
                )
        return TraversalResult(status=TraversalStatus.NO_PATH, path=None)

    def _resolve(self, reference: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                entity.entity_id
                for entity in self.entities
                if reference == entity.entity_id or reference in entity.aliases
            )
        )

    def _neighbors(
        self, entity_id: str, direction: TraversalDirection
    ) -> tuple[tuple[str, GraphEdge], ...]:
        if direction is TraversalDirection.FORWARD:
            candidates = (
                (edge.target_id, edge)
                for edge in self.edges
                if edge.source_id == entity_id
            )
        else:
            candidates = (
                (edge.source_id, edge)
                for edge in self.edges
                if edge.target_id == entity_id
            )
        return tuple(
            sorted(
                candidates,
                key=lambda item: (
                    item[0],
                    item[1].relation,
                    item[1].document_id,
                    item[1].chunk_id,
                ),
            )
        )
