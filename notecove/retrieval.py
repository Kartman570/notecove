def retrieve(index, query, limit=5, per_source=2, budget=4500):
    if not 1 <= limit <= 20 or not 1 <= per_source <= limit or budget < 100:
        raise ValueError("Invalid retrieval limits")
    hits = index.search(query, min(100, limit * 5))
    selected = []
    counts = {}
    remaining = budget
    for hit in hits:
        source = hit["source"]
        if counts.get(source, 0) >= per_source:
            continue
        text = hit["text"][:remaining]
        if not text.strip():
            continue
        selected.append(dict(hit, text=text, end=hit["start"] + len(text), citation="S" + str(len(selected) + 1)))
        counts[source] = counts.get(source, 0) + 1
        remaining -= len(text)
        if len(selected) == limit or remaining <= 0:
            break
    return selected
