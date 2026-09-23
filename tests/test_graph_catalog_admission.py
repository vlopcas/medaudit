import unittest

from medaudit.graph import (
    GraphAdmissionStatus,
    GraphAuditCode,
    GraphCatalogDraft,
    GraphEdgeCandidate,
    GraphEntityCandidate,
    admit_graph_catalog,
)

ALLOWED = frozenset({"regulated_by", "requires"})


def clean_draft() -> GraphCatalogDraft:
    return GraphCatalogDraft(
        entities=(
            GraphEntityCandidate("PROC-A", "procedure", ("PROCEDIMENTO A",)),
            GraphEntityCandidate("RULE-A", "rule"),
        ),
        edges=(
            GraphEdgeCandidate(
                "PROC-A", "regulated_by", "RULE-A", "doc-a", "chunk-a"
            ),
        ),
    )


class GraphCatalogAdmissionTest(unittest.TestCase):
    def test_clean_catalog_is_admitted_as_executable_graph(self) -> None:
        result = admit_graph_catalog(clean_draft(), allowed_relations=ALLOWED)

        self.assertEqual(result.status, GraphAdmissionStatus.ADMITTED)
        self.assertIsNotNone(result.graph)

    def test_orphan_edge_is_rejected(self) -> None:
        draft = GraphCatalogDraft(
            entities=(GraphEntityCandidate("PROC-A", "procedure"),),
            edges=(
                GraphEdgeCandidate(
                    "PROC-A", "regulated_by", "MISSING", "doc-a", "chunk-a"
                ),
            ),
        )

        result = admit_graph_catalog(draft, allowed_relations=ALLOWED)

        self.assertEqual(result.status, GraphAdmissionStatus.REJECTED)
        self.assertEqual(result.findings[0].code, GraphAuditCode.ORPHAN_EDGE)

    def test_missing_provenance_is_rejected(self) -> None:
        draft = GraphCatalogDraft(
            entities=clean_draft().entities,
            edges=(
                GraphEdgeCandidate(
                    "PROC-A", "regulated_by", "RULE-A", "", "chunk-a"
                ),
            ),
        )

        result = admit_graph_catalog(draft, allowed_relations=ALLOWED)

        self.assertEqual(result.status, GraphAdmissionStatus.REJECTED)
        self.assertEqual(result.findings[0].code, GraphAuditCode.EMPTY_EDGE_FIELD)

    def test_alias_collision_requires_review(self) -> None:
        draft = GraphCatalogDraft(
            entities=(
                GraphEntityCandidate("ITEM-A", "item", ("ALFA",)),
                GraphEntityCandidate("ITEM-B", "item", ("alfa",)),
            ),
            edges=(),
        )

        result = admit_graph_catalog(draft, allowed_relations=ALLOWED)

        self.assertEqual(result.status, GraphAdmissionStatus.REVIEW)
        self.assertEqual(
            result.findings[0].code, GraphAuditCode.AMBIGUOUS_REFERENCE
        )

    def test_unknown_relation_requires_review(self) -> None:
        draft = GraphCatalogDraft(
            entities=clean_draft().entities,
            edges=(
                GraphEdgeCandidate(
                    "PROC-A", "invented_relation", "RULE-A", "doc-a", "chunk-a"
                ),
            ),
        )

        result = admit_graph_catalog(draft, allowed_relations=ALLOWED)

        self.assertEqual(result.status, GraphAdmissionStatus.REVIEW)
        self.assertEqual(result.findings[0].code, GraphAuditCode.UNKNOWN_RELATION)

    def test_duplicate_semantic_edge_requires_review(self) -> None:
        draft = GraphCatalogDraft(
            entities=clean_draft().entities,
            edges=(
                GraphEdgeCandidate(
                    "PROC-A", "regulated_by", "RULE-A", "doc-a", "chunk-a"
                ),
                GraphEdgeCandidate(
                    "PROC-A", "regulated_by", "RULE-A", "doc-b", "chunk-b"
                ),
            ),
        )

        result = admit_graph_catalog(draft, allowed_relations=ALLOWED)

        self.assertEqual(result.status, GraphAdmissionStatus.REVIEW)
        self.assertEqual(result.findings[0].code, GraphAuditCode.DUPLICATE_EDGE)


if __name__ == "__main__":
    unittest.main()
