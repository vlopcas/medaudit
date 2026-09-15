import unittest

from medaudit.evaluation.context_compilation import evaluate


class ContextCompilationEvaluationTest(unittest.TestCase):
    def test_report_contains_decisions_but_not_evidence_text(self) -> None:
        report = evaluate(
            [
                {
                    "id": "case",
                    "category": "ready",
                    "question": "Compare alfa e beta.",
                    "instruction": "Responda com suporte.",
                    "token_budget": 20,
                    "evidence_groups": [
                        {
                            "step_id": "alfa",
                            "scope": "alfa",
                            "evidence": [
                                {
                                    "evidence_id": "alfa-c1",
                                    "document_id": "alfa-doc",
                                    "text": "SEGREDO alfa sintético.",
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
                                    "text": "SEGREDO beta sintético.",
                                }
                            ],
                        },
                    ],
                    "expected": {
                        "status": "ready",
                        "included_evidence_ids": ["alfa-c1", "beta-c1"],
                        "evidence_steps": {
                            "alfa-c1": ["alfa"],
                            "beta-c1": ["beta"],
                        },
                        "exclusion_reasons": [],
                    },
                }
            ]
        )

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertNotIn("SEGREDO", str(report))


if __name__ == "__main__":
    unittest.main()
