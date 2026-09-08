import unittest

from medaudit.documents import Chunk
from medaudit.evaluation.baseline import EvaluationCase, evaluate, validate_references
from medaudit.retrieval import BM25Index


class EvaluationTest(unittest.TestCase):
    def test_metrics_for_first_rank_hit(self) -> None:
        index = BM25Index([Chunk("c1", "d1", "autorização código PX-101")])
        cases = [
            EvaluationCase(
                case_id="case-1",
                question="PX-101",
                relevant_chunk_ids=frozenset({"c1"}),
                category="exact_lookup",
            )
        ]

        report = evaluate(index, cases, top_k=1)

        self.assertEqual(report["metrics"]["hit_rate@1"], 1.0)
        self.assertEqual(report["metrics"]["recall@1"], 1.0)
        self.assertEqual(report["metrics"]["mrr"], 1.0)

    def test_no_results_is_correct_abstention(self) -> None:
        index = BM25Index([Chunk("c1", "d1", "autorização PX-101")])
        cases = [
            EvaluationCase(
                case_id="missing-1",
                question="ZQ-999",
                relevant_chunk_ids=frozenset(),
                category="missing_evidence",
            )
        ]

        report = evaluate(index, cases, top_k=1)

        self.assertEqual(report["metrics"]["abstention_accuracy"], 1.0)
        self.assertTrue(report["cases"][0]["correct_abstention"])

    def test_unknown_golden_reference_is_rejected(self) -> None:
        chunks = [Chunk("c1", "d1", "conteúdo sintético")]
        cases = [
            EvaluationCase(
                case_id="case-1",
                question="pergunta",
                relevant_chunk_ids=frozenset({"unknown"}),
                category="factual",
            )
        ]

        with self.assertRaisesRegex(ValueError, "unknown chunks"):
            validate_references(chunks, cases)
