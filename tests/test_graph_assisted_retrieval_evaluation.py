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


if __name__ == "__main__":
    unittest.main()
