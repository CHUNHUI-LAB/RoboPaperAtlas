import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from atlas_taxonomy import atlas_projection
class AtlasTaxonomyTests(unittest.TestCase):
 def setUp(self):
  self.papers=json.loads((ROOT/'data/catalog.json').read_text())['papers'];self.overlay=json.loads((ROOT/'data/classification.json').read_text())
 def test_complete_unique_coverage_and_unchanged_bibliography(self):
  before=json.dumps(self.papers,sort_keys=True);data=atlas_projection(self.papers,self.overlay)
  self.assertEqual(set(data['placements']),{p['id'] for p in self.papers});self.assertEqual(len(data['placements']),95);self.assertEqual(before,json.dumps(self.papers,sort_keys=True))
 def test_incomplete_or_duplicate_overlay_fails_closed(self):
  for records in [self.overlay['records'][:-1],self.overlay['records']+[self.overlay['records'][0]]]:
   x=copy.deepcopy(self.overlay);x['records']=records
   with self.assertRaises(ValueError):atlas_projection(self.papers,x)
 def test_cross_domain_research_is_not_resource(self):
  p=atlas_projection(self.papers,self.overlay)['placements'];self.assertEqual(p['holoagent-0']['direction'],'cross-domain');self.assertEqual(p['savva2019habitat']['direction'],'resources')
  self.assertEqual(sum(x['direction']=='resources' for x in p.values()),7);self.assertEqual(sum(x['direction']=='cross-domain' for x in p.values()),1)
 def test_verified_abstracts_are_not_full_read_or_citation_verification(self):
  p=atlas_projection(self.papers,self.overlay)['placements'];self.assertEqual(sum(x['needsReview'] for x in p.values()),4)
  self.assertTrue(all(x['evidenceScope']!='catalog_title' for x in p.values()));self.assertTrue(all(x['sources'] for x in p.values()))
  self.assertEqual(sum(x['citation_verified'] for x in self.papers),22)
 def test_primary_problem_does_not_follow_old_method_bucket(self):
  p=atlas_projection(self.papers,self.overlay)['placements']
  for pid in ['rpa-0062','rpa-0070']:self.assertEqual(p[pid]['direction'],'mobile-manipulation')
  self.assertEqual(p['rpa-0043']['direction'],'policy-learning');self.assertEqual(p['rpa-0012']['direction'],'wbc');self.assertEqual(p['rpa-0008']['direction'],'general-ml')
 def test_unresolved_null_never_silently_becomes_resource(self):
  x=copy.deepcopy(self.overlay);r=next(p for p in x['records'] if p['primary_direction'] is None);r['placement_state']='unknown'
  with self.assertRaises(ValueError):atlas_projection(self.papers,x)
 def test_public_projection_drops_unapproved_nested_fields(self):
  x=copy.deepcopy(self.overlay);r=next(p for p in x['records'] if p['method_tags']);r['method_tags'][0]['private_note']='not public'
  self.assertNotIn('private_note',json.dumps(atlas_projection(self.papers,x)))
