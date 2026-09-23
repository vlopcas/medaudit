import unittest
from pathlib import Path

from medaudit.evaluation.graph_assisted_retrieval import evaluate, load_dataset


class GraphAssistedRetrievalEvaluationTest(unittest.TestCase):
    def test_graph_and_bm25_use_the_same_queries(self) -> None:
        cases = load_dataset(
            Path(
                "data/synthetic_cases/"
                "graph_assisted_retrieval_development.json"
            )
        )

        report = evaluate(cases)

        self.assertEqual(report["metrics"]["graph_complete_chain_rate"], 1.0)
        self.assertLess(
            report["metrics"]["bm25_complete_chain_rate"],
            report["metrics"]["graph_complete_chain_rate"],
        )
        self.assertEqual(report["metrics"]["control_exact_match"], 1.0)
        self.assertTrue(report["metrics"]["graph_provenance_complete"])
        self.assertEqual(report["metrics"]["exact_match"], 1.0)

    def test_loader_rejects_unexpected_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported"):
            load_dataset(
                Path(
                    "data/synthetic_cases/"
                    "graph_assisted_retrieval_development.json"
                ),
                expected_policy="graph-assisted-retrieval-holdout-v1",
            )

    def test_holdout_schema_is_frozen_under_its_own_policy(self) -> None:
        cases = load_dataset(
            Path(
                "data/synthetic_cases/"
                "graph_assisted_retrieval_holdout.json"
            ),
            expected_policy="graph-assisted-retrieval-holdout-v1",
        )

        self.assertEqual(len(cases), 8)


if __name__ == "__main__":
    unittest.main()
