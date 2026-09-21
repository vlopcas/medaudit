import unittest
from pathlib import Path

from medaudit.evaluation.structured_fact_verifier import evaluate, load_dataset


class StructuredFactVerifierTest(unittest.TestCase):
    def test_development_dataset_matches_expected_decisions(self) -> None:
        report = evaluate(
            load_dataset(
                Path(
                    "data/synthetic_cases/structured_fact_verifier_development.json"
                )
            )
        )

        self.assertEqual(report["case_count"], 10)
        self.assertEqual(report["metrics"]["exact_match"], 1.0)


if __name__ == "__main__":
    unittest.main()
