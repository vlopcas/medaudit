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

    def test_external_dependency_stops_before_retrieval(self) -> None:
        decision = self.pipeline.retrieve(
            "Consulte o preço atual no portal externo."
        )

        self.assertEqual(decision.route, QueryRoute.REQUIRES_EXTERNAL_DATA)
        self.assertIsNone(decision.retrieval)
