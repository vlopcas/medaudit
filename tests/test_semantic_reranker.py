import unittest

import numpy as np

from medaudit.documents import Chunk
from medaudit.retrieval import BM25Index, SemanticCandidateReranker
from medaudit.retrieval.embeddings import FloatMatrix


class QueryEmbedder:
    def encode_passages(self, texts: list[str], *, batch_size: int) -> FloatMatrix:
        raise AssertionError("passages must already be encoded")

    def encode_query(self, text: str) -> FloatMatrix:
        return np.asarray([[1.0, 0.0]], dtype=np.float32)


class SemanticCandidateRerankerTest(unittest.TestCase):
    def test_semantic_rank_can_promote_a_lexical_candidate(self) -> None:
        chunks = [
            Chunk("lexical-first", "doc-a", "term term term"),
            Chunk("semantic-first", "doc-b", "term"),
        ]
        vectors = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
        reranker = SemanticCandidateReranker(
            BM25Index(chunks),
            chunks,
            vectors,
            QueryEmbedder(),
            rank_constant=0,
            lexical_weight=1.0,
            semantic_weight=2.0,
        )

        results = reranker.search("term", top_k=2)

        self.assertEqual(results[0].chunk.chunk_id, "semantic-first")

    def test_never_introduces_a_chunk_outside_lexical_candidates(self) -> None:
        chunks = [
            Chunk("candidate", "doc-a", "matching"),
            Chunk("excluded", "doc-b", "unrelated"),
        ]
        vectors = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
        reranker = SemanticCandidateReranker(
            BM25Index(chunks), chunks, vectors, QueryEmbedder()
        )

        results = reranker.search("matching", top_k=2)

        self.assertEqual([result.chunk.chunk_id for result in results], ["candidate"])
