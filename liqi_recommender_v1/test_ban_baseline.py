import unittest
from ban_baseline import fit_records, recommend_bans


class BanTests(unittest.TestCase):
    def setUp(self):
        self.names = {str(i): str(i) for i in range(20)}
        self.games = [dict(game_id='g', series_id='s', split='train')]
        self.actions = [dict(game_id='g', series_id='s', split='train',
                             hero_id=str(i), team_number=str(1 + i % 2),
                             action_type='pick' if i < 10 else 'ban') for i in range(18)]
        self.model = fit_records(self.games, self.actions, self.names)

    def test_holdout_payload_ignored(self):
        altered = self.actions + [dict(split='validation'), dict(split='test')]
        self.assertEqual(self.model, fit_records(self.games, altered, self.names))

    def test_filter_and_short_result(self):
        result = recommend_bans(self.model, own_picks=['10'], enemy_picks=['11'], banned=['12'], k=10)
        self.assertEqual(result['returned_count'], 5)
        self.assertFalse({'10', '11', '12'} & {r['hero_id'] for r in result['recommendations']})
        self.assertEqual(recommend_bans(self.model, banned=list(self.model['ban_counts']))['returned_count'], 0)

    def test_conflicts_and_duplicate_data(self):
        with self.assertRaises(ValueError):
            recommend_bans(self.model, own_picks=['1'], banned=['1'])
        with self.assertRaises(ValueError):
            fit_records(self.games, self.actions + [self.actions[-1]], self.names)


if __name__ == '__main__':
    unittest.main()
