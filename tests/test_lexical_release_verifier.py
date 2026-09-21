import unittest
from pathlib import Path

from medaudit.evaluation.lexical_release_verifier import evaluate, load_dataset
from medaudit.rag import ConservativeLexicalVerifier


class LexicalReleaseVerifierTest(unittest.TestCase):
    def test_development_metrics_are_explicit(self) -> None:
        report = evaluate(
            load_dataset(
                Path(
                    "data/synthetic_cases/lexical_release_verifier_development.json"
                )
            )
        )

        self.assertEqual(report["case_count"], 6)
        self.assertGreater(report["metrics"]["safe_release_rate"], 0.0)
        self.assertGreater(report["metrics"]["unsafe_block_rate"], 0.0)

    def test_threshold_must_be_a_probability(self) -> None:
        with self.assertRaises(ValueError):
            ConservativeLexicalVerifier(minimum_claim_coverage=0)
        with self.assertRaises(ValueError):
            ConservativeLexicalVerifier(minimum_claim_coverage=1.1)


if __name__ == "__main__":
    unittest.main()
