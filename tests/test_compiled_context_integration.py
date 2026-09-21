import json
import unittest
from dataclasses import asdict

from medaudit.evaluation.local_decomposed_grounding import build_bundle
from medaudit.rag import (
    ANSWER_WHEN_SUPPORTED_INSTRUCTION,
    CompiledContextGateway,
    CompiledInstructionPolicy,
    CompiledRequestMode,
    CompiledRequestStatus,
    CompiledSchemaPolicy,
    ContextStatus,
    DecompositionEvidenceBundle,
)


def make_bundle() -> DecompositionEvidenceBundle:
    return build_bundle(
        {
            "question": "Compare alfa sigiloso e beta sigiloso.",
            "evidence_groups": [
                {
                    "step_id": "alfa",
                    "scope": "alfa",
                    "evidence": [
                        {
                            "evidence_id": "alfa-c1",
                            "document_id": "alfa-doc",
                            "text": "CONTEUDO_PRIVADO_SIMULADO alfa.",
                        }
                    ],
                },
                {
                    "step_id": "beta",
                    "scope": "beta",
                    "evidence": [
                        {
                            "evidence_id": "beta-c1",
                            "document_id": "beta-doc",
                            "text": "CONTEUDO_PRIVADO_SIMULADO beta.",
                        }
                    ],
                },
            ],
        }
    )


class CompiledContextGatewayTest(unittest.TestCase):
    def test_is_disabled_by_default_without_compiling(self) -> None:
        result = CompiledContextGateway(clock=lambda: 1.0).prepare(make_bundle())

        self.assertFalse(result.is_prepared)
        self.assertIsNone(result.request)
        self.assertEqual(result.telemetry.status, CompiledRequestStatus.DISABLED)
        self.assertEqual(result.telemetry.failure_code, "integration_disabled")
        self.assertEqual(result.telemetry.item_count, 0)

    def test_experimental_mode_prepares_a_sealed_request(self) -> None:
        ticks = iter((1.0, 1.025))
        gateway = CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            token_budget=10_000,
            clock=lambda: next(ticks),
        )

        result = gateway.prepare(make_bundle())

        self.assertTrue(result.is_prepared)
        self.assertIsNotNone(result.request)
        self.assertEqual(result.telemetry.status, CompiledRequestStatus.PREPARED)
        self.assertEqual(result.telemetry.context_status, ContextStatus.READY)
        self.assertEqual(result.telemetry.group_count, 2)
        self.assertEqual(result.telemetry.item_count, 4)
        self.assertAlmostEqual(result.telemetry.duration_ms, 25.0)

    def test_answer_policy_changes_only_the_sealed_instruction(self) -> None:
        baseline = CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            token_budget=10_000,
            clock=lambda: 1.0,
        ).prepare(make_bundle())
        candidate = CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            instruction_policy=(
                CompiledInstructionPolicy.ANSWER_WHEN_SUPPORTED_V1
            ),
            token_budget=10_000,
            clock=lambda: 1.0,
        ).prepare(make_bundle())

        self.assertIsNotNone(baseline.request)
        self.assertIsNotNone(candidate.request)
        assert baseline.request is not None
        assert candidate.request is not None
        self.assertEqual(
            candidate.request.instruction, ANSWER_WHEN_SUPPORTED_INSTRUCTION
        )
        self.assertNotEqual(
            candidate.request.instruction, baseline.request.instruction
        )
        self.assertEqual(candidate.request.input_text, baseline.request.input_text)
        self.assertEqual(
            candidate.request.response_schema, baseline.request.response_schema
        )
        self.assertEqual(candidate.request.temperature, baseline.request.temperature)

    def test_bounded_schema_changes_only_structural_limits(self) -> None:
        baseline = CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            token_budget=10_000,
            clock=lambda: 1.0,
        ).prepare(make_bundle())
        bounded = CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            schema_policy=CompiledSchemaPolicy.BOUNDED_V1,
            token_budget=10_000,
            clock=lambda: 1.0,
        ).prepare(make_bundle())

        assert baseline.request is not None
        assert bounded.request is not None
        self.assertEqual(bounded.request.instruction, baseline.request.instruction)
        self.assertEqual(bounded.request.input_text, baseline.request.input_text)
        self.assertEqual(bounded.request.temperature, baseline.request.temperature)
        claims = bounded.request.response_schema["properties"]["claims"]
        self.assertEqual(claims["maxItems"], 4)
        self.assertNotEqual(
            bounded.request.response_schema, baseline.request.response_schema
        )

    def test_budget_failure_returns_no_request(self) -> None:
        gateway = CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            token_budget=1,
            clock=lambda: 1.0,
        )

        result = gateway.prepare(make_bundle())

        self.assertFalse(result.is_prepared)
        self.assertIsNone(result.request)
        self.assertEqual(result.telemetry.status, CompiledRequestStatus.BLOCKED)
        self.assertEqual(
            result.telemetry.context_status, ContextStatus.BUDGET_EXCEEDED
        )
        self.assertEqual(
            result.telemetry.failure_code, "context_budget_exceeded"
        )

    def test_telemetry_contains_no_query_evidence_or_identifiers(self) -> None:
        result = CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            token_budget=10_000,
            clock=lambda: 1.0,
        ).prepare(make_bundle())

        rendered = json.dumps(asdict(result.telemetry), default=str)
        self.assertNotIn("sigiloso", rendered)
        self.assertNotIn("CONTEUDO_PRIVADO_SIMULADO", rendered)
        self.assertNotIn("alfa-c1", rendered)
        self.assertNotIn("alfa-doc", rendered)

    def test_rejects_non_positive_budget(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be positive"):
            CompiledContextGateway(token_budget=0)

    def test_compiler_failure_is_closed_without_error_content(self) -> None:
        class RejectingEstimator:
            def estimate(self, text: str) -> int:
                raise ValueError(f"sensitive compiler detail: {text}")

        result = CompiledContextGateway(
            mode=CompiledRequestMode.EXPERIMENTAL,
            estimator=RejectingEstimator(),
            clock=lambda: 1.0,
        ).prepare(make_bundle())

        self.assertIsNone(result.request)
        self.assertEqual(result.telemetry.status, CompiledRequestStatus.REJECTED)
        self.assertEqual(result.telemetry.failure_code, "compiler_rejected_input")
        self.assertNotIn("sensitive", str(asdict(result.telemetry)))


if __name__ == "__main__":
    unittest.main()
