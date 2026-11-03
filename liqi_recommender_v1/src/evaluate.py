import json
import math
from collections import defaultdict
from .recommender import recommend


def case_score(rank, k):
    return (int(rank is not None and rank <= k),
            1 / math.log2(rank + 1) if rank is not None and rank <= k else 0.0)


def evaluate(model, rows):
    records, summary = [], {}
    for row in rows:
        for team in ['team_a_heroes', 'team_b_heroes']:
            heroes = json.loads(row[team])
            for target in sorted(heroes):
                own = [h for h in heroes if h != target]
                recs = recommend(model, own, k=10)['recommendations']
                ids = [x['hero_id'] for x in recs]
                if len(ids) != len(set(ids)) or set(ids) & set(own):
                    raise ValueError('Kết quả gợi ý không hợp lệ')
                records.append({'game_id': row['game_id'], 'series_id': row['series_id'],
                                'team_column': team, 'target': target, 'own_picks': own,
                                'target_seen': target in model['catalog'],
                                'rank': ids.index(target) + 1 if target in ids else None,
                                'recommendations': recs})
    if not records:
        raise ValueError('Không có trường hợp đánh giá')
    for k in [5, 10]:
        hits, ndcg, fallback_req, fallback_slots, slots, full = 0, 0.0, 0, 0, 0, 0
        covered = set()
        per_series = defaultdict(lambda: {'cases': 0, 'hits': 0, 'ndcg_sum': 0.0})
        for r in records:
            hit, gain = case_score(r['rank'], k)
            hits += hit; ndcg += gain
            recs = r['recommendations'][:k]
            covered.update(x['hero_id'] for x in recs)
            fallback = sum(x['source'] == 'popularity_fallback' for x in recs)
            fallback_req += int(fallback > 0); fallback_slots += fallback
            slots += len(recs); full += int(len(recs) == k)
            s = per_series[r['series_id']]
            s['cases'] += 1; s['hits'] += hit; s['ndcg_sum'] += gain
        n = len(records)
        summary[str(k)] = {'cases': n, 'hits': hits, 'hit_rate': hits / n, 'ndcg': ndcg / n,
                           'catalog_coverage': len(covered) / len(model['catalog']),
                           'fallback_request_rate': fallback_req / n,
                           'fallback_slot_rate': fallback_slots / slots if slots else 0,
                           'full_k_rate': full / n, 'invalid_recommendation_rate': 0.0,
                           'target_coverage': sum(r['target_seen'] for r in records) / n,
                           'unseen_target_cases': sum(not r['target_seen'] for r in records),
                           'per_series': dict(per_series)}
    return {'method': model['method'], 'protocol': model['protocol'],
            'games': len(rows), 'series': len({r['series_id'] for r in rows}),
            'metrics': summary}, records
