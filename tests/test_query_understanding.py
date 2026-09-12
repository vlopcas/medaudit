import unittest
from datetime import date

from medaudit.query_understanding import DeterministicQueryAnalyzer, QueryIntent


class DeterministicQueryAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = DeterministicQueryAnalyzer()

    def test_normalizes_and_extracts_audit_signals(self) -> None:
        result = self.analyzer.analyze(
            "  O procedimento 12345678 tinha cobertura em 12/06/2026?  "
        )

        self.assertEqual(result.intent, QueryIntent.AUDIT_CASE)
        self.assertEqual(
            result.normalized_query,
            "O procedimento 12345678 tinha cobertura em 12/06/2026?",
        )
        self.assertEqual(result.reference_date, date(2026, 6, 12))
        self.assertEqual(result.procedure, "12345678")
        self.assertEqual(result.entities, ("procedure:12345678",))
        self.assertFalse(result.requires_decomposition)

    def test_recognizes_accented_comparison_as_decomposition(self) -> None:
        result = self.analyzer.analyze(
            "Compare a regra sintética A com a regra sintética B."
        )

        self.assertEqual(result.intent, QueryIntent.COMPARISON)
        self.assertTrue(result.requires_decomposition)

    def test_external_data_takes_precedence(self) -> None:
        result = self.analyzer.analyze(
            "Consulte o preço atual deste procedimento no sistema externo."
        )

        self.assertEqual(result.intent, QueryIntent.EXTERNAL_LOOKUP)
        self.assertTrue(result.requires_external_data)

    def test_recognizes_observed_paraphrases(self) -> None:
        comparison = self.analyzer.analyze(
            "Quais mudanças ocorreram da regra sintética A para a B?"
        )
        external = self.analyzer.analyze(
            "Qual é o valor vigente informado hoje pelo portal?"
        )
        decomposition = self.analyzer.analyze(
            "Relacione as exigências de dois documentos sintéticos."
        )

        self.assertEqual(comparison.intent, QueryIntent.COMPARISON)
        self.assertTrue(comparison.requires_decomposition)
        self.assertEqual(external.intent, QueryIntent.EXTERNAL_LOOKUP)
        self.assertTrue(external.requires_external_data)
        self.assertTrue(decomposition.requires_decomposition)

    def test_two_dates_require_decomposition_without_choosing_one(self) -> None:
        result = self.analyzer.analyze(
            "Qual regra valia em 2026-01-01 e também em 01/07/2026?"
        )

        self.assertIsNone(result.reference_date)
        self.assertTrue(result.requires_decomposition)

    def test_rejects_invalid_date(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid date"):
            self.analyzer.analyze("Qual regra valia em 31/02/2026?")

    def test_rejects_blank_query(self) -> None:
        with self.assertRaisesRegex(ValueError, "blank"):
            self.analyzer.analyze("  \n ")
