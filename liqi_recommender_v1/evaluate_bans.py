"""B1 unordered leave-one-ban-out validation; never next-turn evaluation."""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from ban_baseline import VERSION, load_model, read_csv, recommend_bans, save


def evaluate(model, games, ban_sets, ks=(5, 10)):
    cases = []
    for game in sorted(games):
        bans = sorted(ban_sets[game])
        if not bans:
            raise ValueError('No observed bans: ' + game)
        for target in bans:
            context = [h for h in bans if h != target]
            result = recommend_bans(model, banned=context, k=max(ks))
            ids = [r['hero_id'] for r in result['recommendations']]
            if len(ids) != len(set(ids)) or set(ids) & set(context):
                raise ValueError('Invalid recommendations')
            rank = ids.index(target) + 1 if target in ids else None
            row = dict(game_id=game, series_id=games[game]['series_id'], target=target,
                       target_name=model['hero_names'][target], context=context,
                       unseen=target not in model['ban_counts'], rank_at_max_k=rank,
                       recommendations=ids)
            cases.append(row)
    if not cases:
        raise ValueError('Empty evaluation')
    metrics = {}
    for k in ks:
        hits = 0
        ndcg = 0.0
        covered = set()
        series = defaultdict(lambda: dict(cases=0, hits=0, ndcg_sum=0.0))
        for row in cases:
            rank = row['rank_at_max_k']
            hit = int(rank is not None and rank <= k)
            gain = 1 / math.log2(rank + 1) if hit else 0.0
            hits += hit
            ndcg += gain
            covered.update(row['recommendations'][:k])
            s = series[row['series_id']]
            s['cases'] += 1
            s['hits'] += hit
            s['ndcg_sum'] += gain
        metrics[str(k)] = dict(cases=len(cases), hits=hits, hit_rate=hits/len(cases),
                              ndcg=ndcg/len(cases), catalog_coverage=len(covered)/len(model['ban_counts']),
                              recommended_unique_heroes=len(covered),
                              full_k_rate=sum(len(r['recommendations']) >= k for r in cases)/len(cases),
                              invalid_recommendation_rate=0.0, per_series=dict(series))
    unseen = sum(r['unseen'] for r in cases)
    return dict(protocol='B1_unordered_leave_one_ban_out_all_teams',
                split='validation', games=len(games), series=len({r['series_id'] for r in games.values()}),
                candidate_catalog=len(model['ban_counts']), unseen_target_cases=unseen,
                target_coverage=1-unseen/len(cases), metrics=metrics), cases


def main():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=root/'data/raw')
    p.add_argument('--model', type=Path, default=root/'artifacts/v2/ban_popularity/model.json')
    p.add_argument('--output-dir', type=Path, default=root/'reports/v2/ban_validation')
    a = p.parse_args()
    model_hash = hashlib.sha256(a.model.read_bytes()).hexdigest()
    model = load_model(a.model)
    manifest = json.loads((a.data_dir/'manifest.json').read_text(encoding='utf-8'))
    if manifest['dataset_version'] != VERSION or model['dataset_version'] != VERSION:
        raise ValueError('Dataset mismatch')
    if model['fit_split'] != 'train' or model['method'] != 'ban_popularity':
        raise ValueError('Expected train-only ban popularity model')
    hashes = {}
    for name in ('validation.csv', 'draft_actions.csv', 'split_assignments.csv'):
        hashes[name] = hashlib.sha256((a.data_dir/name).read_bytes()).hexdigest()
        if hashes[name] != manifest['files'][name]['sha256']:
            raise ValueError('Source hash mismatch: ' + name)
    for name, sha in model['source_hashes'].items():
        if sha != manifest['files'][name]['sha256']:
            raise ValueError('Model provenance mismatch: ' + name)
    rows = read_csv(a.data_dir/'validation.csv')
    games = {r['game_id']: r for r in rows}
    assignments = {r['series_id']: r['split'] for r in read_csv(a.data_dir/'split_assignments.csv')}
    if len(games) != len(rows) or any(r['split'] != 'validation' or assignments.get(r['series_id']) != 'validation' for r in rows):
        raise ValueError('Validation split mismatch')
    bans = defaultdict(set)
    with (a.data_dir/'draft_actions.csv').open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if r['split'] != 'validation':
                continue
            if r['game_id'] not in games or r['series_id'] != games[r['game_id']]['series_id']:
                raise ValueError('Action linkage mismatch')
            if r['action_type'] != 'ban':
                continue
            h = r['hero_id']
            if h not in model['hero_names'] or h in bans[r['game_id']]:
                raise ValueError('Unknown or duplicate ban')
            bans[r['game_id']].add(h)
    report, cases = evaluate(model, games, bans)
    report.update(model_version=model['model_version'], model_sha256=model_hash,
                  dataset_version=VERSION, source_hashes=hashes,
                  model_refit=False, test_csv_opened=False, mixed_split_actions_scanned=True,
                  non_validation_policy='skip_by_split_before_hero_statistics',
                  context='all other observed bans from both teams; no picks',
                  limitations=['Unordered set reconstruction, not next-turn prediction.',
                               'Other bans can occur later in the real draft.',
                               'Masks within games and series are correlated.',
                               'Unseen targets retained as misses; no test evaluation.'])
    if hashlib.sha256(a.model.read_bytes()).hexdigest() != model_hash:
        raise ValueError('Model changed during evaluation')
    save(a.output_dir/'validation_metrics.json', report)
    save(a.output_dir/'validation_cases.json', cases)
    with (a.output_dir/'validation_summary.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['k', 'cases', 'hits', 'hit_rate', 'ndcg', 'catalog_coverage'])
        for k, m in report['metrics'].items():
            w.writerow([k] + [m[x] for x in ('cases', 'hits', 'hit_rate', 'ndcg', 'catalog_coverage')])
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
