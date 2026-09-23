import unittest

from medaudit.graph import (
    ExplicitGraphRequestCompiler,
    GraphEntity,
    GraphRequestStatus,
    TraversalDirection,
)


def make_compiler() -> ExplicitGraphRequestCompiler:
    return ExplicitGraphRequestCompiler(
        entities=(
            GraphEntity("PX-A", "procedure", aliases=("PROCEDIMENTO AZUL",)),
            GraphEntity("RULE-1", "rule", aliases=("REGRA UM",)),
            GraphEntity("ALFA-1", "item", aliases=("ALFA",)),
            GraphEntity("ALFA-2", "item", aliases=("ALFA",)),
        )
    )


class ExplicitGraphRequestCompilerTest(unittest.TestCase):
    def test_compiles_two_canonical_ids_in_mention_order(self) -> None:
        result = make_compiler().compile("Qual o caminho de PX-A até RULE-1?")

        self.assertEqual(result.status, GraphRequestStatus.READY)
        assert result.request is not None
        self.assertEqual(result.request.start_id, "PX-A")
        self.assertEqual(result.request.target_id, "RULE-1")

    def test_compiles_unique_aliases(self) -> None:
        result = make_compiler().compile(
            "Mostre o caminho de procedimento azul até regra um."
        )

        self.assertEqual(result.status, GraphRequestStatus.READY)

    def test_requires_explicit_path_intent(self) -> None:
        result = make_compiler().compile("Compare PX-A e RULE-1.")

        self.assertEqual(result.status, GraphRequestStatus.NOT_APPLICABLE)

    def test_ambiguous_alias_requires_review(self) -> None:
        result = make_compiler().compile("Qual o caminho de ALFA até RULE-1?")

        self.assertEqual(result.status, GraphRequestStatus.REVIEW)
        self.assertEqual(result.review_references, ("alfa",))

    def test_longer_canonical_id_is_not_shadowed_by_alias(self) -> None:
        result = make_compiler().compile("Qual o caminho de ALFA-1 até RULE-1?")

        self.assertEqual(result.status, GraphRequestStatus.READY)
        assert result.request is not None
        self.assertEqual(result.request.start_id, "ALFA-1")

    def test_incomplete_reference_set_requires_review(self) -> None:
        result = make_compiler().compile("Qual o caminho a partir de PX-A?")

        self.assertEqual(result.status, GraphRequestStatus.REVIEW)

    def test_explicit_reverse_path_sets_direction(self) -> None:
        result = make_compiler().compile(
            "Qual o caminho reverso de RULE-1 até PX-A?"
        )

        assert result.request is not None
        self.assertEqual(result.request.direction, TraversalDirection.REVERSE)


if __name__ == "__main__":
    unittest.main()
