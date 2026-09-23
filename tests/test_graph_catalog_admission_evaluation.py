import unittest
from pathlib import Path

from medaudit.evaluation.graph_catalog_admission import evaluate, load_dataset


class GraphCatalogAdmissionEvaluationTest(unittest.TestCase):
    def test_development_cases_match_expected_admission(self) -> None:
        payload = load_dataset(
            Path("data/synthetic_cases/graph_catalog_admission_development.json")
        )

        report = evaluate(payload)

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["passed"], 10)


if __name__ == "__main__":
    unittest.main()
