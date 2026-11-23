import tempfile
import unittest
from pathlib import Path
from notecove.index import Index
from notecove.answers import answer


class StaticResponse:
    def __init__(self, text):
        self.text = text

    def chat(self, messages):
        return self.text


class AnswerTests(unittest.TestCase):
    def test_references_and_no_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Index(Path(directory) / "index.sqlite3")
            try:
                index.put("backup.md", "Make a backup before restoring files.")
                self.assertEqual(answer(index, "backup")["mode"], "excerpts")
                self.assertEqual(answer(index, "volcano")["mode"], "no-evidence")
                self.assertEqual(answer(index, "backup", StaticResponse("Make a copy [S1]"))["mode"], "generated")
                self.assertEqual(answer(index, "backup", StaticResponse("Make a copy [S9]"))["mode"], "rejected")
                self.assertEqual(answer(index, "backup", StaticResponse("Make a copy"))["mode"], "rejected")
            finally:
                index.close()
