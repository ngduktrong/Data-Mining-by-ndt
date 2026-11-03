"""Bước 3: audit ban train/validation, không fit hoặc đánh giá mô hình.
Chép file cạnh run.py rồi chạy: python audit_bans.py
"""
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


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def save_csv(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def audit(data):
    manifest = json.loads((data / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['dataset_version'] != VERSION:
        raise ValueError('Sai snapshot dữ liệu')
    hashes = {}
    for name in ['draft_actions.csv', 'train.csv', 'validation.csv', 'heroes.csv', 'split_assignments.csv']:
        hashes[name] = hashlib.sha256((data / name).read_bytes()).hexdigest()
        if hashes[name] != manifest['files'][name]['sha256']:
            raise ValueError('Sai hash: ' + name)
    names_rows = read_csv(data / 'heroes.csv')
    names = {r['hero_id']: r['name'] for r in names_rows}
    if len(names) != len(names_rows): raise ValueError('Trùng hero_id')
    assignments_rows = read_csv(data / 'split_assignments.csv')
    assignment = {r['series_id']: r['split'] for r in assignments_rows}
    if len(assignment) != len(assignments_rows): raise ValueError('Trùng series assignment')
    games, issues, info = {}, [], {}

    def issue(severity, code, game='', team='', detail=''):
        issues.append({'severity': severity, 'code': code, 'game_id': game,
                       'team_number': team, 'detail': detail})

    for split in ['train', 'validation']:
        rows = read_csv(data / f'{split}.csv')
        for r in rows:
            gid = r['game_id']
            if gid in games: issue('error', 'duplicate_or_cross_split_game', gid)
            if r['split'] != split or assignment.get(r['series_id']) != split:
                issue('error', 'game_split_mismatch', gid)
            games[gid] = r
        info[split] = {'games': len(rows), 'series': len({r['series_id'] for r in rows})}

    # File nguồn chứa cả test; chỉ dùng nhãn split để loại test ngay khi đọc dòng.
    # Hash xác minh toàn file nhưng không tính thống kê tướng test.
    actions = []
    with (data / 'draft_actions.csv').open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if r['split'] == 'test': continue
            if r['split'] not in ['train', 'validation']:
                issue('error', 'unknown_split', detail=r['split']); continue
            actions.append(r)
    group = defaultdict(list)
    field_keys = Counter()
    for r in actions:
        gid, team, hero = r['game_id'], r['team_number'], r['hero_id']
        game = games.get(gid)
        if game is None: issue('error', 'action_game_not_found', gid, team)
        elif r['split'] != game['split'] or r['series_id'] != game['series_id']:
            issue('error', 'action_game_link_mismatch', gid, team)
        if assignment.get(r['series_id']) != r['split']:
            issue('error', 'action_series_split_mismatch', gid, team)
        if team not in ['1', '2']: issue('error', 'invalid_team_number', gid, team)
        if r['action_type'] not in ['pick', 'ban']: issue('error', 'unknown_action_type', gid, team)
        if not hero: issue('error', 'missing_hero_id', gid, team)
        elif hero not in names: issue('error', 'unknown_hero_id', gid, team, hero)
        if r['validation_status'] != 'valid_raw': issue('warning', 'source_validation_status', gid, team, r['validation_status'])
        field_keys[(gid, r['source_field'])] += 1
        group[(gid, team, r['action_type'])].append(r)
    for (gid, field), n in field_keys.items():
        if n > 1: issue('error', 'duplicate_source_field', gid, detail=f'{field}: {n}')

    team_rows, game_rows, transactions = [], [], []
    for gid, game in sorted(games.items()):
        all_picks, all_bans = [], []
        for team, col in [('1', 'team_a_heroes'), ('2', 'team_b_heroes')]:
            picks = [r['hero_id'] for r in group[(gid, team, 'pick')]]
            bans = [r['hero_id'] for r in group[(gid, team, 'ban')]]
            expected = json.loads(game[col])
            if len(expected) != 5 or len(set(expected)) != 5 or not set(expected) <= set(names):
                issue('error', 'invalid_game_lineup', gid, team)
            if Counter(picks) != Counter(expected): issue('error', 'pick_lineup_mismatch', gid, team)
            if len(bans) != len(set(bans)): issue('error', 'duplicate_ban_same_team', gid, team)
            if not bans: issue('warning', 'no_observed_bans', gid, team)
            # 4 là mẫu phổ biến cần đối chiếu, không giả định luật giải bắt buộc.
            if len(bans) != 4: issue('warning', 'ban_count_not_four_review', gid, team, str(len(bans)))
            team_rows.append({'split': game['split'], 'game_id': gid, 'series_id': game['series_id'],
                              'team_number': team, 'observed_ban_count': len(bans),
                              'hero_ids': json.dumps(bans),
                              'hero_names': json.dumps([names.get(h, h) for h in bans], ensure_ascii=False)})
            all_picks += picks; all_bans += bans
        if len(all_picks) != len(set(all_picks)): issue('error', 'duplicate_pick_across_teams', gid)
        if len(all_bans) != len(set(all_bans)): issue('error', 'duplicate_ban_across_teams', gid)
        if set(all_bans) & set(all_picks): issue('error', 'pick_ban_overlap', gid, detail=json.dumps(sorted(set(all_bans)&set(all_picks))))
        game_rows.append({'split': game['split'], 'game_id': gid, 'series_id': game['series_id'],
                          'observed_bans': len(all_bans), 'unique_bans': len(set(all_bans))})
        transactions.append({'split': game['split'], 'game_id': gid, 'series_id': game['series_id'],
                             'observed_ban_ids': sorted(set(all_bans))})
    for split in info:
        aa = [r for r in actions if r['split'] == split]
        bans = [r for r in aa if r['action_type'] == 'ban']
        info[split].update({'pick_rows': sum(r['action_type']=='pick' for r in aa),
                           'ban_rows': len(bans), 'unique_banned_heroes': len({r['hero_id'] for r in bans}),
                           'ban_count_per_team_distribution': dict(Counter(r['observed_ban_count'] for r in team_rows if r['split']==split)),
                           'ban_count_per_game_distribution': dict(Counter(r['observed_bans'] for r in game_rows if r['split']==split)),
                           'missing_sequence_rows': sum(not r['sequence_number'] for r in bans),
                           'missing_phase_rows': sum(not r['phase'] for r in bans),
                           'order_status_counts': dict(Counter(r['draft_order_status'] for r in bans))})
    train_bans = [r for r in actions if r['split']=='train' and r['action_type']=='ban']
    counts = Counter(r['hero_id'] for r in train_bans)
    freq = [{'hero_id': h, 'hero_name': names.get(h,h), 'ban_count': n,
             'games_banned': len({r['game_id'] for r in train_bans if r['hero_id']==h})}
            for h,n in sorted(counts.items(), key=lambda x:(-x[1], x[0]))]
    val_bans = [r for r in actions if r['split']=='validation' and r['action_type']=='ban']
    unseen = [r for r in val_bans if r['hero_id'] not in counts]
    errors = sum(r['severity']=='error' for r in issues)
    summary = {'status': 'failed' if errors else 'passed_with_warnings' if issues else 'passed',
               'dataset_version': VERSION, 'scope': 'ban_audit_train_validation_only',
               'source_hashes': hashes, 'splits': info,
               'errors': errors, 'warnings': sum(r['severity']=='warning' for r in issues),
               'issue_counts': dict(Counter(r['code'] for r in issues)),
               'validation_ban_events_unseen_in_train_bans': len(unseen),
               'validation_unseen_ban_heroes': [{'hero_id':h,'hero_name':names.get(h,h)} for h in sorted({r['hero_id'] for r in unseen})],
               'test_csv_opened': False, 'mixed_split_draft_file_scanned': True,
               'test_rows_policy': 'skip_by_split_before_hero_statistics_or_evaluation',
               'model_trained': False, 'model_evaluated': False,
               'draft_order_verified': False,
               'readiness': 'review_warnings_then_design_unordered_ban_baseline' if not errors else 'resolve_errors_before_training'}
    return summary, issues, team_rows, game_rows, transactions, freq


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=root/'data/raw')
    parser.add_argument('--output-dir', type=Path, default=root/'reports/v2/ban_audit')
    args = parser.parse_args(); out = args.output_dir; out.mkdir(parents=True,exist_ok=True)
    try:
        summary, issues, teams, games, transactions, freq = audit(args.data_dir)
    except Exception as exc:
        save_json(out/'ban_quality_report.json', {'status':'failed','error':str(exc)})
        raise SystemExit(str(exc))
    save_json(out/'ban_quality_report.json',summary)
    save_csv(out/'ban_issues.csv',issues,['severity','code','game_id','team_number','detail'])
    save_csv(out/'bans_by_team.csv',teams,['split','game_id','series_id','team_number','observed_ban_count','hero_ids','hero_names'])
    save_csv(out/'bans_by_game.csv',games,['split','game_id','series_id','observed_bans','unique_bans'])
    save_csv(out/'train_ban_frequency.csv',freq,['hero_id','hero_name','ban_count','games_banned'])
    save_json(out/'observed_ban_sets_train_validation.json',transactions)
    lines=['# Bước 3 — Kiểm tra dữ liệu ban','',f"Trạng thái: {summary['status']}. Lỗi: {summary['errors']}; cảnh báo: {summary['warnings']}.",'',
           '| Tập | Ván | Lượt ban | Tướng bị ban | Phân bố số ban/ván |','|---|---:|---:|---:|---|']
    for split,d in summary['splits'].items():
        lines.append(f"| {split} | {d['games']} | {d['ban_rows']} | {d['unique_banned_heroes']} | {d['ban_count_per_game_distribution']} |")
    lines += ['', '## Những điều cần giữ đúng',
              '- Không có thứ tự ban được xác minh; số ban khác 4/đội chỉ được gắn cờ để xem nguồn, không tự sửa hoặc xóa.',
              '- Bảng tần suất chỉ dùng train; đây là thống kê audit, chưa có mô hình ban hoặc kết quả đánh giá ban.',
              '- Không mở test.csv. draft_actions.csv chứa các tập cùng file: script quét nhãn split và loại dòng test trước thống kê tướng. Không tuyên bố toàn bộ file test chưa từng được đọc ở mức bytes.',
              '- V1 đã được đánh giá test trên máy người dùng. Không sửa code, mô hình hoặc kết quả V1 trong bước này.',
              '- Xem ban_issues.csv và bans_by_team.csv để truy vết cảnh báo. Không coi mẫu ít ban là dữ liệu đầy đủ cho đến khi đối chiếu nguồn.',
              f"- Số ban validation có tướng chưa từng bị ban trong train: {summary['validation_ban_events_unseen_in_train_bans']}.",
              '', '## Đề xuất công việc 4 (chưa thực hiện)',
              'Chốt cách xử lý bản ghi cần xem lại; sau đó học baseline ban theo tần suất train. Thiết kế đánh giá khôi phục tập ban riêng, không dùng pick cuối trận làm thông tin biết trước ban.']
    (out/'KET_QUA_KIEM_TRA_BAN.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2));print('Báo cáo:',out)
    if summary['errors']:raise SystemExit(1)

if __name__=='__main__':main()
