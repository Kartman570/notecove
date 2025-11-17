import tempfile
import unittest
from pathlib import Path
from notecove.index import Index
from notecove.vectors import Vectors, cosine
from notecove.retrieval import hybrid


class FixtureEmbedding:
    model = "protocol-fixture"

    def embed(self, text):
        return [float("backup" in text), 1.0]


class VectorTests(unittest.TestCase):
    def test_cache_refresh_and_hybrid_search(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Index(Path(directory) / "index.sqlite3")
            try:
                index.put("a", "backup files")
                index.put("b", "queue messages")
                vectors = Vectors(index)
                model = FixtureEmbedding()
                self.assertEqual(vectors.build(model), 2)
                self.assertEqual(vectors.build(model), 0)
                self.assertEqual(hybrid(index, vectors, "backup", model)[0]['source'], "a")
                index.put("a", "backup snapshots")
                self.assertEqual(vectors.build(model), 1)
                index.delete("a")
                self.assertEqual(len(vectors.search("backup", model)), 1)
            finally:
                index.close()

    def test_invalid_vectors(self):
        for left, right in (([0], [1]), ([1], [1, 2]), ([float('nan')], [1])):
            with self.assertRaises(ValueError):
                cosine(left, right)
