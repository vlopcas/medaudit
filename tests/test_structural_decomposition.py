import unittest

from medaudit.query_understanding import requires_structural_decomposition


class StructuralDecompositionTest(unittest.TestCase):
    def test_detects_repeated_sources_and_explicit_scope(self) -> None:
        positives = (
            "Use o manual alfa e o manual beta.",
            "Informe o prazo de cada documento.",
            "Mostre as normas alfa e beta, respectivamente.",
        )

        for query in positives:
            with self.subTest(query=query):
                self.assertTrue(requires_structural_decomposition(query))

    def test_plural_source_alone_does_not_require_decomposition(self) -> None:
        negatives = (
            "Quais documentos mencionam o prazo?",
            "Liste as regras de cobrança.",
            "Resuma as normas recuperadas.",
        )

        for query in negatives:
            with self.subTest(query=query):
                self.assertFalse(requires_structural_decomposition(query))

