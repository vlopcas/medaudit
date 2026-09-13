import unittest

from medaudit.evaluation.decomposed_grounding import evaluate


class DecomposedGroundingEvaluationTest(unittest.TestCase):
    def test_requires_cases(self) -> None:
        with self.assertRaises(KeyError):
            evaluate({})
