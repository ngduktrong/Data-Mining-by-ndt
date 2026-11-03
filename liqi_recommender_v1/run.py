"""Chạy từ thư mục dự án: python run.py develop | demo | final-test --confirm-final-test"""
import argparse
import csv
import json
import platform
import shutil
from pathlib import Path
from src.data_loader import check_data, read_csv, require, sha256, lineup
from src.train import fit
from src.evaluate import evaluate
from src.recommender import load_model, recommend

ROOT = Path(__file__).resolve().parent


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def code_hashes():
    return {str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT / 'src').glob('*.py'))} | {'run.py': sha256(ROOT / 'run.py')}


def develop():
    require(not (ROOT / 'reports/test_metrics.json').exists(),
            'Test đã được dùng. Tạo vòng nghiên cứu mới với holdout mới để phát triển tiếp.')
    config = json.loads((ROOT / 'configs/experiment.json').read_text(encoding='utf-8'))
    methods = ['popularity', 'item_item_count', 'item_item_cosine']
    require(config['methods'] == methods and config['protocol'] == 'P1_leave_one_hero_out_ally_only'
            and config['primary_k'] == 5 and config['secondary_k'] == 10
            and config['fit_split'] == 'train', 'Config không thuộc giao thức đã triển khai')
    save(ROOT / 'reports/experiment_config.json', config)
    try:
        transactions, names, validation, report = check_data(ROOT / 'data/raw')
    except Exception as exc:
        save(ROOT / 'reports/data_quality_report.json', {'status': 'failed', 'error': str(exc)})
        raise
    save(ROOT / 'reports/data_quality_report.json', report)
    results = []
    for method in methods:
        model = fit(transactions, names, method)
        model_path = ROOT / f'artifacts/{method}.json'
        save(model_path, model)
        require(load_model(model_path) == model, 'Lưu/nạp mô hình không nhất quán')
        metrics, predictions = evaluate(load_model(model_path), validation)
        save(ROOT / f'reports/{method}_validation_predictions.json', predictions)
        results.append(metrics)
    winner = max(results, key=lambda r: (r['metrics']['5']['ndcg'],
                 r['metrics']['5']['hit_rate'], -methods.index(r['method'])))
    save(ROOT / 'reports/validation_metrics.json', results)
    with (ROOT / 'reports/validation_comparison.csv').open('w', encoding='utf-8-sig', newline='') as f:
        fields = ['method', 'ndcg_at_5', 'hit_rate_at_5', 'ndcg_at_10', 'coverage_at_5', 'unseen_target_cases']
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for r in results:
            a, b = r['metrics']['5'], r['metrics']['10']
            writer.writerow(dict(zip(fields, [r['method'], a['ndcg'], a['hit_rate'], b['ndcg'],
                                              a['catalog_coverage'], a['unseen_target_cases']])))
    shutil.copy2(ROOT / f'artifacts/{winner["method"]}.json', ROOT / 'artifacts/selected_model.json')
    lock = {'status': 'selected_on_validation_test_pending', 'method': winner['method'],
            'selection_rule': 'ndcg@5_then_hit@5_then_simplicity',
            'model_sha256': sha256(ROOT / 'artifacts/selected_model.json'),
            'config_sha256': sha256(ROOT / 'configs/experiment.json'),
            'code_hashes': code_hashes(), 'dataset_version': report['dataset_version'],
            'fit_split': 'train', 'test_evaluation_launched': False, 'python': platform.python_version()}
    save(ROOT / 'artifacts/selection_lock.json', lock)
    handoff = ROOT / 'handoff'; handoff.mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'artifacts/selected_model.json', handoff / 'model.json')
    shutil.copy2(ROOT / 'src/recommender.py', handoff / 'recommender.py')
    save(handoff / 'model_metadata.json', lock)
    save(handoff / 'validation_metrics.json', winner)
    sample = json.loads(transactions[0]['hero_ids'])[:2]
    save(handoff / 'example_request.json', {'own_picks': sample, 'enemy_picks': [], 'banned': [], 'k': 5})
    for r in results:
        print(r['method'], 'NDCG@5=', round(r['metrics']['5']['ndcg'], 6),
              'Hit@5=', round(r['metrics']['5']['hit_rate'], 6))
    print('Được chọn trên validation:', winner['method'], '| Test chưa chạy')


def final_test(confirm):
    require(confirm, 'Cần --confirm-final-test sau khi chốt mô hình; lệnh này sẽ sử dụng test.')
    require(not (ROOT / 'reports/test_metrics.json').exists(), 'Đã có kết quả test; không chạy lại để chọn mô hình')
    lock = json.loads((ROOT / 'artifacts/selection_lock.json').read_text(encoding='utf-8'))
    require(lock['model_sha256'] == sha256(ROOT / 'artifacts/selected_model.json'), 'Model đã thay đổi')
    require(lock['config_sha256'] == sha256(ROOT / 'configs/experiment.json'), 'Config đã thay đổi')
    require(lock['code_hashes'] == code_hashes(), 'Code đã thay đổi từ lúc chọn mô hình')
    check_data(ROOT / 'data/raw')
    model = load_model(ROOT / 'artifacts/selected_model.json')
    p = ROOT / 'data/raw'
    manifest = json.loads((p / 'manifest.json').read_text(encoding='utf-8'))
    require(sha256(p / 'test.csv') == manifest['files']['test.csv']['sha256'], 'Sai hash test')
    rows = read_csv(p / 'test.csv')
    assignments = {r['series_id']: r['split'] for r in read_csv(p / 'split_assignments.csv')}
    known_games = {r['game_id'] for s in ['train', 'validation'] for r in read_csv(p / f'{s}.csv')}
    require(len({r['game_id'] for r in rows}) == len(rows), 'Trùng test game')
    for r in rows:
        require(r['split'] == 'test' and assignments[r['series_id']] == 'test'
                and r['game_id'] not in known_games, 'Sai split test')
        a = lineup(r['team_a_heroes'], model['hero_names'])
        b = lineup(r['team_b_heroes'], model['hero_names'])
        require(not set(a) & set(b), 'Tướng trùng hai đội test')
    result, predictions = evaluate(model, rows)
    save(ROOT / 'reports/test_metrics.json', result)
    save(ROOT / 'reports/test_predictions.json', predictions)
    save(ROOT / 'handoff/test_metrics.json', result)
    lock['status'] = 'final_test_evaluated'; lock['test_evaluation_launched'] = True
    save(ROOT / 'handoff/model_metadata.json', lock)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'develop', 'demo', 'final-test'])
    parser.add_argument('--confirm-final-test', action='store_true')
    args = parser.parse_args()
    if args.command == 'develop': develop()
    elif args.command == 'check':
        *_, report = check_data(ROOT / 'data/raw')
        save(ROOT / 'reports/data_quality_report.json', report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.command == 'demo':
        model = load_model(ROOT / 'artifacts/selected_model.json')
        request = json.loads((ROOT / 'handoff/example_request.json').read_text(encoding='utf-8'))
        print(json.dumps(recommend(model, **request), ensure_ascii=False, indent=2))
    else: final_test(args.confirm_final_test)
