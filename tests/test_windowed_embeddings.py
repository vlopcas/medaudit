import unittest

import numpy as np

from medaudit.retrieval.embeddings import mean_window_embeddings, token_windows


class WindowedEmbeddingsTest(unittest.TestCase):
    def test_creates_overlapping_token_windows(self) -> None:
        windows = token_windows(list(range(10)), capacity=4, overlap=1)

        self.assertEqual(windows, [[0, 1, 2, 3], [3, 4, 5, 6], [6, 7, 8, 9]])

    def test_means_windows_and_normalizes_each_passage(self) -> None:
        vectors = np.asarray(
            [[1.0, 0.0], [0.0, 1.0], [0.0, 1.0]], dtype=np.float32
        )

        means = mean_window_embeddings(vectors, owners=[0, 0, 1], passage_count=2)

        self.assertTrue(np.allclose(means[0], [2**-0.5, 2**-0.5]))
        self.assertTrue(np.allclose(means[1], [0.0, 1.0]))
