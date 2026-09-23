"""Explicit fail-closed boundary for graph-assisted evidence retrieval."""

from dataclasses import dataclass
from enum import StrEnum

from medaudit.graph.models import TraversalPath, TraversalStatus
from medaudit.graph.request import (
    ExplicitGraphRequestCompiler,
    GraphRequestStatus,
)
from medaudit.graph.traversal import InMemoryKnowledgeGraph


class GraphGatewayStatus(StrEnum):
    """Closed outcomes exposed by the graph-assisted retrieval boundary."""

    PATH_FOUND = "path_found"
    NO_PATH = "no_path"
    NOT_APPLICABLE = "not_applicable"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class GraphGatewayResult:
    """Evidence path or a closed non-retrieval outcome."""

    status: GraphGatewayStatus
    path: TraversalPath | None = None
    review_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        found = self.status is GraphGatewayStatus.PATH_FOUND
        if found != (self.path is not None):
            raise ValueError("only path-found gateway results may carry a path")
        review = self.status is GraphGatewayStatus.REVIEW
        if review != bool(self.review_references):
            raise ValueError("review gateway results require review references")


@dataclass(frozen=True, slots=True)
class ExplicitGraphGateway:
    """Compile an explicit request before allowing bounded traversal."""

    graph: InMemoryKnowledgeGraph

    def retrieve(self, query: str) -> GraphGatewayResult:
        compilation = ExplicitGraphRequestCompiler(self.graph.entities).compile(query)
        if compilation.status is GraphRequestStatus.NOT_APPLICABLE:
            return GraphGatewayResult(GraphGatewayStatus.NOT_APPLICABLE)
        if compilation.status is GraphRequestStatus.REVIEW:
            return GraphGatewayResult(
                GraphGatewayStatus.REVIEW,
                review_references=compilation.review_references,
            )

        request = compilation.request
        if request is None:  # pragma: no cover - protected by typed invariants
            raise RuntimeError("ready graph compilation omitted its request")
        traversal = self.graph.find_path(
            request.start_id,
            request.target_id,
            direction=request.direction,
            max_hops=request.max_hops,
        )
        if traversal.status is TraversalStatus.PATH_FOUND:
            return GraphGatewayResult(
                GraphGatewayStatus.PATH_FOUND,
                path=traversal.path,
            )
        if traversal.status is TraversalStatus.REVIEW:
            return GraphGatewayResult(
                GraphGatewayStatus.REVIEW,
                review_references=traversal.ambiguous_references,
            )
        return GraphGatewayResult(GraphGatewayStatus.NO_PATH)
