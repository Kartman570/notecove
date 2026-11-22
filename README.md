# Notecove

Search a folder of Markdown and text notes, inspect relevant excerpts, and optionally ask a local model to answer with source references.

## Quick start

Python 3.11+ with SQLite FTS5 is required. The CLI's lexical search has no third-party dependencies.

```sh
python3 -m notecove ingest examples/notes
python3 -m notecove search "worker lease"
python3 -m notecove ask "How do workers recover expired leases?"
python3 -m notecove evaluate examples/questions.jsonl
python3 -m notecove check
python3 -m notecove export
```

The default database is `notes.sqlite3`. Select another with `--db <path>` before the subcommand. `ask` without a model returns source excerpts, not a synthetic answer. Character offsets refer to decoded source text. Text is indexed as UTF-8; hidden files, symbolic links, unsupported suffixes and files above the size limit are skipped.

Re-running ingestion updates changed files and keeps unchanged documents. Each database belongs to one source folder. `prune <folder>` explicitly removes documents whose files are gone; ingestion does not silently delete them. `delete <source>` removes one indexed document. `documents` and `stats` show index contents.

## Local generation and vectors

Use a model already installed in your Ollama server:

```sh
python3 -m notecove ask "How should a restore be checked?" --model YOUR_CHAT_MODEL
python3 -m notecove embed --model YOUR_EMBEDDING_MODEL
python3 -m notecove hybrid "restore safety" --model YOUR_EMBEDDING_MODEL
```

The commands never install or pull models. `--endpoint` selects a different server. Requests use `/api/chat` with streaming disabled and `/api/embeddings`. Not every chat model supports embeddings. The embedding model name must match when indexing and searching. Replacing the weights behind an existing model name requires rebuilding the database or using a new model name.

Lexical search uses SQLite BM25. Optional dense search computes cosine similarity over stored vectors; hybrid search fuses the two rankings. Dense search is an in-process scan intended for small personal collections. The answer command uses lexical retrieval with per-source and character-budget limits. Hybrid retrieval is available as a separate command for inspection.

Citation validation rejects answers without source IDs or with IDs that were not supplied. It does **not** prove that an answer is factually supported. Retrieved text is untrusted; the model is instructed to treat it as evidence, not instructions, but this is not a complete prompt-injection defense. No tools or side effects are exposed to the model.

## HTTP service

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export NOTECOVE_API_KEY=choose-a-long-private-key
uvicorn notecove.api:create_app --factory --host 127.0.0.1
make test lint
```

`GET /search?q=queue`, `GET /documents` and `POST /ask` require `Authorization: Bearer <key>`. The ask body is `{"question":"How do leases work?"}`. Generation is off unless `NOTECOVE_MODEL` is set; `NOTECOVE_ENDPOINT` can override the model endpoint. The service deliberately does not accept arbitrary filesystem paths or model URLs from requests.

For Docker, set `NOTECOVE_API_KEY`, run `docker compose run --rm search python -m notecove --db /data/notes.sqlite3 ingest /notes`, then `docker compose up --build`. The example corpus is mounted read-only and the index lives in a named volume. The API is bound to localhost port 8001.

## Evaluation

Question sets are JSON lines with `question` and expected `sources`. An empty sources list denotes an unanswerable question. The evaluator reports source recall, mean reciprocal rank and no-answer accuracy separately. The included six questions are a smoke corpus, not evidence of general retrieval quality. Add your own notes and independently written questions before drawing quality conclusions.

Tests exercise real SQLite indexes, file ingestion, HTTP endpoints and loopback model-protocol requests. Vector fixtures test arithmetic and cache invalidation, not embedding quality. A live model is not required by the suite. `make coverage` reports line coverage; subprocess CLI tests are not included in the parent process measurement.

## Limits

There is no OCR, PDF extraction, multi-user access control or background file watcher. The server shares one trusted collection. Put public deployments behind your own HTTPS proxy, request limits and access controls. Indexes and exports contain document text and should be kept private. Moving a collection to another folder requires a fresh database. For a consistent backup, stop writers or use SQLite's online backup API.
