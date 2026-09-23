import unittest
from pathlib import Path

from medaudit.evaluation.graph_catalog_publication import evaluate, load_dataset


class GraphCatalogPublicationEvaluationTest(unittest.TestCase):
    def test_development_cases_match_expected_publication(self) -> None:
        payload = load_dataset(
            Path("data/synthetic_cases/graph_catalog_publication_development.json")
        )

        report = evaluate(payload)

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["passed"], 12)

    def test_loader_rejects_unexpected_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            load_dataset(
                Path(
                    "data/synthetic_cases/"
                    "graph_catalog_publication_development.json"
                ),
                expected_policy="graph-catalog-publication-holdout-v1",
            )

    def test_holdout_schema_is_frozen_under_its_own_policy(self) -> None:
        payload = load_dataset(
            Path("data/synthetic_cases/graph_catalog_publication_holdout.json"),
            expected_policy="graph-catalog-publication-holdout-v1",
        )

        self.assertEqual(len(payload["cases"]), 8)


if __name__ == "__main__":
    unittest.main()
