import unittest
from dataclasses import replace

from medaudit.evaluation.local_decomposed_grounding import build_bundle
from medaudit.rag import (
    ContextExclusionReason,
    ContextItemKind,
    ContextStatus,
    ContextTrust,
    DecompositionEvidenceBundle,
    compile_decomposed_context,
)


class WordEstimator:
    def estimate(self, text: str) -> int:
        return len(text.split())


def make_bundle() -> DecompositionEvidenceBundle:
    return build_bundle(
        {
            "question": "Compare alfa e beta.",
            "evidence_groups": [
                {
                    "step_id": "alfa",
                    "scope": "alfa",
                    "evidence": [
                        {
                            "evidence_id": "alfa-c1",
                            "document_id": "alfa-doc",
                            "text": "Alfa permite o evento sintético.",
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
                            "text": "Beta proíbe o evento sintético.",
                        }
                    ],
                },
            ],
        }
    )


class ContextCompilerTest(unittest.TestCase):
    def test_keeps_control_and_evidence_structurally_separated(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction="Responda somente com suporte.",
            token_budget=30,
            estimator=WordEstimator(),
        )

        self.assertEqual(context.status, ContextStatus.READY)
        self.assertTrue(context.can_generate)
        self.assertEqual(context.items[0].kind, ContextItemKind.INSTRUCTION)
        self.assertEqual(context.items[0].trust, ContextTrust.TRUSTED_CONTROL)
        self.assertEqual(context.items[1].kind, ContextItemKind.QUERY)
        self.assertEqual(context.items[1].trust, ContextTrust.UNTRUSTED_DATA)
        evidence = context.items[2:]
        self.assertTrue(evidence)
        self.assertTrue(
            all(item.trust is ContextTrust.UNTRUSTED_DATA for item in evidence)
        )
        self.assertEqual({item.step_ids[0] for item in evidence}, {"alfa", "beta"})

    def test_requires_review_without_exposing_rejected_evidence(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction="Responda somente com suporte.",
            token_budget=30,
            estimator=WordEstimator(),
            review_evidence_ids=frozenset({"beta-c1"}),
        )

        self.assertEqual(context.status, ContextStatus.NEEDS_REVIEW)
        self.assertFalse(context.can_generate)
        self.assertNotIn("Beta proíbe", repr(context))
        self.assertEqual(
            context.exclusions[-1].reason,
            ContextExclusionReason.REVIEW_REQUIRED,
        )

    def test_blocks_generation_when_budget_omits_a_required_step(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction="Responda com suporte.",
            token_budget=12,
            estimator=WordEstimator(),
        )

        self.assertEqual(context.status, ContextStatus.BUDGET_EXCEEDED)
        self.assertFalse(context.can_generate)
        self.assertIn(
            ContextExclusionReason.TOKEN_BUDGET,
            {exclusion.reason for exclusion in context.exclusions},
        )

    def test_conflicting_duplicate_identity_requires_review(self) -> None:
        bundle = make_bundle()
        first = bundle.groups[0].evidence[0]
        conflicting = replace(first, text="Conteúdo conflitante.")
        duplicate_group = replace(
            bundle.groups[1],
            evidence=(conflicting,),
        )
        execution_step = replace(
            bundle.execution.steps[1],
            retrieval=replace(
                bundle.execution.steps[1].retrieval,
                evidence=(conflicting,),
            ),
        )
        conflicting_bundle = replace(
            bundle,
            groups=(bundle.groups[0], duplicate_group),
            execution=replace(
                bundle.execution,
                steps=(bundle.execution.steps[0], execution_step),
            ),
        )

        context = compile_decomposed_context(
            conflicting_bundle,
            instruction="Responda com suporte.",
            token_budget=30,
            estimator=WordEstimator(),
        )

        self.assertEqual(context.status, ContextStatus.NEEDS_REVIEW)
        self.assertIn(
            ContextExclusionReason.CONFLICTING_IDENTITY,
            {exclusion.reason for exclusion in context.exclusions},
        )


if __name__ == "__main__":
    unittest.main()
