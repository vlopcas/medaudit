import unittest
from pathlib import Path

from medaudit.evaluation.graph_necessity import evaluate, load_dataset


class GraphNecessityEvaluationTest(unittest.TestCase):
    def test_development_dataset_produces_relational_gap_metrics(self) -> None:
        cases = load_dataset(
            Path("data/synthetic_cases/graph_necessity_development.json")
        )

        report = evaluate(cases)

        self.assertEqual(report["case_count"], 8)
        self.assertGreater(report["metrics"]["candidate_graph_gap_count"], 0)
        self.assertLessEqual(report["metrics"]["bm25_complete_chain_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
