"""P2 retrospective lineup reconstruction; validation only, no refit."""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import opponent_pick
from opponent_pick import VERSION, load_model, read_csv, recommend_picks, save

CONFIGS = [dict(id='popularity',method='popularity',weight=0,alpha=10),
           dict(id='cosine',method='cosine',weight=0,alpha=10)] + [
    dict(id=f'combined_w{w}_a{a}',method='combined',weight=w,alpha=a)
    for w in (0.1,0.25,0.5) for a in (10,30)]


def make_cases(rows, names):
    cases=[]
    seen=set()
    for r in sorted(rows,key=lambda r:r['game_id']):
        if r['split']!='validation' or r['game_id'] in seen:
            raise ValueError('Invalid validation split or duplicate game')
        seen.add(r['game_id'])
        a,b=json.loads(r['team_a_heroes']),json.loads(r['team_b_heroes'])
        if len(a)!=5 or len(b)!=5 or len(set(a+b))!=10 or any(h not in names for h in a+b):
            raise ValueError('Invalid lineup')
        for team,own,enemy in (('a',a,b),('b',b,a)):
            for target in sorted(own):
                cases.append(dict(game_id=r['game_id'],series_id=r['series_id'],team=team,
                                  target=target,own_picks=sorted(h for h in own if h!=target),
                                  enemy_picks=sorted(enemy)))
    if not cases: raise ValueError('Empty validation')
    return cases


def metric(rank,k):
    hit=int(rank is not None and rank<=k)
    return hit, 1/math.log2(rank+1) if hit else 0.0


def evaluate(model,cases,config):
    predictions=[]
    for case in cases:
        result=recommend_picks(model,own_picks=case['own_picks'],enemy_picks=case['enemy_picks'],
                               k=10,**{key:config[key] for key in ('method','weight','alpha')})
        ids=[r['hero_id'] for r in result['recommendations']]
        if len(ids)!=len(set(ids)) or set(ids)&set(case['own_picks']+case['enemy_picks']):
            raise ValueError('Invalid recommendations')
        predictions.append(dict(**case,recommendations=ids,
                                rank_at_10=ids.index(case['target'])+1 if case['target'] in ids else None))
    metrics={}
    for k in (5,10):
        hits=0; ndcg=0.0; covered=set(); series=defaultdict(lambda:dict(cases=0,hits=0,ndcg_sum=0.0))
        for row in predictions:
            hit,gain=metric(row['rank_at_10'],k)
            hits+=hit; ndcg+=gain; covered.update(row['recommendations'][:k])
            s=series[row['series_id']];s['cases']+=1;s['hits']+=hit;s['ndcg_sum']+=gain
        metrics[str(k)]=dict(cases=len(cases),hits=hits,hit_rate=hits/len(cases),ndcg=ndcg/len(cases),
                            catalog_coverage=len(covered)/len(model['popularity']),
                            full_k_rate=sum(len(r['recommendations'])>=k for r in predictions)/len(cases),
                            invalid_recommendation_rate=0.0,per_series=dict(series))
    return dict(config=config,metrics=metrics,
                unseen_target_cases=sum(c['target'] not in model['popularity'] for c in cases)),predictions


def select(results):
    # Exact metric ties: simpler method, smaller weight, larger alpha, then ID.
    return min(results,key=lambda r:(-r['metrics']['5']['ndcg'],-r['metrics']['5']['hit_rate'],
               {'popularity':0,'cosine':1,'combined':2}[r['config']['method']],
               r['config']['weight'],-r['config']['alpha'],r['config']['id']))


def main():
    root=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,default=root/'data/raw')
    p.add_argument('--model',type=Path,default=root/'artifacts/v2/opponent_pick/model.json')
    p.add_argument('--output-dir',type=Path,default=root/'reports/v2/pick_validation')
    a=p.parse_args()
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    model_hash=sha(a.model);model=load_model(a.model)
    manifest=json.loads((a.data_dir/'manifest.json').read_text(encoding='utf-8'))
    if manifest['dataset_version']!=VERSION or model['dataset_version']!=VERSION or model['fit_split']!='train':
        raise ValueError('Model/dataset provenance mismatch')
    hashes={}
    for name in ('validation.csv','split_assignments.csv'):
        hashes[name]=sha(a.data_dir/name)
        if hashes[name]!=manifest['files'][name]['sha256']:raise ValueError('Hash mismatch: '+name)
    for name,h in model['source_hashes'].items():
        if h!=manifest['files'][name]['sha256']:raise ValueError('Training source mismatch')
    assignments={r['series_id']:r['split'] for r in read_csv(a.data_dir/'split_assignments.csv')}
    rows=read_csv(a.data_dir/'validation.csv')
    if any(assignments.get(r['series_id'])!='validation' for r in rows):raise ValueError('Series split mismatch')
    cases=make_cases(rows,model['hero_names'])
    protocol=dict(name='P2_leave_one_pick_out_final_enemy_lineup',split='validation',
                  context='4 allies + 5 final enemy picks; no bans or outcome inputs',
                  configs=CONFIGS,selection='NDCG@5 then Hit@5 then simplicity/weight/alpha/ID',
                  model_sha256=model_hash,dataset_version=VERSION,source_hashes=hashes,
                  inference_code_sha256=sha(Path(opponent_pick.__file__)),
                  evaluation_code_sha256=sha(Path(__file__)),
                  model_refit=False,test_csv_opened=False,
                  limitations=['Retrospective reconstruction, not chronological draft prediction.',
                               'Validation used for selection; selected score is not independent test evidence.',
                               'Masks within games/series correlated; only 7 validation series.',
                               'No claims of counter strength or improved win probability.'])
    # Persist full search plan before scoring.
    save(a.output_dir/'evaluation_plan.json',protocol)
    results=[]; all_predictions={}
    for config in CONFIGS:
        result,predictions=evaluate(model,cases,config)
        results.append(result);all_predictions[config['id']]=predictions
        m=result['metrics']['5']
        print(f"{config['id']}: NDCG@5={m['ndcg']:.6f} Hit@5={m['hit_rate']:.6f}")
    winner=select(results)
    if sha(a.model)!=model_hash:raise ValueError('Model changed during evaluation')
    save(a.output_dir/'all_metrics.json',dict(protocol=protocol,results=results))
    save(a.output_dir/'all_predictions.json',all_predictions)
    save(a.output_dir/'selected_config.json',dict(config=winner['config'],model_sha256=model_hash,
         inference_code_sha256=protocol['inference_code_sha256'],protocol=protocol['name'],
         selected_on='validation',independent_test_evaluated=False,metrics=winner['metrics'],
         note='Pass method/weight/alpha explicitly to recommend_picks; model defaults unchanged.'))
    with (a.output_dir/'validation_comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['id','ndcg_at_5','hit_at_5','ndcg_at_10','hit_at_10','coverage_at_5','unseen_target_cases'])
        for r in results:
            x,y=r['metrics']['5'],r['metrics']['10']
            w.writerow([r['config']['id'],x['ndcg'],x['hit_rate'],y['ndcg'],y['hit_rate'],x['catalog_coverage'],r['unseen_target_cases']])
    print('Selected on validation:',winner['config'])


if __name__=='__main__':main()
