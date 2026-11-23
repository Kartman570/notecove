import tempfile
import unittest
from pathlib import Path
from notecove.index import Index
from notecove.ingest import ingest_folder


class IngestTests(unittest.TestCase):
    def test_reindex_and_skip_unsafe_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            notes = root / "notes"
            notes.mkdir()
            (notes / "a.md").write_text("A backup lives on another disk.")
            (notes / "bad.txt").write_bytes(b"\xff")
            (notes / ".secret.txt").write_text("private")
            (root / "outside.txt").write_text("outside")
            (notes / "link.txt").symlink_to(root / "outside.txt")
            index = Index(root / "index.sqlite3")
            try:
                self.assertEqual(ingest_folder(index, notes), {"updated": 1, "unchanged": 0, "skipped": 1})
                self.assertEqual(ingest_folder(index, notes)["unchanged"], 1)
                self.assertEqual(index.search("private outside"), [])
            finally:
                index.close()
