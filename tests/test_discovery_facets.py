import json,re,sys,copy,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from discovery_facets import GROUPS,for_catalog,counts,project
class DiscoveryFacetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.papers=json.loads((ROOT/'data/catalog.json').read_text())['papers'];cls.records=json.loads((ROOT/'data/classification.json').read_text())['records'];cls.groups=for_catalog(cls.papers,cls.records)
 def test_every_record_has_evidenced_membership_without_mutation(self):
  original=copy.deepcopy(self.records);self.assertEqual(set(self.groups),{p['id']for p in self.papers});self.assertTrue(all(v['groups']and v['reasons']for v in self.groups.values()));self.assertEqual(self.records,original)
  self.assertEqual(counts(self.groups),{'navigation-space':29,'motion-manipulation':46,'robot-learning':50,'methods-resources':29});self.assertGreater(sum(counts(self.groups).values()),95)
 def test_foundations_are_not_automatically_robot_learning(self):
  for pid in ['rpa-0008','rpa-0018','rpa-0046','rpa-0058']:self.assertEqual(self.groups[pid]['groups'],['methods-resources'])
  self.assertIn('motion-manipulation',self.groups['rpa-0062']['groups']);self.assertIn('robot-learning',self.groups['rpa-0062']['groups']);self.assertIn('motion-manipulation',self.groups['rpa-0070']['groups'])
  self.assertIn('navigation-space',self.groups['holoagent-0']['groups']);self.assertIn('motion-manipulation',self.groups['holoagent-0']['groups'])
 def test_unmapped_or_mismatched_records_fail(self):
  r=copy.deepcopy(self.records);r[0]['primary_direction']='unreviewed'
  with self.assertRaises(ValueError):project(r)
  with self.assertRaises(ValueError):project([self.records[0],self.records[0]])
  with self.assertRaises(ValueError):for_catalog(self.papers,self.records[:-1])
 def test_global_and_library_share_exact_membership(self):
  from global_preview import read_preview
  from preview_discovery import hydrate_discovery
  page=hydrate_discovery(read_preview(ROOT)).decode();data=json.loads(re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>',page,re.S)[1])
  self.assertEqual(data['browseLabels'],{key:label for key,label,_ in GROUPS})
  for p in data['papers']:self.assertEqual(p['navigation']['groups'],self.groups[p['id']]['groups']);self.assertEqual(p['navigation']['reasons'],self.groups[p['id']]['reasons'])
