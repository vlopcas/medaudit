import unittest
from dataclasses import replace

from medaudit.query_understanding import (
    ConservativeQueryRouter,
    DeterministicQueryAnalyzer,
    QueryRoute,
    expected_route,
)


class ConservativeQueryRouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = DeterministicQueryAnalyzer()
        self.router = ConservativeQueryRouter()

    def test_external_block_depends_only_on_deterministic_signal(self) -> None:
        query = "O que consta no manual sintético?"
        semantic = self.analyzer.analyze(query)
        semantic = replace(semantic, requires_external_data=True)

        route = self.router.route(query, semantic)

        self.assertEqual(route, QueryRoute.DIRECT_RETRIEVAL)

    def test_semantic_signal_can_request_decomposition(self) -> None:
        query = "Consolide as condições das fontes alfa e beta."
        semantic = self.analyzer.analyze(query)
        semantic = replace(semantic, requires_decomposition=True)

        self.assertEqual(
            self.router.route(query, semantic), QueryRoute.REQUIRES_DECOMPOSITION
        )

    def test_external_route_has_precedence(self) -> None:
        self.assertEqual(
            expected_route(
                requires_external_data=True,
                requires_decomposition=True,
            ),
            QueryRoute.REQUIRES_EXTERNAL_DATA,
        )
