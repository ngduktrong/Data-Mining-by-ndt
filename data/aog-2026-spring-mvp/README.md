# AoG Spring 2026 — final MVP snapshot

Dataset version: `035ce761e53a47dbfd18ca1d9fabe7ceb0ec79115271bccac303bed2a6c0195c`.
Training-ready: **true**, scope: `post_draft_baseline_schedule_proxy`.

## Files

- `csv/train.csv`, `validation.csv`, `test.csv`: post-draft baseline rows, one game per row.
- `feature_schema.json`: the only allowed input features and label.
- `split_manifest.json`: cutoffs, per-series membership, counts and limitations.
- `validation.json`, `quality.json`: integrity checks and blockers.
- `csv/association_train.csv`: train-only mining transactions. Full `association_transactions.csv` is descriptive data, not a fit set.
- `csv/manifest.json`: source revisions, row counts and SHA-256 of every CSV.
- `csv/games.csv`, `series.csv`, `draft_actions.csv`: inspection exports with IDs/raw names/provenance.
- Other catalogs/statistics/prize tables are supplementary, not baseline features.

## Split

80/10/10 requested by series count, chronological and deterministic. All games of a series stay together; identical schedule timestamps cannot cross partitions.

| Partition | Series | Games |
| --- | ---: | ---: |
| train | 60 | 231 |
| validation | 7 | 28 |
| test | 8 | 40 |

## Use and limitations

Input: `team_a_heroes`, `team_b_heroes`, `team_a_side`, `patch_id`. Label: `team_a_win`.
Hero arrays are JSON sets; source slots are not player roles or draft order. Parse arrays with json.loads and boolean labels explicitly.
Fit encoders/preprocessing/model on train only. Tune with validation, evaluate test once. Unknown hero/patch categories in holdouts must be handled without refitting on them.
No target encoding, historical win rates, synergy or counter features are supplied. Never use full-tournament statistics as past-only features.
Temporal boundaries use series schedules as an explicitly accepted proxy. Actual game played_at stays null, and rescheduling/actual chronology is not independently verified.
A single tournament is a small sample; passing validation does not establish generalization or good model accuracy.
Draft sequence, per-game lineups and items are not verified; 14 person references are source redlinks, not verified biographies.
API acquisition permission does not establish redistribution rights. License/attribution review remains required before public distribution.
Keep older snapshots separate; merging versions duplicates games. Raw response archives and contact/policy diagnostics are not included in a release ZIP.
