import json
import unittest

from medaudit.documents import Chunk
from medaudit.llm import LLMResponse, Usage
from medaudit.query_understanding import DeterministicQueryPlanner
from medaudit.rag import (
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    build_decomposed_grounded_request,
    group_decomposition_evidence,
    validate_decomposed_grounded_response,
)
from medaudit.retrieval import BM25Index


class DecomposedGroundedContractTest(unittest.TestCase):
    def setUp(self) -> None:
        chunks = [
            Chunk("alpha", "document-alpha", "regra alfa sintética"),
            Chunk("beta", "document-beta", "regra beta sintética"),
        ]
        pipeline = EvidenceFirstPipeline(
            chunks=chunks,
            retriever=BM25Index(chunks),
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
        executor = DeterministicDecompositionExecutor(
            comparison_pipeline=pipeline,
            temporal_pipeline_for=lambda _: pipeline,
        )
        planner = DeterministicQueryPlanner()
        self.bundle = group_decomposition_evidence(
            executor.execute(
                planner.plan("Compare regra alfa com regra beta."), top_k=1
            )
        )
        self.blocked_bundle = group_decomposition_evidence(
            executor.execute(
                planner.plan("Compare regra alfa com item inexistente."), top_k=1
            )
        )

    def test_request_preserves_groups_and_requires_claim_support(self) -> None:
        request = build_decomposed_grounded_request(self.bundle)
        payload = json.loads(request.input_text)

        self.assertEqual(
            [group["step_id"] for group in payload["evidence_groups"]],
            ["comparison-1", "comparison-2"],
        )
        claim_schema = request.response_schema["properties"]["claims"]["items"]
        self.assertEqual(claim_schema["required"], ["text", "supports"])

    def test_validates_claims_scoped_to_each_group(self) -> None:
        answer = validate_decomposed_grounded_response(
            self._response(
                {
                    "status": "answered",
                    "claims": [
                        {
                            "text": "A regra alfa tem suporte sintético.",
                            "supports": [
                                {
                                    "step_id": "comparison-1",
                                    "evidence_ids": ["alpha"],
                                }
                            ],
                        },
                        {
                            "text": "A regra beta tem suporte sintético.",
                            "supports": [
                                {
                                    "step_id": "comparison-2",
                                    "evidence_ids": ["beta"],
                                }
                            ],
                        },
                    ],
                }
            ),
            self.bundle,
        )

        self.assertEqual(len(answer.claims), 2)
        self.assertEqual(answer.claims[0].supports[0].step_id, "comparison-1")

    def test_rejects_citation_from_another_group(self) -> None:
        response = self._response(
            {
                "status": "answered",
                "claims": [
                    {
                        "text": "Suporte trocado.",
                        "supports": [
                            {
                                "step_id": "comparison-1",
                                "evidence_ids": ["beta"],
                            }
                        ],
                    }
                ],
            }
        )

        with self.assertRaisesRegex(ValueError, "outside its step"):
            validate_decomposed_grounded_response(response, self.bundle)

    def test_rejects_answer_that_omits_a_group(self) -> None:
        response = self._response(
            {
                "status": "answered",
                "claims": [
                    {
                        "text": "Somente alfa.",
                        "supports": [
                            {
                                "step_id": "comparison-1",
                                "evidence_ids": ["alpha"],
                            }
                        ],
                    }
                ],
            }
        )

        with self.assertRaisesRegex(ValueError, "every evidence group"):
            validate_decomposed_grounded_response(response, self.bundle)

    def test_rejects_request_and_validation_for_partial_bundle(self) -> None:
        with self.assertRaisesRegex(ValueError, "complete evidence"):
            build_decomposed_grounded_request(self.blocked_bundle)
        with self.assertRaisesRegex(ValueError, "complete grouped evidence"):
            validate_decomposed_grounded_response(
                self._response({"status": "insufficient_evidence", "claims": []}),
                self.blocked_bundle,
            )

    def test_accepts_model_abstention_without_claims(self) -> None:
        answer = validate_decomposed_grounded_response(
            self._response({"status": "insufficient_evidence", "claims": []}),
            self.bundle,
        )

        self.assertEqual(answer.claims, ())

    @staticmethod
    def _response(data: dict[str, object]) -> LLMResponse:
        return LLMResponse(
            data=data,
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=1, output_tokens=1),
        )
