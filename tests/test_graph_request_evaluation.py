import unittest
from pathlib import Path

from medaudit.evaluation.graph_request import evaluate, load_dataset


class GraphRequestEvaluationTest(unittest.TestCase):
    def test_development_dataset_matches_expected_compilations(self) -> None:
        payload = load_dataset(
            Path("data/synthetic_cases/graph_request_development.json")
        )

        report = evaluate(payload)

        self.assertEqual(report["metrics"]["exact_match"], 1.0)


if __name__ == "__main__":
    unittest.main()
