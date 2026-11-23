import tempfile
import unittest
from pathlib import Path
from notecove.evaluate import evaluate, load_cases
from notecove.index import Index
from notecove.ingest import ingest_folder


class EvaluationTests(unittest.TestCase):
    def test_reference_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Index(Path(directory) / "index.sqlite3")
            try:
                ingest_folder(index, "examples/notes")
                report = evaluate(index, load_cases("examples/questions.jsonl"), 3)
                self.assertEqual(report['cases'], 6)
                self.assertEqual(report['recall'], 1)
                self.assertEqual(report['mrr'], 1)
                self.assertEqual(report['no_answer_accuracy'], 1)
                failure = evaluate(index, [{'question': 'queue', 'sources': ['missing.md']}])
                self.assertEqual(failure['recall'], 0)
            finally:
                index.close()

    def test_empty_cases(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.jsonl"
            path.write_text("")
            with self.assertRaises(ValueError):
                load_cases(path)
