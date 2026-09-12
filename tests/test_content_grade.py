import tempfile
import unittest
from pathlib import Path

from medaudit.evaluation.content_grade import grade_expected_content, normalize_answer
from medaudit.evaluation.local_llm_benchmark import verify_input


class ContentGradeTest(unittest.TestCase):
    def test_normalizes_accents_case_and_punctuation(self) -> None:
        self.assertEqual(
            normalize_answer("NÃO: PX-101, autorização prévia!"),
            "nao px-101 autorizacao previa",
        )

    def test_accepts_one_alternative_from_every_concept(self) -> None:
        grade = grade_expected_content(
            "O limite do EX-220 é 2 unidades.",
            {"required_concepts": [["EX-220"], ["duas", "2"]]},
        )

        self.assertTrue(grade.correct)
        self.assertEqual(grade.matched_concept_count, 2)

    def test_reports_incomplete_answer_without_retaining_text(self) -> None:
        grade = grade_expected_content(
            "Prazo de trinta dias.",
            {"required_concepts": [["trinta"], ["dias corridos"], ["glosa"]]},
        )

        self.assertFalse(grade.correct)
        self.assertEqual(grade.matched_concept_count, 1)
        self.assertEqual(grade.concept_count, 3)

    def test_rejects_empty_concept_configuration(self) -> None:
        with self.assertRaisesRegex(ValueError, "concept groups"):
            grade_expected_content("Synthetic answer", {"required_concepts": []})

    def test_verifies_frozen_benchmark_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            path.write_text("synthetic", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                verify_input(path, "0" * 64)
