import tempfile
import unittest
from pathlib import Path
from notecove.index import Index
from notecove.ingest import ingest_folder, prune_missing


class MaintenanceTests(unittest.TestCase):
    def test_folder_identity_and_prune(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / "first", root / "second"
            first.mkdir()
            second.mkdir()
            (first / "one.md").write_text("backup files")
            (second / "one.md").write_text("different files")
            index = Index(root / "index.sqlite3")
            try:
                ingest_folder(index, first)
                with self.assertRaises(ValueError):
                    ingest_folder(index, second)
                with self.assertRaises(ValueError):
                    prune_missing(index, second)
                (first / "one.md").unlink()
                self.assertEqual(prune_missing(index, first), ['one.md'])
                self.assertEqual(index.search("backup"), [])
            finally:
                index.close()
