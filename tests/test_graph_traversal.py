import unittest

from medaudit.graph import (
    GraphEdge,
    GraphEntity,
    InMemoryKnowledgeGraph,
    TraversalDirection,
    TraversalStatus,
)


def make_graph() -> InMemoryKnowledgeGraph:
    return InMemoryKnowledgeGraph(
        entities=(
            GraphEntity("procedure-a", "procedure", aliases=("ALPHA",)),
            GraphEntity("rule-a", "rule"),
            GraphEntity("exception-a", "exception"),
            GraphEntity("condition-a", "condition"),
            GraphEntity("procedure-b", "procedure", aliases=("ALPHA",)),
        ),
        edges=(
            GraphEdge("procedure-a", "regulated_by", "rule-a", "doc-1", "c-1"),
            GraphEdge("rule-a", "has_exception", "exception-a", "doc-2", "c-2"),
            GraphEdge(
                "exception-a", "requires", "condition-a", "doc-3", "c-3"
            ),
        ),
    )


class GraphTraversalTest(unittest.TestCase):
    def test_finds_bounded_path_with_edge_provenance(self) -> None:
        result = make_graph().find_path("procedure-a", "condition-a", max_hops=3)

        self.assertEqual(result.status, TraversalStatus.PATH_FOUND)
        assert result.path is not None
        self.assertEqual(
            tuple(edge.chunk_id for edge in result.path.edges),
            ("c-1", "c-2", "c-3"),
        )

    def test_reverse_traversal_preserves_original_edge_provenance(self) -> None:
        result = make_graph().find_path(
            "condition-a",
            "procedure-a",
            direction=TraversalDirection.REVERSE,
            max_hops=3,
        )

        self.assertEqual(result.status, TraversalStatus.PATH_FOUND)
        assert result.path is not None
        self.assertEqual(result.path.entity_ids[0], "condition-a")
        self.assertEqual(result.path.edges[0].document_id, "doc-3")

    def test_hop_limit_returns_no_path(self) -> None:
        result = make_graph().find_path("procedure-a", "condition-a", max_hops=2)

        self.assertEqual(result.status, TraversalStatus.NO_PATH)

    def test_ambiguous_alias_requires_review(self) -> None:
        result = make_graph().find_path("ALPHA", "condition-a")

        self.assertEqual(result.status, TraversalStatus.REVIEW)
        self.assertEqual(result.ambiguous_references, ("ALPHA",))

    def test_disconnected_entities_return_no_path(self) -> None:
        result = make_graph().find_path("procedure-b", "condition-a")

        self.assertEqual(result.status, TraversalStatus.NO_PATH)


if __name__ == "__main__":
    unittest.main()
