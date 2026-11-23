import json


def export_chunks(index, stream):
    count = 0
    rows = index.db.execute("""SELECT d.source,c.ordinal,c.start,c.end,c.text FROM chunks c
        JOIN documents d ON d.id=c.document_id ORDER BY d.source,c.ordinal""")
    for row in rows:
        stream.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
        count += 1
    return count


def check_index(index):
    integrity = index.db.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = index.db.execute("PRAGMA foreign_key_check").fetchall()
    with index.db:
        index.db.execute("INSERT INTO search(search,rank) VALUES('integrity-check',1)")
    return {'ok': integrity == 'ok' and not foreign_keys, 'integrity': integrity,
            'foreign_key_errors': len(foreign_keys), **index.stats()}
