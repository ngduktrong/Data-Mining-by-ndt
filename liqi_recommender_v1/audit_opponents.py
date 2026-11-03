"""Audit train/validation opponent data. No fit, no test evaluation."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

VERSION = '035ce761e53a47dbfd18ca1d9fabe7ceb0ec79115271bccac303bed2a6c0195c'


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def audit(data):
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    if manifest['dataset_version'] != VERSION:
        raise ValueError('Dataset snapshot mismatch')
    hashes = {}
    for name in ('train.csv', 'validation.csv', 'heroes.csv', 'split_assignments.csv', 'draft_actions.csv'):
        hashes[name] = hashlib.sha256((data/name).read_bytes()).hexdigest()
        if hashes[name] != manifest['files'][name]['sha256']:
            raise ValueError('Hash mismatch: '+name)
    names = {r['hero_id']: r['name'] for r in read_csv(data/'heroes.csv')}
    assignments = {r['series_id']: r['split'] for r in read_csv(data/'split_assignments.csv')}
    issues, splits, all_games = [], {}, {}
    pairs = defaultdict(lambda: dict(games=0, first_wins=0))
    def issue(code, game):
        issues.append(dict(code=code, game_id=game))
    for split in ('train', 'validation'):
        rows = read_csv(data/(split+'.csv'))
        parsed = []
        for r in rows:
            g = r['game_id']
            if g in all_games: issue('duplicate_or_cross_split_game', g)
            if r['split'] != split or assignments.get(r['series_id']) != split:
                issue('split_mismatch', g)
            a, b = json.loads(r['team_a_heroes']), json.loads(r['team_b_heroes'])
            if len(a) != 5 or len(b) != 5 or len(set(a+b)) != 10:
                issue('invalid_lineup_or_overlap', g)
            if any(h not in names for h in a+b): issue('unknown_hero', g)
            win = r['team_a_win'].strip().lower()
            if win not in ('true', 'false'): issue('invalid_outcome', g)
            obj = dict(row=r, a=a, b=b, win=win == 'true')
            all_games[g] = obj
            parsed.append(obj)
            if split == 'train' and win in ('true', 'false'):
                for x in a:
                    for y in b:
                        first, second = sorted((x, y))
                        p = pairs[first, second]
                        p['games'] += 1
                        p['first_wins'] += int(obj['win'] if first == x else not obj['win'])
        splits[split] = dict(games=len(rows), series=len({r['series_id'] for r in rows}),
                             lineup_heroes=len({h for obj in parsed for h in obj['a']+obj['b']}),
                             outcomes=dict(Counter(r['team_a_win'] for r in rows)),
                             side_values=dict(Counter(r['team_a_side'] for r in rows)),
                             patch_values=dict(Counter(r['patch_id'] or '(missing)' for r in rows)),
                             time_basis=dict(Counter(r['time_basis'] for r in rows)))
    if issues:
        return dict(status='failed', issues=issues), []
    action_stats = {s: Counter() for s in splits}
    observed_picks = defaultdict(lambda: defaultdict(set))
    with (data/'draft_actions.csv').open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if r['split'] not in splits: continue
            s, g = r['split'], r['game_id']
            if g not in all_games or all_games[g]['row']['split'] != s:
                issue('action_linkage_mismatch', g)
                continue
            if r['action_type'] != 'pick': continue
            st = action_stats[s]
            st['pick_rows'] += 1
            st['missing_sequence'] += int(not r['sequence_number'])
            st['missing_phase'] += int(not r['phase'])
            st['order_'+r['draft_order_status']] += 1
            observed_picks[g][r['team_number']].add(r['hero_id'])
    for g, obj in all_games.items():
        if observed_picks[g]['1'] != set(obj['a']) or observed_picks[g]['2'] != set(obj['b']):
            issue('canonical_vs_action_pick_mismatch', g)
    validation_support = []
    unseen_heroes = set()
    train_catalog = {h for obj in all_games.values() if obj['row']['split']=='train' for h in obj['a']+obj['b']}
    for obj in all_games.values():
        if obj['row']['split'] != 'validation': continue
        unseen_heroes.update(set(obj['a']+obj['b'])-train_catalog)
        for x in obj['a']:
            for y in obj['b']:
                p = pairs.get(tuple(sorted((x,y))))
                validation_support.append(p['games'] if p else 0)
    def bins(values):
        return {'zero':sum(v==0 for v in values), '1_to_4':sum(1<=v<=4 for v in values),
                '5_to_9':sum(5<=v<=9 for v in values), '10_plus':sum(v>=10 for v in values)}
    table = []
    for (x,y), p in sorted(pairs.items()):
        table.append(dict(hero_1=x, hero_1_name=names[x], hero_2=y, hero_2_name=names[y],
                          games=p['games'], hero_1_team_wins=p['first_wins'],
                          hero_2_team_wins=p['games']-p['first_wins']))
    report = dict(status='passed_with_limitations' if not issues else 'failed', errors=len(issues), issues=issues,
                  dataset_version=VERSION, source_hashes=hashes, splits=splits,
                  pick_action_metadata={s:dict(v) for s,v in action_stats.items()},
                  train_opponent_pairs=dict(unique_unordered_pairs=len(pairs),
                      pair_game_events=sum(p['games'] for p in pairs.values()),
                      support_bins=bins([p['games'] for p in pairs.values()])),
                  validation_opponent_pair_events=dict(total=len(validation_support),
                      train_support_bins=bins(validation_support)),
                  validation_heroes_unseen_in_train_picks=[dict(hero_id=h,name=names[h]) for h in sorted(unseen_heroes)],
                  test_csv_opened=False, mixed_split_actions_scanned=True,
                  model_trained=False, model_evaluated=False,
                  limitations=['Final lineups do not establish what was known at a draft turn.',
                               'Outcome counts reflect whole-team results, not isolated hero counters.',
                               'Pair events within games/series are correlated.',
                               'Patch IDs are source metadata; correctness is not independently verified.'])
    return report, table


def main():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir', type=Path, default=root/'data/raw')
    p.add_argument('--output-dir', type=Path, default=root/'reports/v2/opponent_audit')
    a = p.parse_args()
    report, table = audit(a.data_dir)
    a.output_dir.mkdir(parents=True, exist_ok=True)
    save(a.output_dir/'opponent_audit.json', report)
    if table:
        with (a.output_dir/'train_opponent_pairs.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if report['status']=='failed': raise SystemExit(1)


if __name__=='__main__': main()
