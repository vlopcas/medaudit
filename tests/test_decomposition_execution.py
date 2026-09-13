import unittest
from datetime import date

from medaudit.documents import Chunk
from medaudit.query_understanding import DeterministicQueryPlanner
from medaudit.rag import (
    DecompositionExecutionStatus,
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
)
from medaudit.retrieval import BM25Index


class DeterministicDecompositionExecutorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = DeterministicQueryPlanner()
        self.comparison = self._pipeline(
            [
                Chunk("alpha", "document-alpha", "regra alfa sintética"),
                Chunk("beta", "document-beta", "regra beta sintética"),
            ]
        )
        self.temporal = {
            date(2026, 1, 1): self._pipeline(
                [Chunk("old", "document-old", "regra sintética anterior")]
            ),
            date(2026, 7, 1): self._pipeline(
                [Chunk("new", "document-new", "regra sintética posterior")]
            ),
        }
        self.executor = DeterministicDecompositionExecutor(
            comparison_pipeline=self.comparison,
            temporal_pipeline_for=self.temporal.__getitem__,
        )

    def test_executes_comparison_scopes_independently(self) -> None:
        plan = self.planner.plan("Compare regra alfa com regra beta.")

        execution = self.executor.execute(plan, top_k=1)

        self.assertEqual(execution.status, DecompositionExecutionStatus.READY)
        self.assertEqual(
            tuple(
                item.retrieval.evidence[0].location.chunk_id
                for item in execution.steps
            ),
            ("alpha", "beta"),
        )

    def test_resolves_one_temporal_pipeline_per_date(self) -> None:
        plan = self.planner.plan(
            "Compare a regra sintética em 2026-01-01 e 2026-07-01."
        )

        execution = self.executor.execute(plan, top_k=1)

        self.assertEqual(execution.status, DecompositionExecutionStatus.READY)
        self.assertEqual(
            tuple(
                item.retrieval.evidence[0].location.chunk_id
                for item in execution.steps
            ),
            ("old", "new"),
        )

    def test_any_failed_step_makes_execution_insufficient(self) -> None:
        plan = self.planner.plan("Compare regra alfa com item inexistente.")

        execution = self.executor.execute(plan, top_k=1)

        self.assertEqual(
            execution.status,
            DecompositionExecutionStatus.INSUFFICIENT_EVIDENCE,
        )
        self.assertEqual(len(execution.steps), 2)

    def test_clarification_plan_does_not_resolve_or_retrieve(self) -> None:
        plan = self.planner.plan("Faça uma comparação geral.")

        execution = self.executor.execute(plan)

        self.assertEqual(
            execution.status,
            DecompositionExecutionStatus.NEEDS_CLARIFICATION,
        )
        self.assertEqual(execution.steps, ())

    @staticmethod
    def _pipeline(chunks: list[Chunk]) -> EvidenceFirstPipeline:
        return EvidenceFirstPipeline(
            chunks=chunks,
            retriever=BM25Index(chunks),
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
