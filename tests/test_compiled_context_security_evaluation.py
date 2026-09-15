import unittest

from medaudit.evaluation.compiled_context_security import evaluate
from medaudit.evaluation.local_decomposed_grounding import build_bundle


class CompiledContextSecurityEvaluationTest(unittest.TestCase):
    def test_report_omits_evidence_text(self) -> None:
        payload = {
            "base_context": {
                "question": "Compare alfa e beta.",
                "evidence_groups": [
                    {
                        "step_id": "alfa",
                        "scope": "alfa",
                        "evidence": [
                            {
                                "evidence_id": "alfa-c1",
                                "document_id": "alfa-doc",
                                "text": "SEGREDO sintético alfa.",
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
                                "text": "SEGREDO sintético beta.",
                            }
                        ],
                    },
                ],
            },
            "cases": [
                {
                    "id": "valid",
                    "category": "valid_control",
                    "mutation": "none",
                    "expected": {"accepted": True},
                },
                {
                    "id": "blocked",
                    "category": "status",
                    "mutation": "non_ready_status",
                    "expected": {
                        "accepted": False,
                        "error": (
                            "compiled grounded generation requires ready context"
                        ),
                    },
                },
            ],
        }

        report = evaluate(payload)

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["unsafe_mutation_rejection"], 1.0)
        self.assertNotIn("SEGREDO", str(report))

    def test_evaluation_rejects_a_noop_mutation(self) -> None:
        payload = {
            "base_context": {
                "question": "Compare alfa e beta.",
                "evidence_groups": [
                    {
                        "step_id": "alfa",
                        "scope": "alfa",
                        "evidence": [
                            {
                                "evidence_id": "alfa-c1",
                                "document_id": "alfa-doc",
                                "text": "Fato sintético alfa.",
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
                                "text": "Fato sintético beta.",
                            }
                        ],
                    },
                ],
            },
            "cases": [
                {
                    "id": "noop",
                    "category": "harness",
                    "mutation": "reversed_group_evidence",
                    "expected": {"accepted": False},
                }
            ],
        }

        with self.assertRaisesRegex(ValueError, "mutation produced no change"):
            evaluate(payload)

    def test_synthetic_bundle_preserves_optional_provenance(self) -> None:
        bundle = build_bundle(
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
                                "page": 7,
                                "section": "Seção sintética",
                                "text": "Fato sintético alfa.",
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
                                "text": "Fato sintético beta.",
                            }
                        ],
                    },
                ],
            }
        )

        location = bundle.groups[0].evidence[0].location
        self.assertEqual(location.page, 7)
        self.assertEqual(location.section, "Seção sintética")


if __name__ == "__main__":
    unittest.main()
