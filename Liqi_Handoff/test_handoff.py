import unittest
from liqi_draft import DraftRecommender
from liqi_draft.opponent_pick import recommend_picks
from liqi_draft.ban_baseline import recommend_bans


class HandoffTests(unittest.TestCase):
    def setUp(self): self.service=DraftRecommender()

    def test_selected_method_and_rank_preserved(self):
        s=self.service
        ids=sorted(s._pick['popularity'])
        ctx=dict(own_picks=ids[:2],enemy_picks=ids[2:4],banned=ids[4:6],k=10)
        for action in ('pick','ban'):
            out=s.recommend(dict(action=action,**ctx))
            raw=(recommend_picks(s._pick,**ctx,method='cosine',weight=0,alpha=10) if action=='pick'
                 else recommend_bans(s._ban,**ctx))
            self.assertEqual([(r['hero_id'],r['score']) for r in out['recommendations']],
                             [(r['hero_id'],r['score']) for r in raw['recommendations']])
            self.assertEqual(out['method'],'cosine' if action=='pick' else 'ban_popularity')

    def test_conflicts_and_invalid_input(self):
        h=self.service.heroes()[0]['hero_id']
        for req in ({'action':'counter'}, {'action':'pick','k':True}, {'action':'ban','banned':None},
                    {'action':'pick','method':'combined'}, {'action':'pick','own_picks':[h],'banned':[h]}):
            with self.assertRaises(ValueError): self.service.recommend(req)

    def test_no_candidates(self):
        for action in ('pick','ban'):
            result=self.service.recommend(dict(action=action,banned=[h['hero_id'] for h in self.service.heroes()]))
            self.assertEqual(result['returned_count'],0)

    def test_repeated_calls_do_not_change_model(self):
        request=dict(action='pick')
        first=self.service.recommend(request)
        self.service.recommend(dict(action='ban'))
        self.assertEqual(first,self.service.recommend(request))


if __name__=='__main__':unittest.main()
