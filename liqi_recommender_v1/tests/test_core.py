import json, math, tempfile, unittest
from pathlib import Path
from src.train import fit
from src.recommender import load_model, recommend
from src.evaluate import evaluate, case_score

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.names = {h: h for h in 'ABCDEFGH'}
        self.rows = [{'split':'train','hero_ids':json.dumps(list(s))} for s in ['ABCDE','ABCDF']]
        self.model = fit(self.rows,self.names,'item_item_count')
    def test_counts(self):
        self.assertEqual(self.model['weights']['A']['B'],2)
        self.assertEqual(self.model['weights']['A']['E'],1)
        self.assertNotIn('A',self.model['weights']['A'])
        self.assertAlmostEqual(fit(self.rows,self.names,'item_item_cosine')['weights']['A']['E'],1/math.sqrt(2))
    def test_input_errors(self):
        for own,enemy,banned,k in [(['A','A'],[],[],5),(['A'],['A'],[],5),(['A'],[],['A'],5),(['?'],[],[],5),(list('ABCDE'),[],[],5),([],[],[],True),([],[],[],0),('A',[],[],5)]:
            with self.assertRaises(ValueError): recommend(self.model,own,enemy,banned,k)
    def test_filter_short_empty(self):
        r=recommend(self.model,['A','B'],['C','D'],['E'],10)
        self.assertEqual([x['hero_id'] for x in r['recommendations']],['F'])
        self.assertEqual(recommend(self.model,['A','B'],['C','D'],['E','F'])['returned_count'],0)
    def test_fallback(self):
        r=recommend(self.model,['G'],k=3)
        self.assertEqual(r['unseen_context_heroes'],['G'])
        self.assertTrue(all(x['source']=='popularity_fallback' for x in r['recommendations']))
        self.assertEqual([x['hero_id'] for x in r['recommendations']],['A','B','C'])
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'model.json';p.write_text(json.dumps(self.model))
            self.assertEqual(recommend(self.model,['A']),recommend(load_model(p),['A']))
    def test_metrics_unseen(self):
        self.assertEqual(case_score(None,5),(0,0));self.assertEqual(case_score(6,5),(0,0))
        self.assertEqual(case_score(1,5),(1,1));self.assertAlmostEqual(case_score(2,5)[1],1/math.log2(3))
        rows=[{'game_id':'g','series_id':'s','team_a_heroes':json.dumps(list('ABCDG')),'team_b_heroes':json.dumps(list('ABCDH'))}]
        metrics,records=evaluate(self.model,rows)
        self.assertEqual(metrics['metrics']['5']['cases'],10)
        self.assertEqual(metrics['metrics']['5']['unseen_target_cases'],2)
        self.assertTrue(all(r['rank'] is None for r in records if not r['target_seen']))
    def test_no_holdout_fit(self):
        with self.assertRaises(ValueError):fit([{'split':'validation','hero_ids':'["A"]'}],self.names,'popularity')
if __name__=='__main__':unittest.main()
