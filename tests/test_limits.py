import tempfile
import unittest
from pathlib import Path
from notecove.index import Index
from notecove.ingest import ingest_folder
from notecove.models import Ollama
from notecove.export import check_index


class LimitTests(unittest.TestCase):
    def test_bounds_and_fts_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            index = Index(Path(directory) / 'index.sqlite3')
            try:
                with self.assertRaises(ValueError):
                    index.search('***', 0)
                with self.assertRaises(ValueError):
                    ingest_folder(index, directory, max_bytes=0)
                index.put('one', 'old terms')
                index.put('one', 'new terms')
                index.delete('one')
                self.assertTrue(check_index(index)['ok'])
            finally:
                index.close()

    def test_endpoint_has_no_credentials_or_query(self):
        for endpoint in ('file:///tmp/model', 'http://user:secret@localhost', 'http://localhost?key=secret'):
            with self.assertRaises(ValueError):
                Ollama('test', endpoint)
