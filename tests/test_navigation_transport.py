import sys,unittest,json,hashlib,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import navigation_product as product
from navigation_transport import project,encode,inline_json,ARCHIVE_TABLES,restore_scope_coverage
class NavigationTransportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw,cls.model=product.payloads(ROOT);cls.projected=project(cls.model,product.MODEL_SHA256)
 def test_reconstruct_from_actual_serialized_files(self):
  p=self.projected;index=json.loads(p['inline']);d=index.pop('delivery');archive=json.loads(p['files'][d['archive']['sha256']+'.json']);index.update({k:v for k,v in archive.items() if k not in ('schemaVersion','sourceModelSha256')})
  # Independently decode the only scope redundancy; do not trust project.reconstructed.
  self.assertEqual(d['scopeCoverageEncoding'],'coverage-and-policy-by-scope-id-v1')
  self.assertEqual(set(d['scopeCoverageIds']),set(index['coverage']))
  for s in index['scopes']:
   if s['id'] in d['scopeCoverageIds']:
    self.assertNotIn('coverage',s);self.assertNotIn('coveragePolicy',s)
    s['coverage']=json.loads(json.dumps(index['coverage'][s['id']]))
    s['coveragePolicy']=json.loads(json.dumps(index['coverage'][s['id']]['coveragePolicy']))
  self.assertEqual(set(d['directoryCoverageIds']),{row['id'] for row in index['directory']})
  for row in index['directory']:
   self.assertNotIn('coverage',row)
   row['coverage']=json.loads(json.dumps(index['coverage'][row['id']]))
  for eid,spec in d['packets'].items():
   raw=p['files'][spec['sha256']+'.json'];self.assertEqual(len(raw),spec['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),spec['sha256']);packet=json.loads(raw);self.assertEqual(packet['sourceModelSha256'],product.MODEL_SHA256);self.assertEqual(packet['ownerId'],eid);index['entities'][eid]=packet['entities'][eid]
  self.assertEqual(index,self.model)
 def test_all_state_and_identity_topology_is_exact(self):
  for key in ('positions','scopes','directory','directoryGroups','forests','analyses','template','coverage','taskAliases','versionAliases','revision','statusGates'):
   self.assertEqual(restore_scope_coverage(self.projected['index'])[key],self.model[key],key)
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
  html=product.render(ROOT,self.model,self.projected);self.assertNotIn('<script src=',html);self.assertNotIn('rel="stylesheet"',html);self.assertIn('id="np-navigation-index"',html);self.assertIn('data-inline-start="1"',html);self.assertIn('data-index-sha="'+self.projected['indexSha256']+'"',html);self.assertIn('data-native-global-position=',html)

 def test_global_labels_reconstruct_exactly_from_serialized_source_references(self):
  from navigation_transport import restore_research_map
  p=self.projected;actual=json.loads(p['inline'])['delivery']['researchMap']
  self.assertEqual(restore_research_map(self.model,actual),p['researchMap'])
  self.assertEqual(len(actual['positions']),455)
  for position in actual['positions'].values():
   self.assertNotIn('label',position)
   self.assertIn(position['labelRef'],('entityId.label','labelSourcePaperId.title'))
 def test_global_title_references_reject_ambiguous_or_unknown_sources(self):
  from navigation_transport import restore_research_map
  import copy
  for mutation in ('unknown','duplicate'):
   value=copy.deepcopy(self.projected['index']['delivery']['researchMap']);node=next(iter(value['positions'].values()))
   if mutation=='unknown':node['labelRef']='privateSource.otherField'
   else:node['label']='conflicting title'
   with self.assertRaises(ValueError):restore_research_map(self.model,value)
 def test_scope_coverage_references_fail_closed_and_do_not_alias_objects(self):
  import copy
  original=self.projected['index'];restored=restore_scope_coverage(original)
  s=next(s for s in restored['scopes'] if s['id']=='task:goat')
  s['coverage']['methodCount']=-1;s['coveragePolicy']['note']='changed'
  self.assertNotEqual(restored['coverage']['task:goat']['methodCount'],-1)
  self.assertNotEqual(restored['coverage']['task:goat']['coveragePolicy']['note'],'changed')
  self.assertNotEqual(s['coverage']['coveragePolicy']['note'],'changed')
  directory=next(row for row in restored['directory'] if row['id']=='task:goat')
  directory['coverage']['methodCount']=-2
  self.assertNotEqual(restored['coverage']['task:goat']['methodCount'],-2)
  self.assertEqual(s['coverage']['methodCount'],-1)
  for mode in ('encoding','missing','paired-missing','duplicate','unknown','conflict','identity'):
   x=copy.deepcopy(original);d=x['delivery'];first=d['scopeCoverageIds'][0]
   if mode=='encoding':d['scopeCoverageEncoding']='unknown'
   elif mode=='missing':d['scopeCoverageIds'].pop()
   elif mode=='paired-missing':d['scopeCoverageIds'].remove(first);del x['coverage'][first]
   elif mode=='duplicate':d['scopeCoverageIds'].append(first)
   elif mode=='unknown':d['scopeCoverageIds'][0]='constructor'
   elif mode=='conflict':next(s for s in x['scopes'] if s['id']==first)['coverage']={}
   else:x['coverage'][first]['scopeId']='task:wrong'
   frozen=copy.deepcopy(x)
   with self.assertRaises(ValueError):restore_scope_coverage(x)
   self.assertEqual(x,frozen)
  for mode in ('missing','unknown','duplicate','conflict','removed-encoding'):
   x=copy.deepcopy(original);d=x['delivery'];first=d['directoryCoverageIds'][0]
   if mode=='missing':d['directoryCoverageIds'].pop()
   elif mode=='unknown':d['directoryCoverageIds'][0]='constructor'
   elif mode=='duplicate':d['directoryCoverageIds'].append(first)
   elif mode=='removed-encoding':del d['directoryCoverageIds']
   else:next(row for row in x['directory'] if row['id']==first)['coverage']={}
   frozen=copy.deepcopy(x)
   with self.assertRaises(ValueError):restore_scope_coverage(x)
   self.assertEqual(x,frozen)
