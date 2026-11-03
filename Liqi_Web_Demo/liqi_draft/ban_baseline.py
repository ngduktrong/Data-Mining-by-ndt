"""Train-only ban popularity. Python standard library; no V1 changes."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path

VERSION = '035ce761e53a47dbfd18ca1d9fabe7ceb0ec79115271bccac303bed2a6c0195c'


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fit_records(train_games, actions, names):
    """Ignore non-train action payloads; count observed bans, never impute."""
    games = {r['game_id']: r for r in train_games}
    if not games or len(games) != len(train_games):
        raise ValueError('Empty or duplicate train games')
    if any(r['split'] != 'train' for r in train_games):
        raise ValueError('Fit input must be train only')
    bans, picks = defaultdict(set), defaultdict(set)
    by_team = Counter()
    for r in actions:
        if r['split'] != 'train':
            continue
        g, h, team = r['game_id'], r['hero_id'], r['team_number']
        if g not in games or r['series_id'] != games[g]['series_id']:
            raise ValueError('Action/game linkage mismatch')
        if h not in names or team not in ('1', '2'):
            raise ValueError('Unknown hero or invalid team')
        if r['action_type'] == 'ban':
            if h in bans[g]:
                raise ValueError('Duplicate ban in game: ' + g)
            bans[g].add(h)
            by_team[g, team] += 1
        elif r['action_type'] == 'pick':
            if h in picks[g]:
                raise ValueError('Duplicate pick in game: ' + g)
            picks[g].add(h)
        else:
            raise ValueError('Unknown action type')
    warnings = []
    for g in games:
        if len(picks[g]) != 10 or not bans[g] or bans[g] & picks[g]:
            raise ValueError('Invalid observed draft: ' + g)
        for team in ('1', '2'):
            n = by_team[g, team]
            if n != 4:
                warnings.append({'game_id': g, 'team_number': team, 'observed_bans': n})
    counts = Counter(h for heroes in bans.values() for h in heroes)
    return {
        'model_version': 'ban_popularity_train_v1',
        'method': 'ban_popularity', 'fit_split': 'train',
        'train_games': len(games), 'train_ban_events': sum(counts.values()),
        'candidate_policy': 'positive_train_ban_count_only',
        'score_definition': 'observed_games_banned / train_games',
        'tie_break': 'hero_id ascending',
        'incomplete_policy': 'retain_observed_bans_no_imputation',
        'review_warnings': warnings,
        'hero_names': names, 'ban_counts': dict(sorted(counts.items())),
        'limitations': [
            'Score is observed ban frequency, not win probability.',
            'No verified draft order; no phase, patch or tournament rule checks.',
            'Picks and bans only filter candidates; no opponent-specific ranking.',
            'Heroes never banned in train are not recommended.',
        ],
    }


def train(data_dir):
    data = Path(data_dir)
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    if manifest['dataset_version'] != VERSION:
        raise ValueError('Dataset snapshot mismatch')
    hashes = {}
    for name in ('train.csv', 'draft_actions.csv', 'heroes.csv', 'split_assignments.csv'):
        hashes[name] = hashlib.sha256((data/name).read_bytes()).hexdigest()
        if hashes[name] != manifest['files'][name]['sha256']:
            raise ValueError('Hash mismatch: ' + name)
    rows = read_csv(data/'heroes.csv')
    names = {r['hero_id']: r['name'] for r in rows}
    if len(names) != len(rows):
        raise ValueError('Duplicate hero IDs')
    games = read_csv(data/'train.csv')
    split = {r['series_id']: r['split'] for r in read_csv(data/'split_assignments.csv')}
    if any(split.get(g['series_id']) != 'train' for g in games):
        raise ValueError('Series assignment mismatch')
    with (data/'draft_actions.csv').open(encoding='utf-8-sig', newline='') as f:
        model = fit_records(games, csv.DictReader(f), names)
    model.update(dataset_version=VERSION, source_hashes=hashes,
                 validation_csv_opened=False, test_csv_opened=False,
                 mixed_split_actions_scanned=True,
                 non_train_policy='skip_by_split_before_hero_statistics',
                 evaluated=False)
    return model


def load_model(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def recommend_bans(model, own_picks=None, enemy_picks=None, banned=None, k=5):
    if type(k) is not int or not 1 <= k <= 100:
        raise ValueError('k must be an integer from 1 to 100')
    groups = [([] if x is None else x) for x in (own_picks, enemy_picks, banned)]
    seen = set()
    for group in groups:
        if not isinstance(group, list) or any(not isinstance(h, str) for h in group):
            raise ValueError('Context must be lists of hero_id strings')
        if len(set(group)) != len(group) or seen.intersection(group):
            raise ValueError('Duplicate or conflicting heroes')
        if any(h not in model['hero_names'] for h in group):
            raise ValueError('Unknown hero_id')
        seen.update(group)
    if len(groups[0]) > 5 or len(groups[1]) > 5:
        raise ValueError('At most 5 picks per team')
    counts = model['ban_counts']
    ranked = sorted((h for h in counts if h not in seen), key=lambda h: (-counts[h], h))[:k]
    return {'model_version': model['model_version'], 'method': model['method'],
            'recommendations': [dict(rank=i, hero_id=h, hero_name=model['hero_names'][h],
                                     ban_count=counts[h], score=counts[h]/model['train_games'])
                                for i, h in enumerate(ranked, 1)],
            'returned_count': len(ranked), 'requested_k': k,
            'limitations': model['limitations']}


def main():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['train', 'demo'])
    p.add_argument('--data-dir', type=Path, default=root/'data/raw')
    p.add_argument('--model', type=Path, default=root/'artifacts/v2/ban_popularity/model.json')
    p.add_argument('--request', type=Path, help='JSON containing own_picks, enemy_picks, banned, k')
    args = p.parse_args()
    if args.command == 'train':
        model = train(args.data_dir)
        save(args.model, model)
        result = {k: model[k] for k in ('model_version', 'fit_split', 'train_games', 'train_ban_events', 'review_warnings', 'evaluated')}
        result.update(status='trained', candidate_heroes=len(model['ban_counts']), model_path=str(args.model))
    else:
        request = json.loads(args.request.read_text(encoding='utf-8-sig')) if args.request else {}
        result = recommend_bans(load_model(args.model), **request)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
