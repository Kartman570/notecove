import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class ModelError(Exception):
    pass


class Ollama:
    def __init__(self, model, base_url="http://127.0.0.1:11434", timeout=60):
        parsed = urlparse(base_url)
        if not model or parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("A model name and HTTP endpoint are required")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, path, payload):
        request = Request(self.base_url + path, data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise ModelError("Model response is too large")
            result = json.loads(raw)
        except HTTPError as error:
            raise ModelError("Model server returned HTTP " + str(error.code)) from None
        except (URLError, OSError, ValueError):
            raise ModelError("Model server returned an invalid response or could not be reached") from None
        if not isinstance(result, dict) or result.get("error"):
            raise ModelError("Model server rejected the request")
        return result

    def chat(self, messages):
        result = self.request("/api/chat", {"model": self.model, "messages": messages,
                                            "stream": False, "options": {"temperature": 0}})
        message = result.get("message", {})
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ModelError("Model response has no text")
        return message["content"]

    def embed(self, text):
        result = self.request("/api/embeddings", {"model": self.model, "prompt": text})
        vector = result.get("embedding")
        if not isinstance(vector, list) or not vector or any(
            type(value) not in (int, float) or not math.isfinite(value) for value in vector
        ) or not any(vector):
            raise ModelError("Invalid embedding")
        return vector
