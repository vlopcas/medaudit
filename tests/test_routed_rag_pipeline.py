import unittest

from medaudit.documents import Chunk
from medaudit.query_understanding import QueryRoute
from medaudit.rag import (
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    RoutedEvidenceFirstPipeline,
)
from medaudit.retrieval import BM25Index


class RoutedEvidenceFirstPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        chunks = [Chunk("chunk-a", "document-a", "synthetic rule alpha")]
        evidence_pipeline = EvidenceFirstPipeline(
            chunks=chunks,
            retriever=BM25Index(chunks),
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
        self.pipeline = RoutedEvidenceFirstPipeline(evidence_pipeline)

    def test_direct_route_contains_retrieval_decision(self) -> None:
        decision = self.pipeline.retrieve("Qual é a regra alpha?")

        self.assertEqual(decision.route, QueryRoute.DIRECT_RETRIEVAL)
        self.assertIsNotNone(decision.retrieval)

    def test_comparison_stops_before_retrieval(self) -> None:
        decision = self.pipeline.retrieve("Compare a regra alpha com a beta.")

        self.assertEqual(decision.route, QueryRoute.REQUIRES_DECOMPOSITION)
        self.assertIsNone(decision.retrieval)
        self.assertIsNotNone(decision.plan)
        assert decision.plan is not None
        self.assertEqual(len(decision.plan.steps), 2)

    def test_ambiguous_comparison_returns_clarification_plan(self) -> None:
        decision = self.pipeline.retrieve("Faça uma comparação geral.")

        self.assertEqual(decision.route, QueryRoute.REQUIRES_DECOMPOSITION)
        self.assertIsNone(decision.retrieval)
        self.assertIsNotNone(decision.plan)
        assert decision.plan is not None
        self.assertEqual(decision.plan.status, "needs_clarification")

    def test_external_dependency_stops_before_retrieval(self) -> None:
        decision = self.pipeline.retrieve(
            "Consulte o preço atual no portal externo."
        )

        self.assertEqual(decision.route, QueryRoute.REQUIRES_EXTERNAL_DATA)
        self.assertIsNone(decision.retrieval)
        self.assertIsNone(decision.plan)
