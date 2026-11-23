import json
from pathlib import Path


def load_cases(path):
    cases = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        if not isinstance(case, dict) or not isinstance(case.get("question"), str) or not case['question'].strip():
            raise ValueError("Invalid question on line " + str(number))
        sources = case.get('sources')
        if not isinstance(sources, list) or any(not isinstance(source, str) or not source for source in sources):
            raise ValueError("Invalid sources on line " + str(number))
        cases.append(case)
    if not cases:
        raise ValueError("The evaluation set is empty")
    return cases


def evaluate(index, cases, k=3):
    if not cases or not 1 <= k <= 100:
        raise ValueError("Evaluation needs cases and 1 <= k <= 100")
    rows = []
    for case in cases:
        hits = index.search(case['question'], k)
        expected = set(case['sources'])
        ranked = list(dict.fromkeys(hit['source'] for hit in hits))
        ranks = [rank for rank, source in enumerate(ranked, 1) if source in expected]
        recall = len(expected.intersection(ranked)) / len(expected) if expected else float(not ranked)
        reciprocal = 1 / ranks[0] if ranks else 0.0
        rows.append({'question': case['question'], 'expected': sorted(expected), 'retrieved': ranked,
                     'recall': recall, 'reciprocal_rank': reciprocal, 'no_answer_correct': not ranked if not expected else None})
    answerable = [row for row in rows if row['expected']]
    unanswerable = [row for row in rows if not row['expected']]
    return {'k': k, 'cases': len(rows),
            'recall': sum(row['recall'] for row in answerable) / len(answerable) if answerable else None,
            'mrr': sum(row['reciprocal_rank'] for row in answerable) / len(answerable) if answerable else None,
            'no_answer_accuracy': sum(row['no_answer_correct'] for row in unanswerable) / len(unanswerable) if unanswerable else None,
            'results': rows}
