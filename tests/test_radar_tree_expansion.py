"""Public evidence expansion contract; no reading-stage or history promotion."""
import collections
from html.parser import HTMLParser
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'previews/radar-trees-c/data'
BASE_RECORD_HASHES={'harnessvln': '122208f61b32da300eab284780f9fa05ec76698c9e6bf1028bfcd72224a1a4bc', 'navharness': 'd6c0ee87f89b0ad1388b475b388ba688aa5ea5f0c2cc60a5488394b5779bc8ca', 'agenticnav-tool-harness': '3579c9152f4f69b30575133ed279977718a2255291686462e5b8cabc56de1c6c', 'qwen-robotnav': '9fd174d45bcb19f8492d1e188eafd8152ce748a21642c6722cc47b6a25ee63de', 'holoagent-0': '04405d3ecb4050ba82aaf54dd97aa807f049bc9a73ae5da88a0f2090449410e9', 'krantz2023ivln': '3c14933083268f2abb99bc9c5e696e760c927d428860857c2e161367d3f66f96', 'goat': '352b7cdd2a76fc641863cce296aae73dd7a424782089639bec304753b655d355', 'goat-bench': '7016b46b5e2f7e4689a6bc199bb17158179ff1fd211f34585e4c1398ed2fc40d', 'krantz2020vlnce': 'b925a52815914e37f1b3461911963bf0417486a213fe2930fc1dabc13bd5143f', 'batra2020objectnav': 'd52dcb8b946ec724c85c51ece5f1d8f18d43748f8e5819d3014940c15314d0f5'}
PROTECTED_HASHES={'daily': 'e83e034fa14c5306a6ea76e2a5af8e92d9edb7a88264be768d96cd5909dd55dc', 'weekly': '82c4d6a056d065616b31ed6bf1f92e10280a3f466496019f1f76e1b3046c9866', 'candidates': 'd749935ed8e43a57002d8db637d1cf2a63115eb374f6aeed010bfafc3e171ffb', 'academic_edges': '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', 'routes': 'b126883fcd7181791981c56bf4c561b27d05ef756181e9a5714964dc866a9438'}
def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class RadarTreeExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((DATA/'graph-data.json').read_text())
        cls.papers=cls.data['papers']
    def test_public_backward_compatible_schema(self):
        self.assertEqual(self.data['schema'],'radar-c-view/1')
        self.assertIs(self.data['public_only'],True)
    def test_frozen_windows_candidates_and_edges_preserved(self):
        for key,expected in PROTECTED_HASHES.items():
            self.assertEqual(digest(self.data[key]),expected,key)
    def test_original_record_fields_remain_unchanged(self):
        records={p['canonical_id']:p for p in self.papers}
        for ident,expected in BASE_RECORD_HASHES.items():
            self.assertIn(ident,records)
            original={k:v for k,v in records[ident].items() if k not in {'identity','harness_relation','overview_zh','overview_label_zh','overview_attribution','overview_scope_note_zh'}}
            self.assertEqual(digest(original),expected,ident)
    def test_json_and_browser_payload_equivalent(self):
        source=(DATA/'graph-data.js').read_text()
        prefix='window.RADAR_GRAPH_DATA = '
        self.assertTrue(source.startswith(prefix))
        self.assertEqual(json.loads(source[len(prefix):].strip().removesuffix(';')),self.data)
    def test_unique_identity_per_evidence_scope(self):
        for rows in [self.papers,self.data['candidates']]:
            ids=[p['canonical_id'] for p in rows]
            self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(len({p['paper_id'] for p in self.papers}),len(self.papers))
        for kind in ['arxiv_ids','normalized_title']:
            aliases=[]
            for p in self.papers:
                value=p['identity'][kind]
                aliases.extend(value if isinstance(value,list) else [value])
            self.assertEqual(len(aliases),len(set(aliases)),kind)
    def test_cross_scope_identity_never_confuses_same_named_papers(self):
        baseline={p['canonical_id']:p for p in self.papers}
        for p in self.data['candidates']:
            if p['canonical_id'] in baseline:
                self.assertEqual(p['title'],baseline[p['canonical_id']]['title'])
        names=[p for p in self.papers if 'NavHarness:' in p['title']]
        self.assertEqual(len(names),len({p['source_url'] for p in names}))
    def test_counts_derive_from_records_and_keep_scope(self):
        c=self.data['coverage']; papers=self.papers; weekly=self.data['candidates']
        self.assertEqual(c['baseline_unique_papers'],len({p['canonical_id'] for p in papers}))
        self.assertEqual(c['weekly_unique_papers'],len({p['canonical_id'] for p in weekly}))
        self.assertEqual(c['all_scopes_unique_papers'],len({p['canonical_id'] for p in papers+weekly}))
        self.assertEqual(c['targeted_body_papers'],sum(p['read_scope']=='section' for p in papers))
        self.assertEqual(self.data['pool_counts']['targeted_body_core'],c['targeted_body_papers'])
        self.assertEqual(c['classification_counts'],dict(collections.Counter(p['harness_relation']['kind'] for p in papers)))
        self.assertEqual(c['academic_edges'],len(self.data['academic_edges']))
    def test_historical_pool_is_not_a_current_denominator(self):
        pool=self.data['pool_counts'];h=self.data['coverage']['historical_candidate_pool']
        self.assertEqual(pool['candidate_pool_scope'],'historical_unrecovered_claim_not_current_count')
        self.assertIs(pool['candidate_pool_recovered'],False)
        self.assertEqual(h['claimed_count'],pool['candidate_pool'])
        self.assertEqual(h['recovery_status'],'not_fully_recovered')
        self.assertIs(h['not_current_corpus_count'],True)
    def test_every_placement_has_resolvable_endpoints(self):
        tasks={p['id'] for p in self.data['tasks']};routes={p['id'] for p in self.data['routes']};groups={p['id']:p for p in self.data['groups']}
        links={(e['source'],e['target']) for e in self.data['task_routes']}
        self.assertEqual(len(links),len(self.data['task_routes']))
        for p in self.papers:
            self.assertTrue(p['tasks'] and p['routes'] and p['groups'])
            self.assertLessEqual(set(p['tasks']),tasks);self.assertLessEqual(set(p['routes']),routes);self.assertLessEqual(set(p['groups']),set(groups))
            for t in p['tasks']:
                for r in p['routes']:self.assertIn((t,r),links)
            for g in p['groups']:self.assertIn(p['paper_id'],groups[g]['paper_ids'])
        for e in self.data['task_routes']:self.assertEqual(e['attribution'],'curator_organization')
    def test_direct_harness_support_and_protocol_are_explicit(self):
        for p in self.papers:
            h=p['harness_relation']
            self.assertIn(h['kind'],{'direct_harness','supporting_method','benchmark_protocol','unclassified_candidate'})
            self.assertEqual(h['attribution'],'curator_organization')
            self.assertTrue(h['basis'])
            self.assertTrue(h['not_claimed'])
    def test_additions_have_pinned_scoped_evidence_not_stage_completion(self):
        ids=set(self.data['expansion_provenance']['added_canonical_ids'])
        self.assertTrue(ids)
        self.assertFalse(ids.intersection(BASE_RECORD_HASHES))
        for p in self.papers:
            if p['canonical_id'] not in ids:continue
            self.assertIn(p['read_scope'],{'section','abstract','metadata'})
            self.assertTrue(p['version'] and p['read_locations'] and p['not_read'])
            self.assertTrue(p['evidence'])
            s=p['source_provenance']
            for flag in ['full_paper_read','code_read','experiments_independently_verified','stage_changed']:
                self.assertIs(s[flag],False,(p['paper_id'],flag))
            self.assertTrue(s['read_version'] and s['read_locations'])
            u=urlsplit(p['source_url']);self.assertEqual(u.scheme,'https');self.assertIsNone(u.username);self.assertIsNone(u.password)
            if u.hostname=='arxiv.org':self.assertRegex(u.path,r'/\d{4}\.\d{4,5}v\d+(?:\.pdf)?$')
            for e in p['evidence']:
                self.assertIn(e['attribution'],{'author_claim','direct_observation','curator_summary'})
                self.assertTrue(e['locator'] and e['statement'])
            self.assertNotIn('stages',p)
    def test_graph_all_scopes_and_tasks_are_fully_reachable(self):
        code="""
const fs=require('fs'),assert=require('node:assert/strict'),G=require('./previews/radar-trees-c/graph.js');
const d=JSON.parse(fs.readFileSync('./previews/radar-trees-c/data/graph-data.json'));
for(const mode of ['baseline','weekly'])for(const task of ['all',...d.tasks.map(t=>t.id)]){
 const state=G.initialState();state.mode=mode;state.task=task;
 d.routes.forEach(r=>state.expandedRoutes.add(r.id));d.groups.forEach(g=>state.expandedGroups.add(g.id));
 G.activePapers(d,state).forEach(p=>state.expandedChallenges.add(p.canonical_id));
 const scene=G.buildScene(d,state),expected=G.filteredPapers(d,state),nodes=new Map(scene.nodes.map(n=>[n.id,n]));
 const ids=scene.nodes.filter(n=>n.kind==='paper').map(n=>n.canonical);
 assert.equal(new Set(ids).size,ids.length);assert.equal(scene.uniqueVisible,new Set(expected.map(p=>p.canonical_id)).size);
 assert.equal(nodes.size,scene.nodes.length);
 for(const edge of scene.edges){assert(nodes.has(edge.source));assert(nodes.has(edge.target));assert.equal(edge.attribution,'curator_organization');if(edge.cross)assert.equal(nodes.get(edge.source).canonical,nodes.get(edge.target).canonical);}
}
"""
        subprocess.run(['node','-e',code],cwd=ROOT,check=True,capture_output=True,text=True,timeout=30)
    def test_each_baseline_has_an_honestly_labeled_chinese_overview(self):
        for p in self.papers:
            self.assertTrue(p.get('overview_zh') or p.get('abstract_summary_zh'))
            if p.get('overview_zh'):
                self.assertEqual(p['overview_attribution'],'curator_summary_of_reviewed_sections')
                self.assertIn('不是完整摘要',p['overview_scope_note_zh'])
            else:self.assertEqual(p['abstract_summary_attribution'],'curator_summary_of_complete_abstract')
    def test_text_alternatives_cover_all_current_canonical_records(self):
        class Reader(HTMLParser):
            def __init__(self):super().__init__();self.ids=[];self.papers=[];self.counts=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if 'id' in a:self.ids.append(a['id'])
                if 'data-paper-id' in a:self.papers.append(a['data-paper-id'])
                if 'data-baseline-count' in a:self.counts.append(int(a['data-baseline-count']))
        expected={p['canonical_id'] for p in self.papers}
        for name in ['literature.html','challenge.html','reading-overview.html']:
            parser=Reader();parser.feed((DATA.parent/name).read_text())
            self.assertEqual(set(parser.papers),expected,name)
            self.assertEqual(len(parser.ids),len(set(parser.ids)),name)
            self.assertEqual(parser.counts,[len(expected)],name)
            if name!='literature.html':self.assertEqual(len(parser.papers),len(expected),name)
        index=(DATA.parent/'index.html').read_text()
        self.assertNotIn('基线 10 篇',index)
        self.assertIn('当前文字替代',index)
        subprocess.run(['python3','scripts/render_radar_tree_text.py','--check'],cwd=ROOT,check=True,capture_output=True,text=True,timeout=30)
    def test_text_renderer_rejects_unsafe_urls_before_generating_links(self):
        spec=importlib.util.spec_from_file_location('radar_text_renderer',ROOT/'scripts/render_radar_tree_text.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for url in ['javascript:alert(1)','data:text/html,bad','http://example.com','https://user:pass@example.com','https://example.com/\n','https://localhost/x','https://127.0.0.1/x','https://[::1]/x','//example.com/a','../outside.html','/absolute.html','https://example.com:8443/x']:
            with self.assertRaises(ValueError,msg=url):module.link(url,'source')
        self.assertIn('https://arxiv.org/html/2607.29600v1',module.link('https://arxiv.org/html/2607.29600v1','source'))
        self.assertIn('challenge.html#paper-arxiv:2609.39915',module.link('challenge.html#paper-arxiv:2609.39915','paper'))
    def test_held_and_proposed_relations_are_not_promoted(self):
        self.assertNotIn('pan2025sali',{p['canonical_id'] for p in self.papers})
        self.assertFalse(self.data['expansion_provenance']['relation_proposals_integrated'])
        self.assertFalse(self.data['expansion_provenance']['stage_changes'])
        self.assertFalse(self.data['expansion_provenance']['weekly_daily_snapshots_changed'])
        self.assertEqual(self.data['coverage']['full_papers_read'],0)
        self.assertEqual(self.data['coverage']['independent_reproductions'],0)
if __name__=='__main__':unittest.main()
