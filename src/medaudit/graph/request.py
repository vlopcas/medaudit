"""Conservative compilation of explicit text into graph traversal requests."""

import re
from dataclasses import dataclass
from enum import StrEnum

from medaudit.graph.models import GraphEntity, TraversalDirection


class GraphRequestStatus(StrEnum):
    """Closed outcomes for the text-to-traversal boundary."""

    READY = "ready"
    NOT_APPLICABLE = "not_applicable"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class GraphTraversalRequest:
    """A traversal request built only from two explicit unique references."""

    start_id: str
    target_id: str
    direction: TraversalDirection
    max_hops: int = 4


@dataclass(frozen=True, slots=True)
class GraphRequestCompilation:
    """Result of conservatively inspecting one natural-language query."""

    status: GraphRequestStatus
    request: GraphTraversalRequest | None = None
    review_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        ready = self.status is GraphRequestStatus.READY
        if ready != (self.request is not None):
            raise ValueError("only ready graph compilations may carry a request")
        review = self.status is GraphRequestStatus.REVIEW
        if review != bool(self.review_references):
            raise ValueError("review compilations require review references")


@dataclass(frozen=True, slots=True)
class ExplicitGraphRequestCompiler:
    """Recognize only explicit path questions over a reviewed entity catalog."""

    entities: tuple[GraphEntity, ...]

    def compile(self, query: str) -> GraphRequestCompilation:
        normalized = query.casefold()
        if "caminho" not in normalized:
            return GraphRequestCompilation(GraphRequestStatus.NOT_APPLICABLE)

        references = self._mentioned_references(query)
        if len(references) != 2:
            return GraphRequestCompilation(
                GraphRequestStatus.REVIEW,
                review_references=("<unresolved-reference-set>",),
            )

        resolved: list[str] = []
        ambiguous: list[str] = []
        for reference, matches in references:
            if len(matches) != 1:
                ambiguous.append(reference)
            else:
                resolved.append(matches[0])
        if ambiguous:
            return GraphRequestCompilation(
                GraphRequestStatus.REVIEW,
                review_references=tuple(ambiguous),
            )

        direction = (
            TraversalDirection.REVERSE
            if "caminho reverso" in normalized
            else TraversalDirection.FORWARD
        )
        return GraphRequestCompilation(
            GraphRequestStatus.READY,
            request=GraphTraversalRequest(
                start_id=resolved[0],
                target_id=resolved[1],
                direction=direction,
            ),
        )

    def _mentioned_references(
        self, query: str
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        mentions: list[tuple[int, int, str, str]] = []
        for entity in self.entities:
            for reference in (entity.entity_id, *entity.aliases):
                match = re.search(
                    rf"(?<!\w){re.escape(reference)}(?!\w)",
                    query,
                    flags=re.IGNORECASE,
                )
                if match is not None:
                    mentions.append(
                        (
                            match.start(),
                            match.end(),
                            reference.casefold(),
                            entity.entity_id,
                        )
                    )

        retained = [
            mention
            for mention in mentions
            if not any(
                other[0] <= mention[0]
                and mention[1] <= other[1]
                and (other[1] - other[0]) > (mention[1] - mention[0])
                for other in mentions
            )
        ]
        candidates: dict[str, set[str]] = {}
        positions: dict[str, int] = {}
        for start, _, key, entity_id in retained:
            candidates.setdefault(key, set()).add(entity_id)
            positions[key] = min(positions.get(key, start), start)
        return tuple(
            (key, tuple(sorted(candidates[key])))
            for key in sorted(candidates, key=positions.__getitem__)
        )
