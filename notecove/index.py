import hashlib
import sqlite3

from notecove.chunks import split, terms


class Index:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY, source TEXT NOT NULL UNIQUE,
                digest TEXT NOT NULL, chunk_size INTEGER NOT NULL, overlap INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL, text TEXT NOT NULL, start INTEGER NOT NULL, end INTEGER NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(text, content='chunks', content_rowid='id');
            CREATE TRIGGER IF NOT EXISTS chunks_insert AFTER INSERT ON chunks BEGIN
                INSERT INTO search(rowid,text) VALUES(new.id,new.text);
            END;
            CREATE TRIGGER IF NOT EXISTS chunks_delete AFTER DELETE ON chunks BEGIN
                INSERT INTO search(search,rowid,text) VALUES('delete',old.id,old.text);
            END;
        """)

    def close(self):
        self.db.close()

    def put(self, source, text, size=900, overlap=120):
        if not source or not isinstance(text, str):
            raise ValueError("A source and text are required")
        chunks = split(text, size, overlap)
        digest = hashlib.sha256(text.encode()).hexdigest()
        with self.db:
            old = self.db.execute("SELECT * FROM documents WHERE source=?", (source,)).fetchone()
            if old and (old['digest'], old['chunk_size'], old['overlap']) == (digest, size, overlap):
                return False
            if old:
                self.db.execute("DELETE FROM documents WHERE id=?", (old['id'],))
            cursor = self.db.execute("INSERT INTO documents(source,digest,chunk_size,overlap) VALUES(?,?,?,?)",
                                     (source, digest, size, overlap))
            self.db.executemany("INSERT INTO chunks(document_id,ordinal,text,start,end) VALUES(?,?,?,?,?)",
                                [(cursor.lastrowid, c.ordinal, c.text, c.start, c.end) for c in chunks])
        return True

    def search(self, query, limit=5):
        tokens = list(dict.fromkeys(terms(query)))[:40]
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")
        if not tokens:
            return []
        expression = " OR ".join('"' + token + '"' for token in tokens)
        return [dict(row) for row in self.db.execute("""SELECT c.id,c.ordinal,c.text,c.start,c.end,d.source,
            bm25(search) AS score FROM search JOIN chunks c ON c.id=search.rowid
            JOIN documents d ON d.id=c.document_id WHERE search MATCH ? ORDER BY score,c.id LIMIT ?""",
            (expression, limit))]

    def documents(self):
        return [dict(row) for row in self.db.execute("""SELECT d.source,d.digest,COUNT(c.id) AS chunks
            FROM documents d LEFT JOIN chunks c ON c.document_id=d.id GROUP BY d.id ORDER BY d.source""")]

    def delete(self, source):
        with self.db:
            return bool(self.db.execute("DELETE FROM documents WHERE source=?", (source,)).rowcount)

    def stats(self):
        return {name: self.db.execute("SELECT COUNT(*) FROM " + name).fetchone()[0]
                for name in ("documents", "chunks")}
