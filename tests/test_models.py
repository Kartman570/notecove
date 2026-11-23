import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from notecove.models import Ollama, ModelError


class ModelProtocolTests(unittest.TestCase):
    def test_chat_and_embeddings_over_http(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append((self.path, body))
                self.send_response(200)
                self.end_headers()
                value = {"embedding": [1.0, 0.5]} if self.path.endswith("embeddings") else {"message": {"content": "Backup first [S1]"}}
                self.wfile.write(json.dumps(value).encode())

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            model = Ollama("local-model", "http://127.0.0.1:" + str(server.server_port))
            self.assertEqual(model.chat([{"role": "user", "content": "backup"}]), "Backup first [S1]")
            self.assertEqual(model.embed("backup"), [1.0, 0.5])
            self.assertFalse(requests[0][1]["stream"])
            self.assertEqual(requests[1][1]["prompt"], "backup")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_unreachable_model(self):
        with self.assertRaises(ModelError):
            Ollama("missing", "http://127.0.0.1:1", timeout=0.1).chat([])
