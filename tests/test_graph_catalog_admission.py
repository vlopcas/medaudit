import unittest

from medaudit.graph import (
    GraphAdmissionStatus,
    GraphAuditCode,
    GraphCatalogDraft,
    GraphEdgeCandidate,
    GraphEntityCandidate,
    GraphRelationPolicy,
    admit_graph_catalog,
)

POLICY = GraphRelationPolicy(
    "catalog-test-policy", 1, frozenset({"regulated_by", "requires"})
)


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
    def test_relation_policy_identity_is_deterministic_and_order_independent(
        self,
    ) -> None:
        reordered = GraphRelationPolicy(
            "catalog-test-policy",
            1,
            frozenset({"requires", "regulated_by"}),
        )

        self.assertEqual(POLICY.policy_id, reordered.policy_id)

    def test_relation_policy_requires_versioned_non_empty_allowlist(self) -> None:
        with self.assertRaisesRegex(ValueError, "name and version"):
            GraphRelationPolicy("", 1, frozenset({"requires"}))
        with self.assertRaisesRegex(ValueError, "non-empty"):
            GraphRelationPolicy("catalog-test-policy", 1, frozenset())

    def test_clean_catalog_is_admitted_as_executable_graph(self) -> None:
        result = admit_graph_catalog(clean_draft(), relation_policy=POLICY)

        self.assertEqual(result.status, GraphAdmissionStatus.ADMITTED)
        self.assertIsNotNone(result.graph)
        self.assertEqual(result.relation_policy_id, POLICY.policy_id)

    def test_orphan_edge_is_rejected(self) -> None:
        draft = GraphCatalogDraft(
            entities=(GraphEntityCandidate("PROC-A", "procedure"),),
            edges=(
                GraphEdgeCandidate(
                    "PROC-A", "regulated_by", "MISSING", "doc-a", "chunk-a"
                ),
            ),
        )

        result = admit_graph_catalog(draft, relation_policy=POLICY)

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

        result = admit_graph_catalog(draft, relation_policy=POLICY)

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

        result = admit_graph_catalog(draft, relation_policy=POLICY)

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

        result = admit_graph_catalog(draft, relation_policy=POLICY)

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

        result = admit_graph_catalog(draft, relation_policy=POLICY)

        self.assertEqual(result.status, GraphAdmissionStatus.REVIEW)
        self.assertEqual(result.findings[0].code, GraphAuditCode.DUPLICATE_EDGE)


if __name__ == "__main__":
    unittest.main()
