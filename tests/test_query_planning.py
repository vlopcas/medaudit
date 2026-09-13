import unittest
from datetime import date

from medaudit.query_understanding import (
    DeterministicQueryPlanner,
    QueryPlanStatus,
    QueryPlanStrategy,
)


class DeterministicQueryPlannerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.planner = DeterministicQueryPlanner()

    def test_builds_one_step_for_each_explicit_date(self) -> None:
        query = "O que mudou entre 01/03/2026 e 2026-07-01?"

        plan = self.planner.plan(query)

        self.assertEqual(plan.status, QueryPlanStatus.READY)
        self.assertEqual(plan.strategy, QueryPlanStrategy.TEMPORAL_SNAPSHOTS)
        self.assertEqual(
            tuple(step.reference_date for step in plan.steps),
            (date(2026, 3, 1), date(2026, 7, 1)),
        )
        self.assertEqual({step.query for step in plan.steps}, {query})

    def test_builds_scoped_steps_for_explicit_comparison(self) -> None:
        plan = self.planner.plan("Compare a regra alfa com a regra beta.")

        self.assertEqual(plan.status, QueryPlanStatus.READY)
        self.assertEqual(plan.strategy, QueryPlanStrategy.COMPARISON_SCOPES)
        self.assertEqual(
            tuple(step.scope for step in plan.steps),
            ("a regra alfa", "a regra beta"),
        )

    def test_ambiguous_comparison_requests_clarification(self) -> None:
        plan = self.planner.plan("Faça uma comparação das regras alfa e beta.")

        self.assertEqual(plan.status, QueryPlanStatus.NEEDS_CLARIFICATION)
        self.assertIsNone(plan.strategy)
        self.assertEqual(plan.steps, ())

    def test_rejects_query_outside_decomposition_route(self) -> None:
        with self.assertRaisesRegex(ValueError, "not routed"):
            self.planner.plan("Consulte a regra alfa.")
