"""Stable pick/ban interface for the evaluated baseline release."""
import hashlib
import json
from pathlib import Path
from . import opponent_pick, ban_baseline


class DraftRecommender:
    def __init__(self):
        root = Path(__file__).resolve().parent
        manifest = json.loads((root/'release_manifest.json').read_text(encoding='utf-8'))
        for name, expected in manifest['files'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
                raise ValueError('Release file checksum mismatch: '+name)
        self._pick = opponent_pick.load_model(root/'models/pick.json')
        self._ban = ban_baseline.load_model(root/'models/ban.json')
        self._selection = json.loads((root/'models/selected_config.json').read_text(encoding='utf-8'))
        if self._selection['model_sha256'] != manifest['files']['models/pick.json']:
            raise ValueError('Selected config does not match pick model')
        if self._selection['inference_code_sha256'] != manifest['files']['opponent_pick.py']:
            raise ValueError('Selected config does not match inference code')
        if self._selection['config']['method'] != 'cosine' or self._selection['config']['weight'] != 0:
            raise ValueError('This release expects selected cosine configuration')
        if self._pick['dataset_version'] != self._ban['dataset_version']:
            raise ValueError('Model dataset mismatch')
        self.version = manifest['release_version']

    def heroes(self):
        """Return catalog for ID/name mapping; presence does not imply eligibility."""
        return [dict(hero_id=h,hero_name=name,
                     pick_candidate=h in self._pick['popularity'],
                     ban_candidate=h in self._ban['ban_counts'])
                for h,name in sorted(self._pick['hero_names'].items(),key=lambda p:(p[1],p[0]))]

    def recommend(self, request):
        if not isinstance(request,dict): raise ValueError('Request must be a JSON object')
        allowed={'action','own_picks','enemy_picks','banned','k'}
        if set(request)-allowed: raise ValueError('Unexpected fields: '+', '.join(sorted(set(request)-allowed)))
        action=request.get('action')
        if action not in ('pick','ban'): raise ValueError('action must be pick or ban')
        context={key:request.get(key,[]) for key in ('own_picks','enemy_picks','banned')}
        for key,value in context.items():
            if not isinstance(value,list): raise ValueError(key+' must be an array, not null')
        k=request.get('k',5)
        if action=='pick':
            config=self._selection['config']
            raw=opponent_pick.recommend_picks(self._pick,**context,k=k,
                  **{key:config[key] for key in ('method','weight','alpha')})
            rows=[]
            for r in raw['recommendations']:
                evidence=[dict(ally_hero_id=h,cosine=self._pick['cosine'].get(r['hero_id'],{}).get(h,0.0))
                          for h in sorted(context['own_picks'])]
                rows.append(dict(rank=r['rank'],hero_id=r['hero_id'],hero_name=r['hero_name'],
                                 score=r['score'],evidence=dict(train_lineup_count=r['popularity_count'],allies=evidence)))
            scope='P2_retrospective_4_allies_5_enemies_no_bans'
            score_type='mean_ally_cosine'
            fallback=raw['all_candidate_scores_zero']
        else:
            raw=ban_baseline.recommend_bans(self._ban,**context,k=k)
            rows=[dict(rank=r['rank'],hero_id=r['hero_id'],hero_name=r['hero_name'],score=r['score'],
                       evidence=dict(train_ban_count=r['ban_count'],train_games=self._ban['train_games']))
                  for r in raw['recommendations']]
            scope='B1_unordered_leave_one_ban_out_all_teams_no_picks'
            score_type='observed_train_ban_game_frequency'
            fallback=False
        return dict(schema_version='1.0',release_version=self.version,action=action,
                    model_version=raw['model_version'],method=raw['method'],score_type=score_type,
                    recommendations=rows,requested_k=k,returned_count=len(rows),
                    popularity_tiebreak_for_all_zero_scores=fallback,
                    evaluation=dict(split='validation',protocol_scope=scope,independent_v2_test=False),
                    capabilities=dict(opponent_used_for_filtering=True,opponent_used_for_scoring=False,
                                      draft_rule_validation=False,chronological_draft_evaluated=False),
                    limitations=['Scores are not win probabilities.',
                                 'Partial-context demo quality has not been measured.',
                                 'No role, patch, tournament-rule or global-ban validation.'])
