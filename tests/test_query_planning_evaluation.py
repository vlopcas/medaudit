import unittest

from medaudit.evaluation.query_planning import evaluate


class QueryPlanningEvaluationTest(unittest.TestCase):
    def test_reports_exact_match_by_expected_status(self) -> None:
        report = evaluate(
            [
                {
                    "id": "ready",
                    "query": "Regra alfa versus regra beta.",
                    "status": "ready",
                    "strategy": "comparison_scopes",
                    "step_count": 2,
                    "scopes": ["Regra alfa", "regra beta"],
                },
                {
                    "id": "clarify",
                    "query": "Faça uma comparação geral.",
                    "status": "needs_clarification",
                    "step_count": 0,
                },
            ]
        )

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(
            report["metrics"]["exact_match_by_expected_status"],
            {"needs_clarification": 1.0, "ready": 1.0},
        )
