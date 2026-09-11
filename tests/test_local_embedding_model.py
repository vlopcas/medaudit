import unittest

from medaudit.retrieval.local_model import MODEL_ID, MODEL_REVISION


class LocalEmbeddingModelTest(unittest.TestCase):
    def test_model_and_revision_are_pinned(self) -> None:
        self.assertEqual(MODEL_ID, "intfloat/multilingual-e5-base")
        self.assertRegex(MODEL_REVISION, r"^[0-9a-f]{40}$")
