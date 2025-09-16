import json
import math


def cosine(left, right):
    if len(left) != len(right) or not left:
        raise ValueError("Embedding dimensions do not match")
    if any(type(value) not in (float, int) or not math.isfinite(value) for value in left + right):
        raise ValueError("Embeddings must contain finite numbers")
    norm = math.sqrt(sum(value * value for value in left) * sum(value * value for value in right))
    if not norm:
        raise ValueError("Zero embeddings cannot be compared")
    return sum(a * b for a, b in zip(left, right)) / norm


class Vectors:
    def __init__(self, index):
        self.index = index
        self.db = index.db
        self.db.execute("""CREATE TABLE IF NOT EXISTS vectors (
            chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
            model TEXT NOT NULL, vector TEXT NOT NULL, PRIMARY KEY(chunk_id,model))""")
        self.db.commit()

    def build(self, model):
        rows = self.db.execute("""SELECT c.id,c.text FROM chunks c LEFT JOIN vectors v
            ON v.chunk_id=c.id AND v.model=? WHERE v.chunk_id IS NULL ORDER BY c.id""", (model.model,)).fetchall()
        count = 0
        for row in rows:
            vector = model.embed(row['text'])
            cosine(vector, vector)
            with self.db:
                current = self.db.execute("SELECT text FROM chunks WHERE id=?", (row['id'],)).fetchone()
                if current and current['text'] == row['text']:
                    self.db.execute("INSERT OR REPLACE INTO vectors VALUES(?,?,?)",
                                    (row['id'], model.model, json.dumps(vector)))
                    count += 1
        return count

    def search(self, query, model, limit=5):
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")
        vector = model.embed(query)
        rows = self.db.execute("""SELECT c.id,c.text,c.ordinal,c.start,c.end,d.source,v.vector
            FROM vectors v JOIN chunks c ON c.id=v.chunk_id JOIN documents d ON d.id=c.document_id
            WHERE v.model=?""", (model.model,)).fetchall()
        result = []
        for row in rows:
            hit = dict(row)
            hit['score'] = cosine(vector, json.loads(hit.pop('vector')))
            result.append(hit)
        return sorted(result, key=lambda hit: (-hit['score'], hit['id']))[:limit]
