import unittest

from medaudit.evaluation.routed_compiled_integration import evaluate


class RoutedCompiledIntegrationEvaluationTest(unittest.TestCase):
    def test_report_omits_query_and_retrieval_identifiers(self) -> None:
        case = {
            "id": "integration-case",
            "category": "direct",
            "query": "CONSULTA_SECRETA sobre alfa.",
            "expected": {
                "route": "direct_retrieval",
                "execution_present": False,
                "bundle_present": False,
                "preparation_present": False,
                "preparation_status": None,
                "context_status": None,
                "request_present": False,
            },
        }

        report = evaluate([case])
        rendered = str(report)

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertNotIn("CONSULTA_SECRETA", rendered)
        self.assertNotIn("chunk-alpha", rendered)
        self.assertNotIn("document-alpha", rendered)


if __name__ == "__main__":
    unittest.main()
