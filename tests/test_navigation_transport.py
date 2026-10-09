import sys,unittest,json,hashlib,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import navigation_product as product
from navigation_transport import project,encode,inline_json,ARCHIVE_TABLES
class NavigationTransportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw,cls.model=product.payloads(ROOT);cls.projected=project(cls.model,product.MODEL_SHA256)
 def test_reconstruct_from_actual_serialized_files(self):
  p=self.projected;index=json.loads(p['inline']);d=index.pop('delivery');archive=json.loads(p['files'][d['archive']['sha256']+'.json']);index.update({k:v for k,v in archive.items() if k not in ('schemaVersion','sourceModelSha256')})
  for eid,spec in d['packets'].items():
   raw=p['files'][spec['sha256']+'.json'];self.assertEqual(len(raw),spec['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),spec['sha256']);packet=json.loads(raw);self.assertEqual(packet['sourceModelSha256'],product.MODEL_SHA256);self.assertEqual(packet['ownerId'],eid);index['entities'][eid]=packet['entities'][eid]
  self.assertEqual(index,self.model)
 def test_all_state_and_identity_topology_is_exact(self):
  for key in ('positions','scopes','directory','directoryGroups','forests','analyses','template','coverage','taskAliases','versionAliases','revision','statusGates'):
   self.assertEqual(self.projected['index'][key],self.model[key],key)
 def test_deterministic_bytes(self):
  again=project(self.model,product.MODEL_SHA256);self.assertEqual(again['inline'],self.projected['inline']);self.assertEqual(again['files'],self.projected['files'])
 def test_small_initial_index_and_packet_budget(self):
  p=self.projected;self.assertLess(len(p['inline']),4_000_000);self.assertLess(len(gzip.compress(p['inline'])),550_000)
  sizes=[v['bytes'] for v in p['index']['delivery']['packets'].values()];self.assertLess(max(sizes),350_000);self.assertLess(sum(sizes)/len(sizes),20_000)
 def test_current_science_is_not_replaced(self):
  self.assertEqual(hashlib.sha256(self.raw).hexdigest(),product.MODEL_SHA256);self.assertEqual(self.projected['reconstructed'],self.model)
 def test_all_claim_and_design_dependencies_are_pinned(self):
  p=self.projected
  for eid,spec in p['index']['delivery']['packets'].items():
   packet=json.loads(p['files'][spec['sha256']+'.json']);self.assertEqual(sorted(packet['entities']),spec['entityIds']);self.assertEqual(sorted(packet['claims']),spec['claimIds'])
   for e in packet['entities'].values():self.assertTrue(set(e.get('claimIds',[]))<=packet['claims'].keys())
 def test_embedded_json_escapes_script_boundaries(self):
  text=inline_json({'example':'</script><img src=x>\u2028\u2029'});self.assertNotIn('<',text);self.assertNotIn('\u2028',text);self.assertEqual(json.loads(text)['example'],'</script><img src=x>\u2028\u2029')
 def test_real_html_has_no_external_boot_dependency(self):
  html=product.render(ROOT,self.model,self.projected);self.assertNotIn('<script src=',html);self.assertNotIn('rel="stylesheet"',html);self.assertIn('id="np-navigation-index"',html);self.assertIn('data-inline-start="1"',html);self.assertIn('data-index-sha="'+self.projected['indexSha256']+'"',html);self.assertIn('data-native-position=',html)
