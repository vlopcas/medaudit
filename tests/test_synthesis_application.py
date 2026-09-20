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
    GroundedSynthesisApplication,
    GroundedSynthesisOrchestrator,
    RoutedEvidenceFirstPipeline,
    SynthesisMode,
    SynthesisStatus,
)
from medaudit.retrieval import BM25Index


class RecordingClient:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = data
        self.requests: list[LLMRequest] = []

    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            data=self.data,
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=12, output_tokens=7),
        )


class GroundedSynthesisApplicationTest(unittest.TestCase):
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
        self.pipeline = RoutedEvidenceFirstPipeline(
            evidence_pipeline,
            decomposition_executor=executor,
            compiled_context_gateway=CompiledContextGateway(
                mode=CompiledRequestMode.EXPERIMENTAL,
                token_budget=10_000,
            ),
        )

    def test_default_composition_keeps_synthesis_disabled(self) -> None:
        result = asyncio.run(
            GroundedSynthesisApplication(self.pipeline).execute(
                "Compare regra alfa com regra beta.", top_k=1
            )
        )

        self.assertIsNotNone(result.routed.compiled_request)
        self.assertEqual(result.synthesis.telemetry.status, SynthesisStatus.DISABLED)
        self.assertIsNone(result.synthesis.answer)

    def test_experimental_composition_releases_validated_answer(self) -> None:
        client = RecordingClient(self._valid_data())
        application = GroundedSynthesisApplication(
            self.pipeline,
            orchestrator=GroundedSynthesisOrchestrator(
                mode=SynthesisMode.EXPERIMENTAL,
                client=client,
            ),
        )

        result = asyncio.run(
            application.execute("Compare regra alfa com regra beta.", top_k=1)
        )

        self.assertTrue(result.synthesis.is_validated)
        self.assertEqual(len(client.requests), 1)
        self.assertIsNotNone(result.routed.retrieval.evidence_bundle)

    def test_non_decomposition_route_never_calls_client(self) -> None:
        client = RecordingClient(self._valid_data())
        application = GroundedSynthesisApplication(
            self.pipeline,
            orchestrator=GroundedSynthesisOrchestrator(
                mode=SynthesisMode.EXPERIMENTAL,
                client=client,
            ),
        )

        result = asyncio.run(
            application.execute("Qual é a regra alfa sintética?", top_k=1)
        )

        self.assertEqual(result.synthesis.telemetry.status, SynthesisStatus.BLOCKED)
        self.assertEqual(client.requests, [])

    @staticmethod
    def _valid_data() -> dict[str, object]:
        return {
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


if __name__ == "__main__":
    unittest.main()
