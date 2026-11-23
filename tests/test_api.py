import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from notecove.api import create_app
from notecove.index import Index
from notecove.ingest import ingest_folder


class ApiTests(unittest.TestCase):
    def test_search_and_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.sqlite3"
            index = Index(path)
            ingest_folder(index, "examples/notes")
            index.close()
            with TestClient(create_app(path, "test-key")) as client:
                self.assertEqual(client.get('/search?q=queue').status_code, 401)
                headers = {'Authorization': 'Bearer test-key'}
                self.assertEqual(client.get('/search?q=queue', headers=headers).json()[0]['source'], 'queue.md')
                response = client.post('/ask', json={'question': 'restore checksum'}, headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['mode'], 'excerpts')
                self.assertIn('[S1]', response.json()['answer'])
                self.assertEqual(client.post('/ask', json={'question': ' '}, headers=headers).status_code, 422)
                self.assertEqual(client.get('/search?q=x&limit=0', headers=headers).status_code, 422)
