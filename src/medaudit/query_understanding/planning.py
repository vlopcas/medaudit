"""Conservative deterministic planning for explicitly decomposable queries."""

import re

from medaudit.query_understanding.analyzer import extract_explicit_dates
from medaudit.query_understanding.models import (
    QueryPlan,
    QueryPlanStatus,
    QueryPlanStep,
    QueryPlanStrategy,
    QueryRoute,
)
from medaudit.query_understanding.routing import ExplicitQueryRouter

_TRAILING_PUNCTUATION = re.compile(r"[.!?]+$")
_COMPARISON_PATTERNS = (
    re.compile(r"^(?:compare|comparar)\s+(.+?)\s+com\s+(.+?)$", re.IGNORECASE),
    re.compile(
        r"^(?:qual\s+(?:é|e)\s+a\s+)?diferen[çc]a\s+entre\s+(.+?)\s+e\s+(.+?)$",
        re.IGNORECASE,
    ),
    re.compile(r"^(.+?)\s+versus\s+(.+?)$", re.IGNORECASE),
)


class DeterministicQueryPlanner:
    """Create only temporal or syntactically explicit comparison plans."""

    def __init__(self) -> None:
        self._router = ExplicitQueryRouter()

    def plan(self, query: str) -> QueryPlan:
        """Plan an explicitly decomposable query or request clarification."""
        normalized = " ".join(query.split())
        if self._router.route(normalized) is not QueryRoute.REQUIRES_DECOMPOSITION:
            raise ValueError("query is not routed to decomposition")

        dates = extract_explicit_dates(normalized)
        if len(dates) > 1:
            return QueryPlan(
                original_query=query,
                status=QueryPlanStatus.READY,
                strategy=QueryPlanStrategy.TEMPORAL_SNAPSHOTS,
                steps=tuple(
                    QueryPlanStep(
                        step_id=f"temporal-{index}",
                        query=normalized,
                        reference_date=reference_date,
                    )
                    for index, reference_date in enumerate(dates, start=1)
                ),
            )

        scopes = _extract_comparison_scopes(normalized)
        if scopes is None:
            return QueryPlan(
                original_query=query,
                status=QueryPlanStatus.NEEDS_CLARIFICATION,
                strategy=None,
                steps=(),
            )
        return QueryPlan(
            original_query=query,
            status=QueryPlanStatus.READY,
            strategy=QueryPlanStrategy.COMPARISON_SCOPES,
            steps=tuple(
                QueryPlanStep(
                    step_id=f"comparison-{index}",
                    query=scope,
                    scope=scope,
                )
                for index, scope in enumerate(scopes, start=1)
            ),
        )


def _extract_comparison_scopes(query: str) -> tuple[str, str] | None:
    candidate = _TRAILING_PUNCTUATION.sub("", query).strip()
    for pattern in _COMPARISON_PATTERNS:
        match = pattern.fullmatch(candidate)
        if match is None:
            continue
        left, right = (part.strip(" ,;:") for part in match.groups())
        if left and right:
            return left, right
    return None
