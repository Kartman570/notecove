import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    text: str
    start: int
    end: int


def split(text, size=900, overlap=120):
    if size < 40 or overlap < 0 or overlap >= size:
        raise ValueError("Require size >= 40 and 0 <= overlap < size")
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        if text[start:end].strip():
            chunks.append(Chunk(len(chunks), text[start:end], start, end))
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def terms(text):
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())
