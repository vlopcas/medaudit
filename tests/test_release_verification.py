import asyncio
import unittest
from pathlib import Path

from medaudit.evaluation.release_verification import evaluate, load_dataset
from medaudit.rag import (
    VerificationCode,
    VerificationDecision,
    VerificationResult,
)


class ReleaseVerificationTest(unittest.TestCase):
    def test_development_dataset_matches_every_expected_flow(self) -> None:
        cases = load_dataset(
            Path("data/synthetic_cases/release_verification_development.json")
        )

        report = asyncio.run(evaluate(cases))

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertEqual(report["metrics"]["release_safety"], 1.0)

    def test_non_release_requires_a_fixed_reason_code(self) -> None:
        with self.assertRaises(ValueError):
            VerificationResult(VerificationDecision.REJECT)
        with self.assertRaises(ValueError):
            VerificationResult(
                VerificationDecision.RELEASE,
                VerificationCode.UNTRUSTED_CONTENT,
            )


if __name__ == "__main__":
    unittest.main()
