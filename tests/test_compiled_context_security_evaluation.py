import unittest

from medaudit.evaluation.compiled_context_security import evaluate


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


if __name__ == "__main__":
    unittest.main()
