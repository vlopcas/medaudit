import asyncio
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from medaudit.evaluation.local_query_understanding import run_benchmark
from medaudit.evaluation.query_understanding import QueryUnderstandingCase
from medaudit.llm import LLMResponse, Usage
from medaudit.query_understanding import QueryIntent


class LocalQueryUnderstandingBenchmarkTest(unittest.TestCase):
    def test_benchmark_does_not_persist_queries_or_model_outputs(self) -> None:
        case = QueryUnderstandingCase(
            case_id="synthetic-case",
            query="private-shaped but synthetic query",
            intent=QueryIntent.GENERAL,
            reference_date=date(2026, 1, 1),
            procedure=None,
            requires_external_data=False,
            requires_decomposition=False,
        )
        analysis = mock.Mock(
            intent=QueryIntent.GENERAL,
            reference_date=date(2026, 1, 1),
            procedure=None,
            requires_external_data=False,
            requires_decomposition=False,
        )
        response = LLMResponse(
            data={},
            model="synthetic",
            latency_ms=2,
            usage=Usage(input_tokens=1, output_tokens=1),
        )
        analyzer = mock.AsyncMock()
        analyzer.analyze.return_value = (analysis, response)

        with (
            mock.patch(
                "medaudit.evaluation.local_query_understanding.load_cases",
                return_value=[case],
            ),
            mock.patch(
                "medaudit.evaluation.local_query_understanding.LlamaCppClient"
            ),
            mock.patch(
                "medaudit.evaluation.local_query_understanding.LocalLLMQueryAnalyzer",
                return_value=analyzer,
            ),
        ):
            report = asyncio.run(
                run_benchmark(Path("synthetic.json"), base_url="http://localhost:8080")
            )

        self.assertEqual(report["metrics"]["exact_match"], 1.0)
        self.assertNotIn("private-shaped", str(report))
