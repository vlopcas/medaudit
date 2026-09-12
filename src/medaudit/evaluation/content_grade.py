"""Transparent lexical grading for wholly synthetic generated answers."""

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ContentGrade:
    """Aggregate-safe result of checking explicit expected concepts."""

    correct: bool
    matched_concept_count: int
    concept_count: int


def normalize_answer(text: str) -> str:
    """Normalize accents, case and punctuation for deterministic matching."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", ascii_text))


def grade_expected_content(answer: str, expected: dict[str, Any]) -> ContentGrade:
    """Require at least one lexical alternative from every concept group."""
    groups = expected.get("required_concepts")
    if not isinstance(groups, list) or not groups:
        raise ValueError("answered case requires expected concept groups")
    normalized_answer = normalize_answer(answer)
    matched = 0
    for group in groups:
        if not isinstance(group, list) or not group or not all(
            isinstance(alternative, str) and alternative.strip()
            for alternative in group
        ):
            raise ValueError("expected concept group must contain text alternatives")
        alternatives = [normalize_answer(alternative) for alternative in group]
        matched += any(alternative in normalized_answer for alternative in alternatives)
    return ContentGrade(
        correct=matched == len(groups),
        matched_concept_count=matched,
        concept_count=len(groups),
    )
