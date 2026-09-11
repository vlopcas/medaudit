import unittest

import numpy as np

from medaudit.documents import Chunk
from medaudit.retrieval import DenseIndex
from medaudit.retrieval.embeddings import FloatMatrix


class SyntheticEmbedder:
    def encode_passages(self, texts: list[str], *, batch_size: int) -> FloatMatrix:
        vectors = {
            "alpha": [1.0, 0.0],
            "beta": [0.0, 1.0],
            "mixed": [0.8, 0.6],
        }
        return np.asarray([vectors[text] for text in texts], dtype=np.float32)

    def encode_query(self, text: str) -> FloatMatrix:
        vectors = {"first concept": [1.0, 0.0], "second concept": [0.0, 1.0]}
        return np.asarray([vectors[text]], dtype=np.float32)


class DenseIndexTest(unittest.TestCase):
    def test_ranks_normalized_vectors_by_cosine_similarity(self) -> None:
        chunks = [
            Chunk("chunk-a", "doc-a", "alpha"),
            Chunk("chunk-b", "doc-b", "beta"),
            Chunk("chunk-c", "doc-c", "mixed"),
        ]
        index = DenseIndex(chunks, SyntheticEmbedder(), batch_size=2)

        results = index.search("first concept", top_k=2)

        self.assertEqual(
            [result.chunk.chunk_id for result in results], ["chunk-a", "chunk-c"]
        )
        self.assertAlmostEqual(results[0].score, 1.0)

    def test_applies_similarity_threshold(self) -> None:
        chunks = [Chunk("chunk-a", "doc-a", "alpha")]
        index = DenseIndex(chunks, SyntheticEmbedder())

        results = index.search("second concept", min_score=0.1)

        self.assertEqual(results, [])

    def test_rejects_non_finite_embeddings(self) -> None:
        class InvalidEmbedder(SyntheticEmbedder):
            def encode_passages(
                self, texts: list[str], *, batch_size: int
            ) -> FloatMatrix:
                return np.asarray([[np.nan]], dtype=np.float32)

        with self.assertRaisesRegex(ValueError, "non-finite"):
            DenseIndex([Chunk("chunk-a", "doc-a", "alpha")], InvalidEmbedder())
