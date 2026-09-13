import asyncio
import unittest

from medaudit.evaluation.local_decomposed_grounding import (
    apply_prompt_policy,
    run_benchmark,
)
from medaudit.llm import LLMRequest, LLMResponse, Usage


class _FakeClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = iter(responses)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        del request
        return next(self._responses)


class LocalDecomposedGroundingBenchmarkTest(unittest.TestCase):
    def test_candidate_policy_changes_only_the_instruction(self) -> None:
        request = LLMRequest(
            instruction="baseline",
            input_text="synthetic input",
            response_schema={"type": "object"},
        )

        candidate = apply_prompt_policy(request, "answer-when-supported-v1")

        self.assertNotEqual(candidate.instruction, request.instruction)
        self.assertEqual(candidate.input_text, request.input_text)
        self.assertEqual(candidate.response_schema, request.response_schema)
        self.assertEqual(candidate.temperature, request.temperature)

    def test_reports_aggregate_safe_generation_metrics(self) -> None:
        cases = [
            {
                "id": "safe-case",
                "category": "comparison",
                "question": "synthetic private-shaped question",
                "evidence_groups": [
                    {
                        "step_id": "one",
                        "scope": "one",
                        "evidence": [
                            {
                                "evidence_id": "one-c1",
                                "document_id": "one-doc",
                                "text": "First synthetic fact is amber.",
                            }
                        ],
                    },
                    {
                        "step_id": "two",
                        "scope": "two",
                        "evidence": [
                            {
                                "evidence_id": "two-c1",
                                "document_id": "two-doc",
                                "text": "Second synthetic fact is blue.",
                            }
                        ],
                    },
                ],
                "expected": {
                    "status": "answered",
                    "required_concepts": [["amber"], ["blue"]],
                },
            }
        ]
        client = _FakeClient(
            [
                LLMResponse(
                    data={
                        "status": "answered",
                        "claims": [
                            {
                                "text": "Amber and blue.",
                                "supports": [
                                    {"step_id": "one", "evidence_ids": ["one-c1"]},
                                    {"step_id": "two", "evidence_ids": ["two-c1"]},
                                ],
                            }
                        ],
                    },
                    model="synthetic",
                    latency_ms=2,
                    usage=Usage(input_tokens=1, output_tokens=1),
                )
            ]
        )

        report = asyncio.run(run_benchmark(cases, client=client))

        self.assertEqual(report["metrics"]["grounded_contract_rate"], 1.0)
        self.assertEqual(report["metrics"]["answer_content_accuracy"], 1.0)
        self.assertEqual(report["metrics"]["exact_response_stability_rate"], 1.0)
        self.assertNotIn("private-shaped", str(report))

    def test_invalid_grounding_is_counted_without_aborting(self) -> None:
        case = {
            "id": "invalid-case",
            "category": "comparison",
            "question": "Compare.",
            "evidence_groups": [
                {
                    "step_id": "one",
                    "scope": "one",
                    "evidence": [
                        {
                            "evidence_id": "one-c1",
                            "document_id": "one-doc",
                            "text": "One.",
                        }
                    ],
                },
                {
                    "step_id": "two",
                    "scope": "two",
                    "evidence": [
                        {
                            "evidence_id": "two-c1",
                            "document_id": "two-doc",
                            "text": "Two.",
                        }
                    ],
                },
            ],
            "expected": {"status": "answered", "required_concepts": [["one"]]},
        }
        client = _FakeClient(
            [
                LLMResponse(
                    data={"status": "answered", "claims": []},
                    model="synthetic",
                    latency_ms=1,
                    usage=Usage(1, 1),
                )
            ]
        )

        report = asyncio.run(run_benchmark([case], client=client))

        self.assertEqual(report["metrics"]["structured_output_rate"], 1.0)
        self.assertEqual(report["metrics"]["grounded_contract_rate"], 0.0)

    def test_detects_variation_across_repetitions(self) -> None:
        case = {
            "id": "repeat-case",
            "category": "comparison",
            "question": "Compare.",
            "evidence_groups": [
                {
                    "step_id": "one",
                    "scope": "one",
                    "evidence": [
                        {
                            "evidence_id": "one-c1",
                            "document_id": "one-doc",
                            "text": "One is amber.",
                        }
                    ],
                },
                {
                    "step_id": "two",
                    "scope": "two",
                    "evidence": [
                        {
                            "evidence_id": "two-c1",
                            "document_id": "two-doc",
                            "text": "Two is blue.",
                        }
                    ],
                },
            ],
            "expected": {
                "status": "answered",
                "required_concepts": [["amber"], ["blue"]],
            },
        }
        answered = LLMResponse(
            data={
                "status": "answered",
                "claims": [
                    {
                        "text": "Amber and blue.",
                        "supports": [
                            {"step_id": "one", "evidence_ids": ["one-c1"]},
                            {"step_id": "two", "evidence_ids": ["two-c1"]},
                        ],
                    }
                ],
            },
            model="synthetic",
            latency_ms=1,
            usage=Usage(1, 1),
        )
        abstained = LLMResponse(
            data={"status": "insufficient_evidence", "claims": []},
            model="synthetic",
            latency_ms=1,
            usage=Usage(1, 1),
        )

        report = asyncio.run(
            run_benchmark(
                [case],
                client=_FakeClient([answered, abstained, answered]),
                repetitions=3,
            )
        )

        self.assertEqual(report["attempt_count"], 3)
        self.assertEqual(report["metrics"]["response_status_accuracy"], 2 / 3)
        self.assertEqual(report["metrics"]["exact_response_stability_rate"], 0.0)
        self.assertEqual(report["metrics"]["status_stability_rate"], 0.0)
        self.assertEqual(
            report["metrics"]["content_correctness_stability_rate"], 0.0
        )


if __name__ == "__main__":
    unittest.main()
