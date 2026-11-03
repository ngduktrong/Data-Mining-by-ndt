"""Đọc và kiểm tra snapshot trước khi fit. Không đọc nhãn test trong develop."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

VERSION = '035ce761e53a47dbfd18ca1d9fabe7ceb0ec79115271bccac303bed2a6c0195c'


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def lineup(value, names):
    ids = json.loads(value)
    require(isinstance(ids, list) and len(ids) == 5, 'Đội hình phải có 5 tướng')
    require(all(isinstance(h, str) for h in ids), 'ID phải là chuỗi')
    require(len(set(ids)) == 5 and set(ids) <= set(names), 'ID trùng hoặc không hợp lệ')
    return ids


def check_data(data_dir):
    p = Path(data_dir)
    manifest = json.loads((p / 'manifest.json').read_text(encoding='utf-8'))
    require(manifest['dataset_version'] == VERSION, 'Sai snapshot')
    hashes = {}
    # Test payload không đọc ở giai đoạn phát triển; chỉ kiểm tra membership series từ metadata.
    for name in ['association_train.csv', 'train.csv', 'validation.csv', 'heroes.csv',
                 'split_assignments.csv']:
        hashes[name] = sha256(p / name)
        require(hashes[name] == manifest['files'][name]['sha256'], f'Sai hash: {name}')
    heroes = read_csv(p / 'heroes.csv')
    names = {r['hero_id']: r['name'] for r in heroes}
    require(len(names) == len(heroes), 'Trùng hero_id')
    assignments = read_csv(p / 'split_assignments.csv')
    assignment = {r['series_id']: r['split'] for r in assignments}
    require(len(assignment) == len(assignments), 'Trùng series assignment')
    times = defaultdict(list)
    for r in assignments:
        require(r['split'] in {'train', 'validation', 'test'}, 'Split không hợp lệ')
        times[r['split']].append(datetime.fromisoformat(r['split_time']))
    require(max(times['train']) < min(times['validation']) and
            max(times['validation']) < min(times['test']), 'Mốc lịch chia tập không tăng')
    rows = {}
    for split in ['train', 'validation']:
        rows[split] = read_csv(p / f'{split}.csv')
        require(len({r['game_id'] for r in rows[split]}) == len(rows[split]), 'Trùng game_id')
        for r in rows[split]:
            require(r['split'] == split and assignment[r['series_id']] == split, 'Sai split')
            a, b = lineup(r['team_a_heroes'], names), lineup(r['team_b_heroes'], names)
            require(not set(a) & set(b), 'Tướng trùng giữa hai đội')
            require(r['team_a_win'] in {'true', 'false'}, 'Boolean không hợp lệ')
    require({r['game_id'] for r in rows['train']}.isdisjoint(
        {r['game_id'] for r in rows['validation']}), 'Game giao nhau train/validation')
    transactions = read_csv(p / 'association_train.csv')
    keys = set()
    transaction_by_game = defaultdict(list)
    for r in transactions:
        require(r['split'] == 'train' and assignment[r['series_id']] == 'train', 'Transaction ngoài train')
        key = (r['game_id'], r['team_id'])
        require(key not in keys, 'Trùng transaction')
        keys.add(key)
        ids = lineup(r['hero_ids'], names)
        require(r['is_winner'] in {'true', 'false'}, 'Nhãn winner không hợp lệ')
        transaction_by_game[r['game_id']].append((tuple(sorted(ids)), r['is_winner'], r['series_id']))
    require(set(transaction_by_game) == {r['game_id'] for r in rows['train']}, 'Lệch ván train')
    for r in rows['train']:
        expected = [(tuple(sorted(json.loads(r['team_a_heroes']))), r['team_a_win'], r['series_id']),
                    (tuple(sorted(json.loads(r['team_b_heroes']))),
                     'false' if r['team_a_win'] == 'true' else 'true', r['series_id'])]
        require(Counter(transaction_by_game[r['game_id']]) == Counter(expected), 'Đội hình/nhãn không khớp train')
    catalog = {h for r in transactions for h in json.loads(r['hero_ids'])}
    report = {'status': 'passed', 'dataset_version': VERSION, 'hashes': hashes,
              'train_games': len(rows['train']), 'train_lineups': len(transactions),
              'validation_games': len(rows['validation']), 'train_catalog': len(catalog),
              'train_matrix_density': 5 / len(catalog), 'catalog_names': len(names),
              'series_counts': dict(Counter(assignment.values())),
              'test_payload_read': False, 'test_evaluation_launched': False,
              'scope': 'train_validation_integrity_and_series_split_metadata',
              'time_basis': 'series_schedule_proxy',
              'test_payload_integrity': 'deferred_until_final_test'}
    return transactions, names, rows['validation'], report
