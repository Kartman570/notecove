import hmac
import os
from contextlib import contextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from notecove.answers import answer
from notecove.index import Index
from notecove.models import Ollama, ModelError


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def create_app(path=None, api_key=None, model=None):
    path = path or os.environ.get("NOTECOVE_DB", "notes.sqlite3")
    api_key = api_key or os.environ.get("NOTECOVE_API_KEY", "")
    if not api_key:
        raise ValueError("NOTECOVE_API_KEY is required")
    if model is None and os.environ.get("NOTECOVE_MODEL"):
        model = Ollama(os.environ['NOTECOVE_MODEL'], os.environ.get('NOTECOVE_ENDPOINT', 'http://127.0.0.1:11434'))
    app = FastAPI(title="Notecove")

    def authorize(authorization: str = Header(default="")):
        if not hmac.compare_digest(authorization.encode(), ("Bearer " + api_key).encode()):
            raise HTTPException(401, "Invalid API key")

    @contextmanager
    def collection():
        index = Index(path)
        try:
            yield index
        finally:
            index.close()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/search", dependencies=[Depends(authorize)])
    def search(q: str = Query(min_length=1, max_length=2000), limit: int = Query(5, ge=1, le=20)):
        with collection() as index:
            return index.search(q, limit)

    @app.get("/documents", dependencies=[Depends(authorize)])
    def documents():
        with collection() as index:
            return index.documents()

    @app.post("/ask", dependencies=[Depends(authorize)])
    def ask(request: Question):
        try:
            with collection() as index:
                return answer(index, request.question, model)
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
        except ModelError:
            raise HTTPException(502, "The configured model is unavailable") from None

    return app
