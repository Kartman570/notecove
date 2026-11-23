# Storage and retrieval

A document row identifies a source path within one collection. A content digest and chunk settings decide whether ingestion can skip the file. Changed documents are replaced within a transaction. Deleting a document cascades to excerpts and vectors, while triggers keep the full-text index synchronized.

Text search ranks excerpts, so `k` in evaluation is an excerpt cutoff. Duplicate source paths are collapsed before source recall and reciprocal rank are computed. No-answer accuracy measures an empty lexical result, not a model's ability to abstain. Lexical matching alone cannot determine whether a passage truly answers a question.

The optional vector cache is keyed by excerpt and model name. A failed embedding request leaves already completed vectors available; rerunning resumes missing rows. A changed document invalidates its cached vectors. The model endpoint is trusted operator configuration and can receive the entire indexed text.

Search and answer HTTP requests are read-only with respect to document contents. Run ingestion and maintenance from the CLI. SQLite serializes writers and permits concurrent readers through WAL mode. Avoid placing the database on a network filesystem.

`check` runs database, foreign-key and full-text integrity checks. It does not compare the index to files on disk. Re-ingestion handles modified files, and explicit pruning handles removed files. Exports are source excerpts, not full database backups.
