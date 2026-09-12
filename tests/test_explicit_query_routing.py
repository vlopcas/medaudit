import unittest

from medaudit.query_understanding import ExplicitQueryRouter, QueryRoute


class ExplicitQueryRouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = ExplicitQueryRouter()

    def test_routes_explicit_comparison_to_decomposition(self) -> None:
        route = self.router.route("Compare a regra alfa com a regra beta.")

        self.assertEqual(route, QueryRoute.REQUIRES_DECOMPOSITION)

    def test_routes_two_dates_to_decomposition(self) -> None:
        route = self.router.route("Qual regra valia em 01/01/2026 e 2026-07-01?")

        self.assertEqual(route, QueryRoute.REQUIRES_DECOMPOSITION)

    def test_keeps_implicit_multi_source_query_in_direct_retrieval(self) -> None:
        route = self.router.route("Consolide os documentos alfa e beta.")

        self.assertEqual(route, QueryRoute.DIRECT_RETRIEVAL)

    def test_external_dependency_takes_precedence(self) -> None:
        route = self.router.route("Compare o preço atual no portal externo.")

        self.assertEqual(route, QueryRoute.REQUIRES_EXTERNAL_DATA)
