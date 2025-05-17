import tempfile
import unittest
from pathlib import Path
from notecove.index import Index
from notecove.retrieval import retrieve


class RetrievalTests(unittest.TestCase):
    def test_budget_and_source_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Index(Path(directory) / "index.sqlite3")
            try:
                index.put("long", "queue delivery retries " * 100, size=100, overlap=10)
                index.put("short", "queue workers use a lease")
                hits = retrieve(index, "queue", limit=3, per_source=1, budget=120)
                self.assertLessEqual(sum(len(hit["text"]) for hit in hits), 120)
                self.assertEqual(len({hit["source"] for hit in hits}), len(hits))
                self.assertEqual(hits[0]["citation"], "S1")
                self.assertTrue(index.delete("long"))
                self.assertFalse(index.delete("missing"))
                self.assertEqual(index.stats()["documents"], 1)
            finally:
                index.close()
