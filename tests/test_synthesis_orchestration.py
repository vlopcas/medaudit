import asyncio
import unittest

from medaudit.documents import Chunk
from medaudit.llm import LLMRequest, LLMResponse, Usage
from medaudit.rag import (
    CompiledContextGateway,
    CompiledRequestMode,
    DeterministicDecompositionExecutor,
    EvidenceFirstPipeline,
    FrozenTopScorePolicy,
    GroundedSynthesisOrchestrator,
    RoutedEvidenceFirstPipeline,
    SynthesisMode,
    SynthesisStatus,
    VerificationCode,
    VerificationDecision,
    VerificationResult,
)
from medaudit.retrieval import BM25Index


class FakeClient:
    def __init__(self, response: LLMResponse | Exception) -> None:
        self.response = response
        self.requests: list[LLMRequest] = []

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeVerifier:
    def __init__(
        self, result: VerificationResult | Exception
    ) -> None:
        self.result = result
        self.call_count = 0

    def verify(self, answer: object, evidence: object) -> VerificationResult:
        self.call_count += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class GroundedSynthesisOrchestratorTest(unittest.TestCase):
    def setUp(self) -> None:
        chunks = [
            Chunk("chunk-alpha", "document-alpha", "regra alfa sintética"),
            Chunk("chunk-beta", "document-beta", "regra beta sintética"),
        ]
        evidence_pipeline = EvidenceFirstPipeline(
            chunks=chunks,
            retriever=BM25Index(chunks),
            policy=FrozenTopScorePolicy(threshold=0.1),
        )
        executor = DeterministicDecompositionExecutor(
            comparison_pipeline=evidence_pipeline,
            temporal_pipeline_for=lambda _: evidence_pipeline,
        )
        self.prepared = RoutedEvidenceFirstPipeline(
            evidence_pipeline,
            decomposition_executor=executor,
            compiled_context_gateway=CompiledContextGateway(
                mode=CompiledRequestMode.EXPERIMENTAL,
                token_budget=10_000,
            ),
        ).retrieve_with_compiled_request(
            "Compare regra alfa com regra beta.", top_k=1
        )
        self.blocked = RoutedEvidenceFirstPipeline(
            evidence_pipeline,
            decomposition_executor=executor,
        ).retrieve_with_compiled_request(
            "Compare regra alfa com regra beta.", top_k=1
        )

    def test_disabled_mode_never_invokes_client(self) -> None:
        client = FakeClient(self._valid_response())

        result = asyncio.run(
            GroundedSynthesisOrchestrator(client=client).synthesize(self.prepared)
        )

        self.assertEqual(result.telemetry.status, SynthesisStatus.DISABLED)
        self.assertIsNone(result.answer)
        self.assertEqual(client.requests, [])

    def test_unprepared_request_is_blocked_without_client_call(self) -> None:
        client = FakeClient(self._valid_response())
        orchestrator = GroundedSynthesisOrchestrator(
            mode=SynthesisMode.EXPERIMENTAL,
            client=client,
        )

        result = asyncio.run(orchestrator.synthesize(self.blocked))

        self.assertEqual(result.telemetry.status, SynthesisStatus.BLOCKED)
        self.assertEqual(result.telemetry.failure_code, "request_not_prepared")
        self.assertEqual(client.requests, [])

    def test_releases_only_validated_grounded_answer(self) -> None:
        client = FakeClient(self._valid_response())
        orchestrator = GroundedSynthesisOrchestrator(
            mode=SynthesisMode.EXPERIMENTAL,
            client=client,
        )

        result = asyncio.run(orchestrator.synthesize(self.prepared))

        self.assertTrue(result.is_validated)
        assert result.answer is not None
        self.assertEqual(len(result.answer.claims), 2)
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(result.telemetry.input_tokens, 12)
        self.assertEqual(result.telemetry.output_tokens, 7)

    def test_rejects_response_with_cross_group_citation(self) -> None:
        client = FakeClient(
            self._response(
                {
                    "status": "answered",
                    "claims": [
                        {
                            "text": "Afirmação sintética inválida.",
                            "supports": [
                                {
                                    "step_id": "comparison-1",
                                    "evidence_ids": ["chunk-beta"],
                                }
                            ],
                        }
                    ],
                }
            )
        )
        orchestrator = GroundedSynthesisOrchestrator(
            mode=SynthesisMode.EXPERIMENTAL,
            client=client,
        )

        result = asyncio.run(orchestrator.synthesize(self.prepared))

        self.assertEqual(result.telemetry.status, SynthesisStatus.REJECTED)
        self.assertEqual(result.telemetry.failure_code, "response_rejected")
        self.assertIsNone(result.answer)

    def test_verifier_can_reject_without_releasing_validated_answer(self) -> None:
        verifier = FakeVerifier(
            VerificationResult(
                VerificationDecision.REJECT,
                VerificationCode.UNTRUSTED_CONTENT,
            )
        )
        result = asyncio.run(
            GroundedSynthesisOrchestrator(
                mode=SynthesisMode.EXPERIMENTAL,
                client=FakeClient(self._valid_response()),
                verifier=verifier,
            ).synthesize(self.prepared)
        )

        self.assertEqual(result.telemetry.status, SynthesisStatus.REJECTED)
        self.assertEqual(
            result.telemetry.failure_code,
            "verification_untrusted_content",
        )
        self.assertIsNone(result.answer)
        self.assertEqual(verifier.call_count, 1)

    def test_verifier_can_hold_answer_for_review(self) -> None:
        verifier = FakeVerifier(
            VerificationResult(
                VerificationDecision.REVIEW,
                VerificationCode.REVIEW_REQUIRED,
            )
        )
        result = asyncio.run(
            GroundedSynthesisOrchestrator(
                mode=SynthesisMode.EXPERIMENTAL,
                client=FakeClient(self._valid_response()),
                verifier=verifier,
            ).synthesize(self.prepared)
        )

        self.assertEqual(result.telemetry.status, SynthesisStatus.HELD)
        self.assertEqual(
            result.telemetry.failure_code,
            "verification_review_required",
        )
        self.assertIsNone(result.answer)

    def test_verifier_failure_is_closed(self) -> None:
        result = asyncio.run(
            GroundedSynthesisOrchestrator(
                mode=SynthesisMode.EXPERIMENTAL,
                client=FakeClient(self._valid_response()),
                verifier=FakeVerifier(RuntimeError("synthetic verifier failure")),
            ).synthesize(self.prepared)
        )

        self.assertEqual(result.telemetry.status, SynthesisStatus.FAILED)
        self.assertEqual(result.telemetry.failure_code, "verifier_failed")
        self.assertIsNone(result.answer)

    def test_client_failure_returns_no_answer(self) -> None:
        client = FakeClient(RuntimeError("synthetic client failure"))
        orchestrator = GroundedSynthesisOrchestrator(
            mode=SynthesisMode.EXPERIMENTAL,
            client=client,
        )

        result = asyncio.run(orchestrator.synthesize(self.prepared))

        self.assertEqual(result.telemetry.status, SynthesisStatus.FAILED)
        self.assertEqual(result.telemetry.failure_code, "client_failed")
        self.assertIsNone(result.answer)

    def test_experimental_mode_requires_client(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires an LLM client"):
            GroundedSynthesisOrchestrator(mode=SynthesisMode.EXPERIMENTAL)

    @classmethod
    def _valid_response(cls) -> LLMResponse:
        return cls._response(
            {
                "status": "answered",
                "claims": [
                    {
                        "text": "A regra alfa possui suporte sintético.",
                        "supports": [
                            {
                                "step_id": "comparison-1",
                                "evidence_ids": ["chunk-alpha"],
                            }
                        ],
                    },
                    {
                        "text": "A regra beta possui suporte sintético.",
                        "supports": [
                            {
                                "step_id": "comparison-2",
                                "evidence_ids": ["chunk-beta"],
                            }
                        ],
                    },
                ],
            }
        )

    @staticmethod
    def _response(data: dict[str, object]) -> LLMResponse:
        return LLMResponse(
            data=data,
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=12, output_tokens=7),
        )


if __name__ == "__main__":
    unittest.main()
