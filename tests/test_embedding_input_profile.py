import unittest

from medaudit.evaluation.embedding_input_profile import summarize_token_lengths


class EmbeddingInputProfileTest(unittest.TestCase):
    def test_summarizes_lengths_and_strict_truncation_boundary(self) -> None:
        report = summarize_token_lengths([10, 20, 30, 40, 60], maximum=40)

        self.assertEqual(report["length_tokens"]["p50"], 30)
        self.assertEqual(report["length_tokens"]["p95"], 60)
        self.assertEqual(report["truncated_chunk_count"], 1)
        self.assertEqual(report["truncated_chunk_rate"], 0.2)

    def test_rejects_invalid_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive"):
            summarize_token_lengths([1, 0], maximum=512)
