import json
import tempfile
import unittest
from pathlib import Path
from opponent_pick import fit_records, pair_signal, recommend_picks, save, load_model


class OpponentTests(unittest.TestCase):
    def setUp(self):
        self.names={str(i):str(i) for i in range(11)}
        self.row=dict(game_id='g',split='train',team_a_heroes=json.dumps(list('01234')),
                      team_b_heroes=json.dumps(list('56789')),team_a_win='true')
        self.model=fit_records([self.row],self.names)

    def test_direction_smoothing_and_unseen(self):
        s,n,w=pair_signal(self.model,'0','5',10)
        self.assertAlmostEqual(s,0.5/11)
        self.assertEqual((n,w),(1,1))
        self.assertAlmostEqual(pair_signal(self.model,'5','0',10)[0],-s)
        self.assertEqual(pair_signal(self.model,'0','10',10),(0.0,0,0))
        self.assertEqual(self.model['cosine']['0']['1'],1.0)

    def test_weight_zero_matches_cosine_and_filtering(self):
        args=dict(own_picks=['0'],enemy_picks=['5'],banned=['1'],k=10)
        a=recommend_picks(self.model,method='combined',weight=0,**args)
        b=recommend_picks(self.model,method='cosine',**args)
        self.assertEqual(a['recommendations'],b['recommendations'])
        self.assertEqual(a['returned_count'],7)
        self.assertFalse({'0','1','5'} & {r['hero_id'] for r in a['recommendations']})
        self.assertEqual(recommend_picks(self.model,banned=list(self.model['popularity']))['returned_count'],0)

    def test_reject_holdout_and_conflicts(self):
        with self.assertRaises(ValueError):
            fit_records([{**self.row,'split':'validation'}],self.names)
        with self.assertRaises(ValueError):
            recommend_picks(self.model,own_picks=['0'],enemy_picks=['0'])
        with self.assertRaises(ValueError):
            recommend_picks(self.model,alpha=0)

    def test_roundtrip_and_empty_context(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'model.json'
            save(path,self.model)
            self.assertEqual(recommend_picks(self.model),recommend_picks(load_model(path)))
        self.assertTrue(recommend_picks(self.model)['all_candidate_scores_zero'])


if __name__=='__main__': unittest.main()
