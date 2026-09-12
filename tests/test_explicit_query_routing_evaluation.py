import unittest

from medaudit.evaluation.explicit_query_routing import evaluate


class ExplicitQueryRoutingEvaluationTest(unittest.TestCase):
    def test_reports_accuracy_by_expected_route(self) -> None:
        report = evaluate(
            [
                {
                    "id": "decompose",
                    "query": "Compare a regra alfa com a beta.",
                    "route": "requires_decomposition",
                },
                {
                    "id": "direct",
                    "query": "Consulte a regra alfa.",
                    "route": "direct_retrieval",
                },
            ]
        )

        self.assertEqual(report["metrics"]["accuracy"], 1.0)
        self.assertEqual(
            report["metrics"]["accuracy_by_expected_route"]["direct_retrieval"],
            1.0,
        )
