import unittest

from medaudit.graph import (
    ExplicitGraphGateway,
    GraphEdge,
    GraphEntity,
    GraphGatewayStatus,
    InMemoryKnowledgeGraph,
)


def make_gateway() -> ExplicitGraphGateway:
    return ExplicitGraphGateway(
        InMemoryKnowledgeGraph(
            entities=(
                GraphEntity("PX-A", "procedure"),
                GraphEntity("RULE-1", "rule"),
                GraphEntity("COND-9", "condition"),
                GraphEntity("ALFA-1", "item", aliases=("ALFA",)),
                GraphEntity("ALFA-2", "item", aliases=("ALFA",)),
            ),
            edges=(
                GraphEdge("PX-A", "regulated_by", "RULE-1", "doc-a", "c-1"),
                GraphEdge("RULE-1", "requires", "COND-9", "doc-b", "c-2"),
            ),
        )
    )


class ExplicitGraphGatewayTest(unittest.TestCase):
    def test_returns_provenanced_path_for_ready_request(self) -> None:
        result = make_gateway().retrieve("Qual o caminho de PX-A até COND-9?")

        self.assertEqual(result.status, GraphGatewayStatus.PATH_FOUND)
        assert result.path is not None
        self.assertEqual(
            tuple(edge.chunk_id for edge in result.path.edges), ("c-1", "c-2")
        )

    def test_returns_no_path_for_disconnected_entities(self) -> None:
        result = make_gateway().retrieve("Qual o caminho de PX-A até ALFA-1?")

        self.assertEqual(result.status, GraphGatewayStatus.NO_PATH)

    def test_propagates_ambiguous_reference_to_review(self) -> None:
        result = make_gateway().retrieve("Qual o caminho de ALFA até COND-9?")

        self.assertEqual(result.status, GraphGatewayStatus.REVIEW)
        self.assertEqual(result.review_references, ("alfa",))

    def test_does_not_activate_without_explicit_path_intent(self) -> None:
        result = make_gateway().retrieve("Compare PX-A e COND-9.")

        self.assertEqual(result.status, GraphGatewayStatus.NOT_APPLICABLE)


if __name__ == "__main__":
    unittest.main()
