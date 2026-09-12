"""Layered routing that keeps safety decisions deterministic."""

from medaudit.query_understanding.analyzer import (
    DeterministicQueryAnalyzer,
    count_explicit_dates,
)
from medaudit.query_understanding.models import QueryAnalysis, QueryIntent, QueryRoute


class ConservativeQueryRouter:
    """Separate external-data blocking from advisory semantic planning."""

    def __init__(self) -> None:
        self._deterministic = DeterministicQueryAnalyzer()

    def route(self, query: str, semantic: QueryAnalysis) -> QueryRoute:
        """Choose a route without allowing the LLM to trigger external access."""
        deterministic = self._deterministic.analyze(query)
        if deterministic.requires_external_data:
            return QueryRoute.REQUIRES_EXTERNAL_DATA
        if (
            deterministic.requires_decomposition
            or semantic.requires_decomposition
        ):
            return QueryRoute.REQUIRES_DECOMPOSITION
        return QueryRoute.DIRECT_RETRIEVAL


class ExplicitQueryRouter:
    """Runtime candidate restricted to high-precision deterministic signals."""

    def __init__(self) -> None:
        self._analyzer = DeterministicQueryAnalyzer()

    def route(self, query: str) -> QueryRoute:
        """Route only explicit comparison, multiple dates or external needs."""
        analysis = self._analyzer.analyze(query)
        if analysis.requires_external_data:
            return QueryRoute.REQUIRES_EXTERNAL_DATA
        if analysis.intent is QueryIntent.COMPARISON or count_explicit_dates(query) > 1:
            return QueryRoute.REQUIRES_DECOMPOSITION
        return QueryRoute.DIRECT_RETRIEVAL


def expected_route(
    *, requires_external_data: bool, requires_decomposition: bool
) -> QueryRoute:
    """Apply the documented precedence to golden labels."""
    if requires_external_data:
        return QueryRoute.REQUIRES_EXTERNAL_DATA
    if requires_decomposition:
        return QueryRoute.REQUIRES_DECOMPOSITION
    return QueryRoute.DIRECT_RETRIEVAL
