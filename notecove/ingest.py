from pathlib import Path


def ingest_folder(index, folder, size=900, overlap=120, max_bytes=2_000_000):
    root = Path(folder).resolve()
    if not root.is_dir():
        raise ValueError("Input must be a directory")
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
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            counts["skipped"] += 1
            continue
        changed = index.put(path.relative_to(root).as_posix(), text, size, overlap)
        counts["updated" if changed else "unchanged"] += 1
    return counts
