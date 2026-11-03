import json
import math
import unittest
from evaluate_opponent_pick import make_cases, metric, select


class EvaluationTests(unittest.TestCase):
    def test_masks_and_outcome_not_used(self):
        row=dict(game_id='g',series_id='s',split='validation',team_a_heroes=json.dumps(list('01234')),
                 team_b_heroes=json.dumps(list('56789')),team_a_win='true')
        names={x:x for x in '0123456789'}
        a=make_cases([row],names)
        self.assertEqual(a,make_cases([{**row,'team_a_win':'false'}],names))
        self.assertEqual(len(a),10)
        for c in a:
            self.assertEqual(len(c['own_picks']),4)
            self.assertEqual(len(c['enemy_picks']),5)
            self.assertNotIn(c['target'],c['own_picks']+c['enemy_picks'])

    def test_metrics_and_tie_selection(self):
        self.assertEqual(metric(None,5),(0,0.0))
        self.assertEqual(metric(6,5),(0,0.0))
        self.assertAlmostEqual(metric(2,5)[1],1/math.log2(3))
        def result(method):
            return dict(config=dict(id=method,method=method,weight=0,alpha=10),
                        metrics={'5':dict(ndcg=0.2,hit_rate=0.3)})
        self.assertEqual(select([result('combined'),result('cosine')])['config']['method'],'cosine')


if __name__=='__main__':unittest.main()
