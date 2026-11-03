import math
import unittest
from evaluate_bans import evaluate


class EvaluationTests(unittest.TestCase):
    def test_hand_calculated_metrics_and_unseen(self):
        model = dict(model_version='test', method='ban_popularity', train_games=10,
                     hero_names={h: h for h in 'abcd'}, ban_counts={'a': 9, 'b': 5, 'c': 1}, limitations=[])
        games = {'g': {'series_id': 's'}}
        # Targets b,d: b ranks second after a; d is unseen and remains a miss.
        report, cases = evaluate(model, games, {'g': {'b', 'd'}}, ks=(1, 2))
        self.assertEqual(report['metrics']['1']['hits'], 0)
        self.assertEqual(report['metrics']['2']['hit_rate'], 0.5)
        self.assertAlmostEqual(report['metrics']['2']['ndcg'], 1/math.log2(3)/2)
        self.assertEqual(report['unseen_target_cases'], 1)
        self.assertEqual(report['target_coverage'], 0.5)
        for case in cases:
            self.assertNotIn(case['target'], case['context'])
            self.assertFalse(set(case['context']) & set(case['recommendations']))
        self.assertEqual(model['ban_counts'], {'a': 9, 'b': 5, 'c': 1})

    def test_empty_data_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({}, {}, {})


if __name__ == '__main__':
    unittest.main()
