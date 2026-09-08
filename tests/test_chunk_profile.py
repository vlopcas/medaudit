import json
import tempfile
import unittest
from pathlib import Path

from medaudit.ingestion.chunk_profile import profile_chunks, write_chunk_profile


class ChunkProfileTest(unittest.TestCase):
    def test_profiles_lengths_and_provenance_without_text(self) -> None:
        records = [
            self.record("application/pdf", "abc", page=1),
            self.record("application/pdf", "abcdefgh", section="Rules"),
            self.record("application/vnd.ms-excel", "abcde"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "chunks.local.jsonl"
            source.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )

            report = profile_chunks(source)

        self.assertEqual(report["chunk_count"], 3)
        self.assertEqual(report["length_characters"]["p50"], 5)
        self.assertEqual(report["length_characters"]["p95"], 8)
        self.assertEqual(report["chunks_by_media_type"]["application/pdf"], 2)
        self.assertEqual(report["chunks_with_page"], 1)
        self.assertNotIn("abc", json.dumps(report))

    def test_profile_output_requires_private_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "must end with .local.json"):
                write_chunk_profile({}, Path(directory) / "profile.json")

    @staticmethod
    def record(
        media_type: str,
        text: str,
        *,
        page: int | None = None,
        section: str | None = None,
    ) -> dict[str, object]:
        return {
            "schema_version": 1,
            "document": {"media_type": media_type},
            "chunk": {
                "text": text,
                "page": page,
                "section": section,
                "metadata": {"strategy": "structure-aware-v1"},
            },
        }
