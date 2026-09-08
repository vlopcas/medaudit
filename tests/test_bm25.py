import unittest

from medaudit.documents import Chunk
from medaudit.retrieval import BM25Index
from medaudit.retrieval.bm25 import tokenize


class BM25IndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.index = BM25Index(
            [
                Chunk("c1", "d1", "O código PX-101 exige autorização prévia."),
                Chunk("c2", "d2", "O exame EX-220 possui limite de duas unidades."),
            ]
        )

    def test_exact_code_retrieval(self) -> None:
        results = self.index.search("autorização do PX-101", top_k=1)

        self.assertEqual(results[0].chunk.chunk_id, "c1")

    def test_tokenization_normalizes_accents(self) -> None:
        self.assertEqual(tokenize("Autorização PRÉVIA"), ["autorizacao", "previa"])

    def test_empty_index_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            BM25Index([])

    def test_minimum_score_can_abstain(self) -> None:
        self.assertEqual(self.index.search("código", min_score=100.0), [])
