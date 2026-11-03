"""Train-only experimental lineup completion with opponent outcome statistics."""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

VERSION = '035ce761e53a47dbfd18ca1d9fabe7ceb0ec79115271bccac303bed2a6c0195c'


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def fit_records(rows, names):
    pop, co = Counter(), defaultdict(Counter)
    opponents = defaultdict(dict)
    seen = set()
    for r in rows:
        if r['split'] != 'train':
            raise ValueError('Fit accepts train rows only')
        if r['game_id'] in seen:
            raise ValueError('Duplicate game')
        seen.add(r['game_id'])
        a, b = json.loads(r['team_a_heroes']), json.loads(r['team_b_heroes'])
        if len(a) != 5 or len(b) != 5 or len(set(a+b)) != 10 or any(h not in names for h in a+b):
            raise ValueError('Invalid lineup')
        if r['team_a_win'] not in ('true', 'false'):
            raise ValueError('Invalid outcome')
        win_a = r['team_a_win'] == 'true'
        for own, enemy, win in ((a,b,win_a), (b,a,not win_a)):
            pop.update(own)
            for h in own:
                co[h].update(x for x in own if x != h)
                for e in enemy:
                    p = opponents[h].setdefault(e, {'games':0, 'wins':0})
                    p['games'] += 1
                    p['wins'] += int(win)
    if not seen:
        raise ValueError('Empty train data')
    cosine = {h:{x:n/math.sqrt(pop[h]*pop[x]) for x,n in sorted(co[h].items())} for h in sorted(pop)}
    return dict(model_version='opponent_pick_train_v1', fit_split='train', train_games=len(seen),
                hero_names=names, popularity=dict(sorted(pop.items())), cosine=cosine,
                opponents={h:dict(sorted(opponents[h].items())) for h in sorted(opponents)},
                evaluated=False, config_selected_on_validation=False,
                score_definition='mean_ally_cosine + weight * mean_centered_smoothed_opponent_outcome',
                limitations=['Final-lineup completion; draft order unverified.',
                             'Opponent outcome associations are not causal counters or win probabilities.',
                             'No role, patch, team strength, side or tournament-rule adjustment.'])


def train(data):
    data = Path(data)
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    if manifest['dataset_version'] != VERSION:
        raise ValueError('Dataset mismatch')
    hashes = {}
    for name in ('train.csv','heroes.csv','split_assignments.csv'):
        hashes[name] = hashlib.sha256((data/name).read_bytes()).hexdigest()
        if hashes[name] != manifest['files'][name]['sha256']:
            raise ValueError('Hash mismatch: '+name)
    hero_rows = read_csv(data/'heroes.csv')
    names = {r['hero_id']:r['name'] for r in hero_rows}
    if len(names) != len(hero_rows): raise ValueError('Duplicate hero ID')
    assignments = {r['series_id']:r['split'] for r in read_csv(data/'split_assignments.csv')}
    rows = read_csv(data/'train.csv')
    if any(assignments.get(r['series_id']) != 'train' for r in rows):
        raise ValueError('Series assignment mismatch')
    model = fit_records(rows, names)
    model.update(dataset_version=VERSION, source_hashes=hashes,
                 validation_csv_opened=False, test_csv_opened=False)
    return model


def load_model(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def pair_signal(model, hero, enemy, alpha):
    p = model['opponents'].get(hero, {}).get(enemy, {'games':0,'wins':0})
    # Symmetric prior with alpha total pseudo-games and mean 0.5.
    return (p['wins'] - 0.5*p['games'])/(p['games']+alpha), p['games'], p['wins']


def recommend_picks(model, own_picks=None, enemy_picks=None, banned=None, k=5,
                    method='combined', weight=0.25, alpha=10.0):
    if method not in ('popularity','cosine','combined'): raise ValueError('Unknown method')
    if type(k) is not int or not 1 <= k <= 100: raise ValueError('k must be 1..100')
    for value in (weight, alpha):
        if isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError('Parameters must be finite numbers')
    if weight < 0 or alpha <= 0: raise ValueError('weight >= 0 and alpha > 0 required')
    groups = [([] if x is None else x) for x in (own_picks, enemy_picks, banned)]
    seen = set()
    for group in groups:
        if not isinstance(group,list) or any(not isinstance(h,str) for h in group):
            raise ValueError('Context must be lists of hero IDs')
        if len(set(group)) != len(group) or seen.intersection(group):
            raise ValueError('Duplicate or conflicting heroes')
        if any(h not in model['hero_names'] for h in group): raise ValueError('Unknown hero ID')
        seen.update(group)
    own, enemy, _ = groups
    if len(own)>4 or len(enemy)>5: raise ValueError('Own picks <= 4 and enemy picks <= 5 required')
    scores=[]
    for h,pop in model['popularity'].items():
        if h in seen: continue
        ally=sum(model['cosine'].get(h,{}).get(x,0.0) for x in own)/max(1,len(own))
        evidence=[]
        for e in enemy:
            signal,n,w=pair_signal(model,h,e,alpha)
            evidence.append(dict(enemy_hero_id=e, games=n, wins=w, centered_signal=signal))
        opponent=sum(e['centered_signal'] for e in evidence)/max(1,len(enemy))
        score=pop/(2*model['train_games']) if method=='popularity' else ally
        if method=='combined': score += weight*opponent
        scores.append(dict(hero_id=h, hero_name=model['hero_names'][h],score=score,
                           ally_score=ally, opponent_score=opponent,popularity_count=pop,
                           opponent_evidence=evidence))
    scores.sort(key=lambda r:(-r['score'],-r['popularity_count'],r['hero_id']))
    result=scores[:k]
    for rank,row in enumerate(result,1): row['rank']=rank
    return dict(model_version=model['model_version'], method=method, weight=weight, alpha=alpha,
                recommendations=result, returned_count=len(result), requested_k=k,
                unseen_context_heroes=sorted(seen-set(model['popularity'])),
                all_candidate_scores_zero=bool(scores) and all(r['score']==0 for r in scores),
                limitations=model['limitations'])


def main():
    root=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['train','demo'])
    p.add_argument('--data-dir',type=Path,default=root/'data/raw')
    p.add_argument('--model',type=Path,default=root/'artifacts/v2/opponent_pick/model.json')
    p.add_argument('--request',type=Path)
    a=p.parse_args()
    if a.command=='train':
        model=train(a.data_dir); save(a.model,model)
        result=dict(status='trained',model_version=model['model_version'],train_games=model['train_games'],
                    candidate_heroes=len(model['popularity']),
                    directed_opponent_pairs=sum(len(v) for v in model['opponents'].values()),
                    evaluated=False,config_selected_on_validation=False,model_path=str(a.model))
    else:
        # Empty default request shows cold-context popularity tie-break, not quality.
        req=json.loads(a.request.read_text(encoding='utf-8-sig')) if a.request else {}
        result=recommend_picks(load_model(a.model),**req)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
