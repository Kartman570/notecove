import tempfile
import unittest
from pathlib import Path
from notecove.chunks import split
from notecove.index import Index


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.index = Index(Path(self.tmp.name) / "index.sqlite3")

    def tearDown(self):
        self.index.close()
        self.tmp.cleanup()

    def test_refresh_removes_old_terms(self):
        self.assertTrue(self.index.put("notes.md", "apples and oranges"))
        self.assertFalse(self.index.put("notes.md", "apples and oranges"))
        self.assertEqual(self.index.search("oranges")[0]["source"], "notes.md")
        self.index.put("notes.md", "pears and plums")
        self.assertEqual(self.index.search("oranges"), [])
        self.assertEqual(len(self.index.search("plums")), 1)

    def test_chunk_offsets(self):
        text = "A slightly longer paragraph about walking through a quiet forest. " * 20
        chunks = split(text, 100, 20)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertEqual(chunk.text, text[chunk.start:chunk.end])
        self.assertEqual(chunks[-1].end, len(text))
        for first, second in zip(chunks, chunks[1:]):
            self.assertLess(second.start, first.end)

    def test_query_syntax_is_literal(self):
        self.index.put("a", "hello world")
        self.assertEqual(len(self.index.search('hello OR "')), 1)
        self.assertEqual(self.index.search('"*'), [])
