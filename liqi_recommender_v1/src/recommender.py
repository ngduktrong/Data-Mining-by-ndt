"""Suy luận độc lập; không cần dữ liệu train khi tích hợp."""
import json
from pathlib import Path


def load_model(path):
    model = json.loads(Path(path).read_text(encoding='utf-8'))
    if model.get('schema_version') != 1:
        raise ValueError('Phiên bản model không được hỗ trợ')
    return model


def recommend(model, own_picks, enemy_picks=None, banned=None, k=5):
    if type(k) is not int or not 1 <= k <= 100:
        raise ValueError('k phải là số nguyên từ 1 đến 100')
    groups = [own_picks, [] if enemy_picks is None else enemy_picks,
              [] if banned is None else banned]
    for group in groups:
        if not isinstance(group, (list, tuple)) or any(not isinstance(h, str) for h in group):
            raise ValueError('Các danh sách tướng phải chứa ID dạng chuỗi')
        if len(group) != len(set(group)):
            raise ValueError('Tướng bị lặp trong danh sách')
        if any(h not in model['hero_names'] for h in group):
            raise ValueError('Có ID tướng không thuộc danh mục')
    own, enemy, bans = map(set, groups)
    if len(own) >= 5 or len(enemy) > 5:
        raise ValueError('Đội mình cần còn vị trí chọn; đối thủ tối đa 5 tướng')
    if own & enemy or own & bans or enemy & bans:
        raise ValueError('Tướng xuất hiện mâu thuẫn giữa pick và ban')
    excluded = own | enemy | bans
    candidates = [h for h in model['catalog'] if h not in excluded]
    pop = model['popularity']
    scores = {h: sum(model['weights'].get(i, {}).get(h, 0) for i in sorted(own))
              for h in candidates}
    if model['method'] == 'popularity':
        ranked = sorted(candidates, key=lambda h: (-pop[h], h))[:k]
    else:
        positive = sorted((h for h in candidates if scores[h] > 0),
                          key=lambda h: (-scores[h], -pop[h], h))
        zero = sorted((h for h in candidates if scores[h] <= 0), key=lambda h: (-pop[h], h))
        ranked = (positive + zero)[:k]
    results = []
    for rank, h in enumerate(ranked, 1):
        source = ('popularity' if model['method'] == 'popularity' else
                  'item_item' if scores[h] > 0 else 'popularity_fallback')
        evidence = [{'hero_id': i, 'weight': model['weights'].get(i, {}).get(h, 0)}
                    for i in sorted(own) if model['weights'].get(i, {}).get(h, 0) > 0]
        results.append({'rank': rank, 'hero_id': h, 'hero_name': model['hero_names'][h],
                        'score': pop[h] if source == 'popularity' else scores[h],
                        'source': source, 'popularity_count': pop[h], 'evidence': evidence})
    return {'model_version': model['model_version'], 'method': model['method'],
            'recommendations': results, 'returned_count': len(results),
            'unseen_context_heroes': sorted(excluded - set(model['catalog'])),
            'capabilities': {'pick': 'lineup_completion', 'counter_pick': False, 'ban': False},
            'limitations': ['Điểm không phải xác suất thắng.',
                           'Đối thủ chỉ dùng lọc ứng viên; chưa kiểm soát luật giải/patch.']}
