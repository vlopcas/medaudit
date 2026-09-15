import unittest

from medaudit.evaluation.compiled_context_gateway import evaluate


class CompiledContextGatewayEvaluationTest(unittest.TestCase):
    def test_report_omits_input_content_and_identifiers(self) -> None:
        case = {
            "id": "gateway-case",
            "category": "prepared",
            "mode": "experimental",
            "token_budget": 100,
            "question": "CONSULTA_SECRETA compare alfa e beta.",
            "evidence_groups": [
                {
                    "step_id": "alfa",
                    "scope": "alfa",
                    "evidence": [
                        {
                            "evidence_id": "ID_SECRETO_ALFA",
                            "document_id": "DOC_SECRETO_ALFA",
                            "text": "TEXTO_SECRETO alfa.",
                        }
                    ],
                },
                {
                    "step_id": "beta",
                    "scope": "beta",
                    "evidence": [
                        {
                            "evidence_id": "ID_SECRETO_BETA",
                            "document_id": "DOC_SECRETO_BETA",
                            "text": "TEXTO_SECRETO beta.",
                        }
                    ],
                },
            ],
            "expected": {
                "status": "prepared",
                "context_status": "ready",
                "failure_code": None,
                "request_present": True,
                "item_count": 4,
                "group_count": 2,
                "exclusion_count": 0,
            },
        }

        report = evaluate([case])
        rendered = str(report)

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["request_safety"], 1.0)
        self.assertNotIn("CONSULTA_SECRETA", rendered)
        self.assertNotIn("TEXTO_SECRETO", rendered)
        self.assertNotIn("ID_SECRETO", rendered)
        self.assertNotIn("DOC_SECRETO", rendered)


if __name__ == "__main__":
    unittest.main()
