import asyncio
import tempfile
import unittest
from pathlib import Path

from medaudit.evaluation.local_synthesis_application import (
    load_dataset,
    run_benchmark,
)
from medaudit.llm import LLMRequest, LLMResponse, Usage
from medaudit.rag import CompiledInstructionPolicy


class DeterministicClient:
    async def generate(self, request: LLMRequest) -> LLMResponse:
        if "taxa da regra cobre" in request.input_text:
            data: dict[str, object] = {
                "status": "insufficient_evidence",
                "claims": [],
            }
        else:
            data = {
                "status": "answered",
                "claims": [
                    {
                        "text": "dez dias",
                        "supports": [
                            {"step_id": "comparison-1", "evidence_ids": ["chunk-ambar"]}
                        ],
                    },
                    {
                        "text": "vinte dias",
                        "supports": [
                            {
                                "step_id": "comparison-2",
                                "evidence_ids": ["chunk-cobalto"],
                            }
                        ],
                    },
                ],
            }
        return LLMResponse(
            data=data,
            model="synthetic-model",
            latency_ms=1,
            usage=Usage(input_tokens=10, output_tokens=5),
        )


class LocalSynthesisApplicationBenchmarkTest(unittest.TestCase):
    def test_benchmark_uses_full_application_without_retaining_text(self) -> None:
        cases = [
            {
                "id": "case-1",
                "category": "supported",
                "query": "Compare item âmbar com item cobalto.",
                "chunks": [
                    {
                        "chunk_id": "chunk-ambar",
                        "document_id": "doc-a",
                        "text": "item âmbar dez dias",
                    },
                    {
                        "chunk_id": "chunk-cobalto",
                        "document_id": "doc-b",
                        "text": "item cobalto vinte dias",
                    },
                ],
                "expected": {
                    "status": "answered",
                    "required_concepts": [["dez dias"], ["vinte dias"]],
                },
            }
        ]

        report = asyncio.run(
            run_benchmark(
                cases,
                client=DeterministicClient(),
                repetitions=2,
                instruction_policy=(
                    CompiledInstructionPolicy.ANSWER_WHEN_SUPPORTED_V1
                ),
            )
        )

        self.assertEqual(report["metrics"]["preparation_rate"], 1.0)
        self.assertEqual(report["metrics"]["validated_release_rate"], 1.0)
        self.assertEqual(report["metrics"]["answer_content_accuracy"], 1.0)
        self.assertEqual(
            report["instruction_policy"], "answer-when-supported-v1"
        )
        self.assertEqual(report["synthesis_status_counts"], {"validated": 2})
        self.assertEqual(report["failure_code_counts"], {})
        self.assertNotIn("query", report["cases"][0])
        self.assertNotIn("answer", report["cases"][0])

    def test_loader_rejects_wrong_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(
                '{"schema_version":1,"policy":"wrong","notice":"x","cases":[]}',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_dataset(path)


if __name__ == "__main__":
    unittest.main()
