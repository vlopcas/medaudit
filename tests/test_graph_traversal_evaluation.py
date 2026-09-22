import unittest
from pathlib import Path

from medaudit.evaluation.graph_traversal import evaluate, load_dataset


class GraphTraversalEvaluationTest(unittest.TestCase):
    def test_development_dataset_matches_paths_and_controls(self) -> None:
        cases = load_dataset(
            Path("data/synthetic_cases/graph_traversal_development.json")
        )

        report = evaluate(cases)

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["candidate_gap_recovery"], 1.0)
        self.assertTrue(report["metrics"]["provenance_complete"])


if __name__ == "__main__":
    unittest.main()
