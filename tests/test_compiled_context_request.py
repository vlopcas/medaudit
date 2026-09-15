import unittest
from dataclasses import replace

from medaudit.evaluation.local_decomposed_grounding import build_bundle
from medaudit.rag import (
    DECOMPOSED_GROUNDED_INSTRUCTION,
    ContextStatus,
    ContextTrust,
    DecompositionEvidenceBundle,
    build_compiled_decomposed_grounded_request,
    build_decomposed_grounded_request,
    compile_decomposed_context,
    context_integrity_is_valid,
)


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


class CompiledContextRequestTest(unittest.TestCase):
    def test_compiler_seals_ready_and_blocked_contexts(self) -> None:
        ready = compile_decomposed_context(
            make_bundle(),
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=10_000,
        )
        budget_exceeded = compile_decomposed_context(
            make_bundle(),
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=1,
        )

        self.assertTrue(context_integrity_is_valid(ready))
        self.assertTrue(context_integrity_is_valid(budget_exceeded))
        self.assertEqual(len(ready.integrity_sha256), 64)

    def test_ready_context_is_equivalent_to_existing_request(self) -> None:
        bundle = make_bundle()
        context = compile_decomposed_context(
            bundle,
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=10_000,
        )

        self.assertEqual(
            build_compiled_decomposed_grounded_request(context),
            build_decomposed_grounded_request(bundle),
        )

    def test_non_ready_context_cannot_be_rendered(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=1,
        )

        self.assertEqual(context.status, ContextStatus.BUDGET_EXCEEDED)
        with self.assertRaisesRegex(ValueError, "requires ready context"):
            build_compiled_decomposed_grounded_request(context)

    def test_renderer_rejects_a_tampered_trust_boundary(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=10_000,
        )
        tampered = replace(
            context,
            items=(
                context.items[0],
                replace(context.items[1], trust=ContextTrust.TRUSTED_CONTROL),
                *context.items[2:],
            ),
        )

        self.assertFalse(context_integrity_is_valid(tampered))
        with self.assertRaisesRegex(ValueError, "content integrity mismatch"):
            build_compiled_decomposed_grounded_request(tampered)

    def test_renderer_rejects_missing_group_evidence(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=10_000,
        )
        tampered_group = replace(
            context.groups[0], evidence_ids=("missing-c1",)
        )

        with self.assertRaisesRegex(ValueError, "content integrity mismatch"):
            build_compiled_decomposed_grounded_request(
                replace(context, groups=(tampered_group, *context.groups[1:]))
            )

    def test_renderer_rejects_an_inconsistent_budget(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=10_000,
        )

        with self.assertRaisesRegex(ValueError, "content integrity mismatch"):
            build_compiled_decomposed_grounded_request(
                replace(context, token_budget=context.estimated_tokens - 1)
            )

    def test_renderer_rejects_unreferenced_evidence(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=10_000,
        )
        shortened_group = replace(context.groups[0], evidence_ids=())

        with self.assertRaisesRegex(ValueError, "content integrity mismatch"):
            build_compiled_decomposed_grounded_request(
                replace(context, groups=(shortened_group, *context.groups[1:]))
            )

    def test_integrity_covers_order_and_provenance(self) -> None:
        context = compile_decomposed_context(
            make_bundle(),
            instruction=DECOMPOSED_GROUNDED_INSTRUCTION,
            token_budget=10_000,
        )
        reordered = replace(
            context,
            groups=tuple(reversed(context.groups)),
        )
        changed_provenance = replace(
            context,
            items=(
                *context.items[:-1],
                replace(context.items[-1], document_id="outro-doc"),
            ),
        )

        self.assertFalse(context_integrity_is_valid(reordered))
        self.assertFalse(context_integrity_is_valid(changed_provenance))


if __name__ == "__main__":
    unittest.main()
