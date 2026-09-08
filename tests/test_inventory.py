import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from medaudit.ingestion.inventory import collect_inventory, main


class InventoryTest(unittest.TestCase):
    def test_collect_inventory_only_includes_supported_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            content = b"synthetic document"
            (tmp_path / "example.pdf").write_bytes(content)
            (tmp_path / "notes.txt").write_text("synthetic", encoding="utf-8")

            records = collect_inventory(tmp_path)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].relative_path, "example.pdf")
            self.assertEqual(records[0].sha256, hashlib.sha256(content).hexdigest())

    def test_cli_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source = tmp_path / "source"
            output = tmp_path / "manifest.local.json"
            source.mkdir()
            (source / "table.xlsx").write_bytes(b"synthetic spreadsheet")

            self.assertEqual(
                main(["--input", str(source), "--output", str(output)]), 0
            )
            manifest = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["document_count"], 1)
            self.assertEqual(
                manifest["documents"][0]["relative_path"], "table.xlsx"
            )
