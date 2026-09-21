import asyncio
import unittest
from pathlib import Path

from medaudit.evaluation.structured_verifier_application import (
    evaluate,
    load_dataset,
)


class StructuredVerifierApplicationTest(unittest.TestCase):
    def test_development_dataset_matches_expected_application_outcomes(self) -> None:
        report = asyncio.run(
            evaluate(
                load_dataset(
                    Path(
                        "data/synthetic_cases/"
                        "structured_verifier_application_development.json"
                    )
                )
            )
        )

        self.assertEqual(report["case_count"], 7)
        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["release_safety"], 1.0)


if __name__ == "__main__":
    unittest.main()
