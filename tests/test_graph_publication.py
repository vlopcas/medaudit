import unittest

from medaudit.graph import (
    GraphAdmissionResult,
    GraphCatalogDraft,
    GraphEdgeCandidate,
    GraphEntityCandidate,
    GraphPublicationCode,
    GraphPublicationStatus,
    GraphRelationPolicy,
    admit_graph_catalog,
    publish_graph_catalog,
)

POLICY = GraphRelationPolicy(
    "publication-test-policy", 1, frozenset({"regulated_by", "requires"})
)


def admitted(
    *,
    entities: tuple[GraphEntityCandidate, ...] | None = None,
    edges: tuple[GraphEdgeCandidate, ...] | None = None,
    relation_policy: GraphRelationPolicy = POLICY,
) -> GraphAdmissionResult:
    return admit_graph_catalog(
        GraphCatalogDraft(
            entities=entities
            or (
                GraphEntityCandidate("PROC-A", "procedure"),
                GraphEntityCandidate("RULE-A", "rule"),
            ),
            edges=edges
            if edges is not None
            else (
                GraphEdgeCandidate(
                    "PROC-A", "regulated_by", "RULE-A", "doc-a", "chunk-a"
                ),
            ),
        ),
        relation_policy=relation_policy,
    )


class GraphPublicationTest(unittest.TestCase):
    def test_initial_publication_is_ordered_and_deterministic(self) -> None:
        admission = admitted(
            entities=(
                GraphEntityCandidate("RULE-A", "rule"),
                GraphEntityCandidate("PROC-A", "procedure"),
            )
        )

        first = publish_graph_catalog(admission, version=1)
        repeated = publish_graph_catalog(admission, version=1)

        self.assertEqual(first.status, GraphPublicationStatus.PUBLISHED)
        assert first.catalog is not None
        assert repeated.catalog is not None
        self.assertEqual(first.catalog.publication_id, repeated.catalog.publication_id)
        self.assertEqual(first.catalog.entities[0].entity_id, "PROC-A")

    def test_non_admitted_catalog_is_not_published(self) -> None:
        admission = admit_graph_catalog(
            GraphCatalogDraft(
                entities=(
                    GraphEntityCandidate("ITEM-A", "item", ("ALFA",)),
                    GraphEntityCandidate("ITEM-B", "item", ("alfa",)),
                ),
                edges=(),
            ),
            relation_policy=POLICY,
        )

        result = publish_graph_catalog(admission, version=1)

        self.assertEqual(result.status, GraphPublicationStatus.REVIEW)
        self.assertEqual(result.code, GraphPublicationCode.CATALOG_NOT_ADMITTED)

    def test_initial_version_must_be_one(self) -> None:
        result = publish_graph_catalog(admitted(), version=2)

        self.assertEqual(result.status, GraphPublicationStatus.BLOCKED)
        self.assertEqual(result.code, GraphPublicationCode.INITIAL_VERSION_INVALID)

    def test_subsequent_version_must_increment_by_one(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        assert first.catalog is not None

        result = publish_graph_catalog(
            admitted(), version=3, previous=first.catalog
        )

        self.assertEqual(result.status, GraphPublicationStatus.BLOCKED)
        self.assertEqual(result.code, GraphPublicationCode.VERSION_NOT_MONOTONIC)

    def test_addition_is_published_without_destructive_review(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        assert first.catalog is not None
        expanded = admitted(
            entities=(
                GraphEntityCandidate("PROC-A", "procedure"),
                GraphEntityCandidate("RULE-A", "rule"),
                GraphEntityCandidate("COND-A", "condition"),
            ),
            edges=(
                GraphEdgeCandidate(
                    "PROC-A", "regulated_by", "RULE-A", "doc-a", "chunk-a"
                ),
                GraphEdgeCandidate(
                    "RULE-A", "requires", "COND-A", "doc-b", "chunk-b"
                ),
            ),
        )

        result = publish_graph_catalog(expanded, version=2, previous=first.catalog)

        self.assertEqual(result.status, GraphPublicationStatus.PUBLISHED)

    def test_relation_policy_change_requires_snapshot_bound_review(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        assert first.catalog is not None
        changed_policy = GraphRelationPolicy(
            "publication-test-policy",
            2,
            frozenset({"regulated_by", "requires", "supersedes"}),
        )
        current = admitted(relation_policy=changed_policy)
        change = f"relation-policy:{POLICY.policy_id}"

        pending = publish_graph_catalog(
            current, version=2, previous=first.catalog
        )
        published = publish_graph_catalog(
            current,
            version=2,
            previous=first.catalog,
            reviewed_changes=frozenset({change}),
            review_previous_publication_id=first.catalog.publication_id,
        )

        self.assertEqual(pending.status, GraphPublicationStatus.REVIEW)
        self.assertEqual(pending.affected_changes, (change,))
        self.assertEqual(published.status, GraphPublicationStatus.PUBLISHED)
        assert published.catalog is not None
        self.assertEqual(
            published.catalog.relation_policy_id, changed_policy.policy_id
        )

    def test_relation_policy_identity_changes_publication_identity(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        alternate = GraphRelationPolicy(
            "alternate-publication-policy",
            1,
            POLICY.allowed_relations,
        )
        second = publish_graph_catalog(
            admitted(relation_policy=alternate), version=1
        )

        assert first.catalog is not None
        assert second.catalog is not None
        self.assertNotEqual(
            first.catalog.publication_id, second.catalog.publication_id
        )

    def test_removal_requires_snapshot_bound_review(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        assert first.catalog is not None
        reduced = admitted(edges=())

        pending = publish_graph_catalog(
            reduced, version=2, previous=first.catalog
        )
        change = "edge:PROC-A|regulated_by|RULE-A|doc-a|chunk-a"
        published = publish_graph_catalog(
            reduced,
            version=2,
            previous=first.catalog,
            reviewed_changes=frozenset({change}),
            review_previous_publication_id=first.catalog.publication_id,
        )

        self.assertEqual(pending.status, GraphPublicationStatus.REVIEW)
        self.assertEqual(pending.affected_changes, (change,))
        self.assertEqual(published.status, GraphPublicationStatus.PUBLISHED)

    def test_entity_mutation_requires_review(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        assert first.catalog is not None
        mutated = admitted(
            entities=(
                GraphEntityCandidate("PROC-A", "procedure", ("NOVO ALIAS",)),
                GraphEntityCandidate("RULE-A", "rule"),
            )
        )

        result = publish_graph_catalog(mutated, version=2, previous=first.catalog)

        self.assertEqual(result.status, GraphPublicationStatus.REVIEW)
        self.assertEqual(result.affected_changes, ("entity:PROC-A",))

    def test_provenance_mutation_requires_review(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        assert first.catalog is not None
        mutated = admitted(
            edges=(
                GraphEdgeCandidate(
                    "PROC-A", "regulated_by", "RULE-A", "doc-new", "chunk-new"
                ),
            )
        )

        result = publish_graph_catalog(mutated, version=2, previous=first.catalog)

        self.assertEqual(result.status, GraphPublicationStatus.REVIEW)
        self.assertEqual(
            result.affected_changes,
            ("edge:PROC-A|regulated_by|RULE-A|doc-a|chunk-a",),
        )

    def test_stale_change_review_is_rejected(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        assert first.catalog is not None

        with self.assertRaisesRegex(ValueError, "current changes"):
            publish_graph_catalog(
                admitted(),
                version=2,
                previous=first.catalog,
                reviewed_changes=frozenset({"entity:STALE"}),
                review_previous_publication_id=first.catalog.publication_id,
            )

    def test_review_for_stale_snapshot_is_rejected(self) -> None:
        first = publish_graph_catalog(admitted(), version=1)
        assert first.catalog is not None
        reduced = admitted(edges=())
        change = "edge:PROC-A|regulated_by|RULE-A|doc-a|chunk-a"

        with self.assertRaisesRegex(ValueError, "previous publication"):
            publish_graph_catalog(
                reduced,
                version=2,
                previous=first.catalog,
                reviewed_changes=frozenset({change}),
                review_previous_publication_id="stale-publication",
            )


if __name__ == "__main__":
    unittest.main()
