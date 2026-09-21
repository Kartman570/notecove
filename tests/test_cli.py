import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def test_offline_workflow(self):
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / "index.sqlite3")

            def command(*args):
                result = subprocess.run([sys.executable, '-m', 'notecove', '--db', db, *args],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            self.assertEqual(command('ingest', 'examples/notes')['updated'], 3)
            self.assertEqual(command('ingest', 'examples/notes')['unchanged'], 3)
            self.assertEqual(command('search', 'worker lease')[0]['source'], 'queue.md')
            self.assertEqual(command('ask', 'restore checksum')['mode'], 'excerpts')
            self.assertTrue(command('check')['ok'])
            self.assertEqual(command('evaluate', 'examples/questions.jsonl')['mrr'], 1)
            self.assertEqual(command('prune', 'examples/notes')['removed'], [])
            result = subprocess.run([sys.executable, '-m', 'notecove', '--db', db, 'export'],
                                    capture_output=True, text=True, check=True)
            self.assertEqual(len([json.loads(line) for line in result.stdout.splitlines()]), 3)
            self.assertTrue(command('delete', 'queue.md')['deleted'])
            self.assertEqual(command('stats')['documents'], 2)
