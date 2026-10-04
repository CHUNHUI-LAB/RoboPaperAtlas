import copy,json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from global_preview import read_preview
from preview_discovery import hydrate_discovery
from preview_reading import hydrate_reading_stages
class PreviewDiscoveryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.payload=hydrate_reading_stages(read_preview(ROOT),ROOT,'atlas-data')
 def parse(self,payload):return json.loads(re.search(rb'<script id="atlas-data" type="application/json">(.*?)</script>',payload,re.S)[1])
 def wrap(self,data):return b'<script id="atlas-data" type="application/json">'+json.dumps(data).encode()+b'</script>'
 def test_only_two_reviewed_method_projections_change(self):
  old=self.parse(self.payload);new=self.parse(hydrate_discovery(self.payload))
  self.assertEqual(len(new['papers']),95);self.assertEqual(new['relations'],old['relations'])
  changed=[]
  for a,b in zip(old['papers'],new['papers']):
   if a==b:continue
   changed.append(a['id']);self.assertEqual(b['stages'],a['stages'])
   self.assertEqual(b['navigation']['primary'],a['navigation']['primary'])
   self.assertEqual(set(k for k in b if a[k]!=b[k]),{'methods','classification','searchAliases','navigation'})
   ac=copy.deepcopy(a);bc=copy.deepcopy(b)
   for p in [ac,bc]:
    for key in ['methods','searchAliases']:p.pop(key)
    p['classification'].pop('methodTags')
    for key in ['groups','labels','reasons']:p['navigation'].pop(key)
   self.assertEqual(ac,bc)
  self.assertEqual(changed,['rpa-0050','rpa-0052'])
  stages=[s for p in new['papers'] for s in p['stages']]
  self.assertEqual(sum(any(s['status']=='imported' for s in p['stages']) for p in new['papers']),5)
  self.assertEqual(sum(s['status']=='imported' for s in stages),12)
  self.assertEqual(sum(len(s['links']) for s in stages),21)
 def test_non_json_bytes_and_idempotence(self):
  result=hydrate_discovery(self.payload)
  mask=lambda x:re.sub(rb'(<script id="atlas-data" type="application/json">).*?(</script>)',rb'\1\2',x,flags=re.S)
  self.assertEqual(mask(result),mask(self.payload));self.assertEqual(hydrate_discovery(result),result)
 def test_missing_duplicate_unknown_ids_and_primary_changes_fail_closed(self):
  for mutate in [lambda d:d['papers'].pop(),lambda d:d['papers'].append(d['papers'][0]),lambda d:d['papers'][0].update(id='unknown'),lambda d:d['papers'][0]['classification'].update(direction='wrong')]:
   data=self.parse(self.payload);mutate(data)
   with self.assertRaises(ValueError):hydrate_discovery(self.wrap(data))
 def test_missing_data_block_or_duplicate_json_key_rejected(self):
  for payload in [b'<html></html>',self.payload+self.payload,self.payload.replace(b'"papers":',b'"papers":[],"papers":',1)]:
   with self.assertRaises(ValueError):hydrate_discovery(payload)
