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


def hybrid(index, vectors, query, model, limit=5):
    if not 1 <= limit <= 20:
        raise ValueError("Limit must be between 1 and 20")
    rankings = (index.search(query, min(100, limit * 4)), vectors.search(query, model, min(100, limit * 4)))
    scores = {}
    hits = {}
    for ranking in rankings:
        for rank, hit in enumerate(ranking, 1):
            key = hit['id']
            scores[key] = scores.get(key, 0) + 1 / (60 + rank)
            hits[key] = hit
    return [dict(hits[key], score=scores[key]) for key in sorted(scores, key=lambda key: (-scores[key], key))[:limit]]
