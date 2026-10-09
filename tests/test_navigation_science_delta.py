"""Exact current science changes, separately from immutable historical fixtures."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE='1229372f697316dc5c0627995fce7de18496160d85f4a1acb4ffc2a6faf1d708'
CURRENT='9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c'

def apply_exact(model,operations):
    result=copy.deepcopy(model)
    for op in operations:
        parts=[p.replace('~1','/').replace('~0','~') for p in op['path'].strip('/').split('/')]
        obj=result
        for part in parts[:-1]:obj=obj[int(part)] if isinstance(obj,list) else obj[part]
        key=int(parts[-1]) if isinstance(obj,list) else parts[-1]
        if op['op']=='add':
            if isinstance(obj,list):
                if key!=len(obj):raise ValueError('Only explicit append is admitted')
                obj.append(copy.deepcopy(op['value']))
            else:
                if key in obj:raise ValueError('Unexpected existing key')
                obj[key]=copy.deepcopy(op['value'])
        elif op['op']=='replace':
            if obj[key]!=op['old']:raise ValueError('Reviewed before-value mismatch')
            obj[key]=copy.deepcopy(op['value'])
        else:raise ValueError('Deletion is not authorized by this additive correction')
    return result

class NavigationScienceDeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_raw=gzip.decompress((ROOT/'tests/fixtures/navigation-product-pr52-1229.json.gz').read_bytes())
        cls.raw=gzip.decompress((ROOT/'data/navigation-product/model.json.gz').read_bytes())
        cls.base=json.loads(cls.base_raw);cls.current=json.loads(cls.raw)
        cls.delta=json.loads((ROOT/'tests/fixtures/navigation-science-delta-20261009.json').read_text())
    def test_exact_grouped_leaf_changes_reconstruct_entire_current_model(self):
        self.assertEqual(hashlib.sha256(self.base_raw).hexdigest(),BASE)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),CURRENT)
        self.assertEqual(self.delta['baseSha256'],BASE)
        model=self.base
        for group in self.delta['groups']:
            model=apply_exact(model,group['operations'])
            canonical=json.dumps(model,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
            self.assertEqual(hashlib.sha256(canonical).hexdigest(),group['expectedSemanticSha256'],group['name'])
        self.assertEqual(model,self.current)
        self.assertEqual(len(self.delta['groups'][1]['operations']),7)
    def test_wrong_before_value_and_unlisted_legacy_change_are_not_accepted(self):
        group=self.delta['groups'][1]
        before=apply_exact(self.base,self.delta['groups'][0]['operations'])
        ops=copy.deepcopy(group['operations']);ops[0]['old']='unreviewed prior value'
        with self.assertRaises(ValueError):apply_exact(before,ops)
        expected=self.base
        for g in self.delta['groups']:expected=apply_exact(expected,g['operations'])
        altered=copy.deepcopy(self.current);altered['claims']['recipe:pipeline-poni']['statement']='unreviewed rewrite'
        self.assertNotEqual(expected,altered)
    def test_old_identity_and_analysis_history_remain_intact(self):
        for table in ('analyses','template','versionAliases','statusGates','sources'):
            self.assertEqual(self.current[table],self.base[table],table)
        self.assertEqual(self.current['summary']['answeredAnalysisContexts'],3)
        for pid,old in self.base['positions'].items():
            for field in ('entityId','tree','scopeId','paperId','versionId','parentId','association','claimIds'):
                self.assertEqual(self.current['positions'][pid].get(field),old.get(field),(pid,field))
        self.assertEqual(self.current['entities']['methods:paper:navharness'],self.base['entities']['methods:paper:navharness'])
        self.assertEqual(self.current['entities']['methods:pipeline-navmcp'],self.base['entities']['methods:pipeline-navmcp'])
    def test_hieranav_is_two_scoped_methods_and_only_sap_specific_ci(self):
        m=self.current;coverage=m['coverage']['task:hieranav']
        self.assertEqual(coverage['direct']['methodNodeIds'],['pipeline-planavid'])
        self.assertEqual(coverage['condition']['methodNodeIds'],['pipeline-sapnav'])
        self.assertEqual(coverage['condition']['paperIds'],['sap-nav'])
        rows=[p for p in m['positions'].values() if p['scopeId']=='task:hieranav' and p['association']=='condition']
        self.assertTrue(rows)
        for p in rows:
            if p['paperId']:self.assertEqual((p['paperId'],p['versionId']),('sap-nav','arxiv:2608.12707v1'))
            self.assertIn('单目标',p['condition'])
        self.assertEqual(m['entities']['methods:pipeline-sapnav']['detail']['pipeline']['feedback'],'被AVV拒绝的候选加入黑名单并继续探索；视点核验次数有限')
    def test_navharness_scopes_do_not_import_the_other_protocol_or_extension(self):
        m=self.current
        for sid,other in [('task:goat','ir2r-tour'),('task:ivln','goat-run')]:
            rows=[p for p in m['positions'].values() if p['scopeId']==sid and p.get('paperId')=='navharness' and p.get('versionId')=='arxiv:2609.34276v1']
            self.assertTrue(rows)
            for p in rows:
                claims=set(p['claimIds'])|set(m['entities'][p['entityId']]['claimIds'])
                self.assertFalse(any(c.endswith(':'+other) or c.endswith(':extended-tours') for c in claims),p['id'])
            self.assertEqual(m['coverage'][sid]['condition']['analysisPaperIds'],['navharness'])
        refs={'goat-run':['task:goat'],'ir2r-tour':['task:ivln'],'extended-tours':[]}
        for suffix,expected in refs.items():self.assertEqual(m['entities']['evidence:method-claim:navharness:v1:'+suffix]['taskRefs'],expected)
    def test_navmcp_new_route_is_fixed_v1_without_snapshot_ci_or_benchmark_claims(self):
        m=self.current
        rows=[p for p in m['positions'].values() if p['scopeId']=='task:active-eqa' and p.get('paperId')=='navmcp']
        self.assertEqual(len(rows),2)
        for p in rows:
            self.assertEqual((p['tree'],p['versionId']),('l','arxiv:2608.30396v1'))
            e=m['entities'][p['entityId']]
            self.assertEqual(e['detail']['sourceVersionId'],'primary:navmcp')
            self.assertTrue(all(r['versionId']=='arxiv:2608.30396v1' and r['url'].endswith('v1') for r in e['sourceRefs']))
        self.assertFalse(any(r['relationType']=='evaluated_on' and r['from']=='methods:pipeline-navmcp-fixed-v1' for r in m['relations'].values()))
