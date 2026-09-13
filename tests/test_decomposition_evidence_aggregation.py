import unittest
from datetime import date

from medaudit.documents import Chunk
from medaudit.query_understanding import DeterministicQueryPlanner
from medaudit.rag import (
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    group_decomposition_evidence,
)
from medaudit.retrieval import BM25Index


class DecompositionEvidenceAggregationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = DeterministicQueryPlanner()
        chunks = [
            Chunk("alpha", "document-alpha", "regra alfa sintética"),
            Chunk("beta", "document-beta", "regra beta sintética"),
        ]
        self.pipeline = EvidenceFirstPipeline(
            chunks=chunks,
            retriever=BM25Index(chunks),
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
        self.executor = DeterministicDecompositionExecutor(
            comparison_pipeline=self.pipeline,
            temporal_pipeline_for=lambda _: self.pipeline,
        )

    def test_preserves_order_context_and_citations(self) -> None:
        execution = self.executor.execute(
            self.planner.plan("Compare regra alfa com regra beta."),
            top_k=1,
        )

        bundle = group_decomposition_evidence(execution)

        self.assertTrue(bundle.can_generate)
        self.assertEqual(
            tuple(group.step.scope for group in bundle.groups),
            ("regra alfa", "regra beta"),
        )
        self.assertEqual(
            tuple(group.evidence[0].location.chunk_id for group in bundle.groups),
            ("alpha", "beta"),
        )

    def test_partial_evidence_remains_visible_but_cannot_generate(self) -> None:
        execution = self.executor.execute(
            self.planner.plan("Compare regra alfa com item inexistente."),
            top_k=1,
        )

        bundle = group_decomposition_evidence(execution)

        self.assertFalse(bundle.can_generate)
        self.assertEqual(len(bundle.groups[0].evidence), 1)
        self.assertEqual(bundle.groups[1].evidence, ())

    def test_clarification_produces_an_empty_blocked_bundle(self) -> None:
        execution = self.executor.execute(
            self.planner.plan("Faça uma comparação geral.")
        )

        bundle = group_decomposition_evidence(execution)

        self.assertFalse(bundle.can_generate)
        self.assertEqual(bundle.groups, ())

    def test_same_evidence_is_not_deduplicated_across_steps(self) -> None:
        execution = self.executor.execute(
            self.planner.plan("Compare regra alfa com regra alfa."),
            top_k=1,
        )

        bundle = group_decomposition_evidence(execution)

        self.assertEqual(len(bundle.groups), 2)
        self.assertEqual(
            [group.evidence[0].location.chunk_id for group in bundle.groups],
            ["alpha", "alpha"],
        )

    def test_temporal_context_remains_attached_to_each_group(self) -> None:
        execution = self.executor.execute(
            self.planner.plan(
                "Compare regra alfa em 2026-01-01 e 2026-07-01."
            ),
            top_k=1,
        )

        bundle = group_decomposition_evidence(execution)

        self.assertEqual(
            tuple(group.step.reference_date for group in bundle.groups),
            (date(2026, 1, 1), date(2026, 7, 1)),
        )
