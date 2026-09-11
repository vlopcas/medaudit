import tempfile
import unittest
from pathlib import Path

import numpy as np

from medaudit.documents import Chunk
from medaudit.retrieval import DenseIndex, EmbeddingCache
from medaudit.retrieval.embeddings import FloatMatrix


class RecordingEmbedder:
    def __init__(self) -> None:
        self.passage_calls: list[list[str]] = []

    def encode_passages(self, texts: list[str], *, batch_size: int) -> FloatMatrix:
        self.passage_calls.append(texts)
        return np.asarray(
            [[float(len(text)), 1.0] for text in texts], dtype=np.float32
        )

    def encode_query(self, text: str) -> FloatMatrix:
        return np.asarray([[1.0, 0.0]], dtype=np.float32)


class EmbeddingCacheTest(unittest.TestCase):
    def test_reuses_vectors_and_only_encodes_new_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = EmbeddingCache(
                Path(directory) / "vectors.local.npz",
                model_id="model",
                model_revision="revision",
            )
            embedder = RecordingEmbedder()
            first = [Chunk("a", "doc", "alpha")]
            cache.materialize(first, embedder)
            combined = [*first, Chunk("b", "doc", "beta")]

            matrix = cache.materialize(combined, embedder)

            self.assertEqual(embedder.passage_calls, [["alpha"], ["beta"]])
            self.assertEqual(matrix.shape, (2, 2))

    def test_rejects_changed_content_for_existing_chunk_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = EmbeddingCache(
                Path(directory) / "vectors.local.npz",
                model_id="model",
                model_revision="revision",
            )
            embedder = RecordingEmbedder()
            cache.materialize([Chunk("a", "doc", "alpha")], embedder)

            with self.assertRaisesRegex(ValueError, "different content"):
                cache.materialize([Chunk("a", "doc", "changed")], embedder)

    def test_cached_matrix_can_build_dense_index_without_passage_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            chunks = [Chunk("a", "doc", "alpha")]
            cache = EmbeddingCache(
                Path(directory) / "vectors.local.npz",
                model_id="model",
                model_revision="revision",
            )
            embedder = RecordingEmbedder()
            matrix = cache.materialize(chunks, embedder)
            embedder.passage_calls.clear()

            DenseIndex(chunks, embedder, passage_embeddings=matrix)

            self.assertEqual(embedder.passage_calls, [])

    def test_rejects_cache_from_another_model_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vectors.local.npz"
            embedder = RecordingEmbedder()
            EmbeddingCache(
                path, model_id="model", model_revision="old"
            ).materialize([Chunk("a", "doc", "alpha")], embedder)

            with self.assertRaisesRegex(ValueError, "different configuration"):
                EmbeddingCache(
                    path, model_id="model", model_revision="new"
                ).materialize([Chunk("a", "doc", "alpha")], embedder)

    def test_rejects_cache_from_another_embedding_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vectors.local.npz"
            embedder = RecordingEmbedder()
            EmbeddingCache(
                path,
                model_id="model",
                model_revision="revision",
                embedding_strategy="truncate-v1",
            ).materialize([Chunk("a", "doc", "alpha")], embedder)

            with self.assertRaisesRegex(ValueError, "different configuration"):
                EmbeddingCache(
                    path,
                    model_id="model",
                    model_revision="revision",
                    embedding_strategy="token-window-mean-v1",
                ).materialize([Chunk("a", "doc", "alpha")], embedder)
