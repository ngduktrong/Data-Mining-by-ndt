import json
import math
from collections import Counter, defaultdict
from itertools import combinations
from .data_loader import VERSION


def fit(transactions, names, method):
    if method not in {'popularity', 'item_item_count', 'item_item_cosine'}:
        raise ValueError('Phương pháp chưa triển khai')
    pop, counts = Counter(), defaultdict(Counter)
    for r in transactions:
        if r['split'] != 'train':
            raise ValueError('Không được fit ngoài train')
        heroes = json.loads(r['hero_ids'])
        pop.update(heroes)
        for a, b in combinations(sorted(heroes), 2):
            counts[a][b] += 1
            counts[b][a] += 1
    weights = {}
    if method != 'popularity':
        for a in sorted(counts):
            weights[a] = {b: (c if method == 'item_item_count' else c / math.sqrt(pop[a] * pop[b]))
                          for b, c in sorted(counts[a].items())}
    return {'schema_version': 1, 'model_version': f'{method}_p1_v1', 'method': method,
            'dataset_version': VERSION, 'fit_split': 'train', 'fit_lineups': len(transactions),
            'catalog': sorted(pop), 'hero_names': names, 'popularity': dict(sorted(pop.items())),
            'weights': weights, 'fallback': 'train_popularity',
            'tie_break': 'score_desc_popularity_desc_id_asc',
            'protocol': 'P1_leave_one_hero_out_ally_only'}
