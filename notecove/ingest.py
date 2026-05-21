from pathlib import Path


def ingest_folder(index, folder, size=900, overlap=120, max_bytes=2_000_000):
    root = Path(folder).resolve()
    if not root.is_dir():
        raise ValueError("Input must be a directory")
    index.db.execute("CREATE TABLE IF NOT EXISTS collection (id INTEGER PRIMARY KEY CHECK(id=1), root TEXT NOT NULL)")
    with index.db:
        previous = index.db.execute("SELECT root FROM collection WHERE id=1").fetchone()
        if previous and previous['root'] != str(root):
            raise ValueError("This index belongs to a different folder; use a separate database")
        index.db.execute("INSERT OR IGNORE INTO collection VALUES(1,?)", (str(root),))
    counts = {"updated": 0, "unchanged": 0, "skipped": 0}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in (".md", ".txt"):
            continue
        if not path.resolve().is_relative_to(root) or any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        if path.stat().st_size > max_bytes:
            counts["skipped"] += 1
            continue
        try:
            with path.open("rb") as stream:
                raw = stream.read(max_bytes + 1)
            if len(raw) > max_bytes:
                counts['skipped'] += 1
                continue
            text = raw.decode("utf-8")
        except UnicodeError:
            counts["skipped"] += 1
            continue
        changed = index.put(path.relative_to(root).as_posix(), text, size, overlap)
        counts["updated" if changed else "unchanged"] += 1
    return counts


def prune_missing(index, folder):
    root = Path(folder).resolve()
    if not root.is_dir():
        raise ValueError("Input must be a directory")
    exists = index.db.execute("SELECT name FROM sqlite_master WHERE name='collection'").fetchone()
    previous = index.db.execute("SELECT root FROM collection WHERE id=1").fetchone() if exists else None
    if not previous or previous['root'] != str(root):
        raise ValueError("Folder does not match this collection")
    removed = []
    for document in index.documents():
        path = root / document['source']
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            index.delete(document['source'])
            removed.append(document['source'])
    return removed
