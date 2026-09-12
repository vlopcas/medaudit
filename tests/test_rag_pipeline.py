import json
import tempfile
import unittest
from pathlib import Path

from medaudit.documents import Chunk
from medaudit.llm import LLMResponse, Usage
from medaudit.rag import (
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    RetrievalStatus,
    build_grounded_request,
    validate_grounded_response,
)
from medaudit.retrieval import BM25Index


class FrozenTopScorePolicyTest(unittest.TestCase):
    def test_loads_supported_frozen_policy(self) -> None:
        payload = {
            "schema_version": 1,
            "status": "frozen",
            "policy": {
                "signal": "top_score",
                "operator": "greater_than_or_equal",
                "threshold": 3,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.local.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            policy = FrozenTopScorePolicy.from_file(path)

        self.assertEqual(policy.threshold, 3.0)

    def test_rejects_candidate_policy(self) -> None:
        payload = {
            "schema_version": 1,
            "status": "candidate",
            "policy": {
                "signal": "top_score",
                "operator": "greater_than_or_equal",
                "threshold": 3,
            },
        }

        with self.assertRaisesRegex(ValueError, "must be frozen"):
            FrozenTopScorePolicy.from_payload(payload)


class EvidenceFirstPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.chunks = [
            Chunk(
                "chunk-a",
                "document-a",
                "synthetic authorization rule alpha",
                page=7,
                section="Synthetic section",
            ),
            Chunk("chunk-b", "document-b", "synthetic billing rule beta", page=2),
        ]
        self.index = BM25Index(self.chunks)

    def test_returns_ranked_evidence_with_source_coordinates(self) -> None:
        pipeline = EvidenceFirstPipeline(
            chunks=self.chunks,
            retriever=self.index,
            policy=FrozenTopScorePolicy(threshold=0.1),
        )

        decision = pipeline.retrieve("authorization alpha", top_k=2)

        self.assertEqual(decision.status, RetrievalStatus.READY)
        self.assertTrue(decision.can_generate)
        self.assertEqual(decision.evidence[0].location.chunk_id, "chunk-a")
        self.assertEqual(decision.evidence[0].location.page, 7)
        self.assertEqual(decision.evidence[0].location.rank, 1)

    def test_abstention_removes_private_evidence_from_decision(self) -> None:
        pipeline = EvidenceFirstPipeline(
            chunks=self.chunks,
            retriever=self.index,
            policy=FrozenTopScorePolicy(threshold=100),
        )

        decision = pipeline.retrieve("authorization alpha")

        self.assertEqual(decision.status, RetrievalStatus.INSUFFICIENT_EVIDENCE)
        self.assertFalse(decision.can_generate)
        self.assertEqual(decision.evidence, ())

    def test_grounded_request_carries_only_selected_evidence_and_schema(self) -> None:
        pipeline = EvidenceFirstPipeline(
            chunks=self.chunks,
            retriever=self.index,
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
        decision = pipeline.retrieve("authorization alpha", top_k=1)

        request = build_grounded_request(decision)
        payload = json.loads(request.input_text)

        self.assertEqual(len(payload["evidence"]), 1)
        self.assertEqual(payload["evidence"][0]["evidence_id"], "chunk-a")
        self.assertEqual(request.temperature, 0.0)
        self.assertIn("evidence_ids", request.response_schema["required"])

    def test_does_not_build_request_after_abstention(self) -> None:
        pipeline = EvidenceFirstPipeline(
            chunks=self.chunks,
            retriever=self.index,
            policy=FrozenTopScorePolicy(threshold=100),
        )
        decision = pipeline.retrieve("authorization alpha")

        with self.assertRaisesRegex(ValueError, "accepted evidence"):
            build_grounded_request(decision)

    def test_validates_answer_citations_against_selected_evidence(self) -> None:
        pipeline = EvidenceFirstPipeline(
            chunks=self.chunks,
            retriever=self.index,
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
        decision = pipeline.retrieve("authorization alpha", top_k=1)
        response = LLMResponse(
            data={
                "status": "answered",
                "answer": "Synthetic supported answer.",
                "evidence_ids": ["chunk-a"],
            },
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=1, output_tokens=1),
        )

        answer = validate_grounded_response(response, decision)

        self.assertEqual(answer.citations[0].document_id, "document-a")

    def test_rejects_citation_not_present_in_selected_evidence(self) -> None:
        pipeline = EvidenceFirstPipeline(
            chunks=self.chunks,
            retriever=self.index,
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
        decision = pipeline.retrieve("authorization alpha", top_k=1)
        response = LLMResponse(
            data={
                "status": "answered",
                "answer": "Unsupported answer.",
                "evidence_ids": ["invented-chunk"],
            },
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=1, output_tokens=1),
        )

        with self.assertRaisesRegex(ValueError, "unauthorized evidence"):
            validate_grounded_response(response, decision)

    def test_accepts_empty_model_abstention(self) -> None:
        pipeline = EvidenceFirstPipeline(
            chunks=self.chunks,
            retriever=self.index,
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
        decision = pipeline.retrieve("authorization alpha", top_k=1)
        response = LLMResponse(
            data={
                "status": "insufficient_evidence",
                "answer": "",
                "evidence_ids": [],
            },
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=1, output_tokens=1),
        )

        answer = validate_grounded_response(response, decision)

        self.assertEqual(answer.status, "insufficient_evidence")
        self.assertEqual(answer.citations, ())
