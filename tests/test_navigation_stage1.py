"""Exact navigation readers, lawful source choices, and isolated preview boundary."""
import copy,json,re,sys,tempfile,unittest,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
import navigation_stage1_preview as preview
from report_navigation_stage1 import IDS,FROZEN
from current_reader import render,entry_path

class NavigationStage1Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.sources={rec['paper_id']:(rec,raw)for rec,raw in preview.load_sources(ROOT)}
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);(self.root/'data').mkdir()
  for pid in IDS:shutil.copyfile(ROOT/f'data/report-{pid}-stage1-v1-policy.json',self.root/f'data/report-{pid}-stage1-v1-policy.json')
 def admit(self,pid,payload,**updates):
  path=self.root/f'data/report-{pid}-stage1-v1-policy.json';policy=json.loads(path.read_text());policy.update(document_sha256=r.sha(payload),**updates);path.write_text(json.dumps(policy))
  return r.split_report(self.root,self.sources[pid][0],payload)
 def test_exact_three_source_versions_pending_not_approved(self):
  self.assertEqual(tuple(self.sources),IDS)
  for pid,(rec,raw)in self.sources.items():
   parsed=r._parse_html(rec,raw,ROOT)
   self.assertEqual(rec['review_status'],'preview_pending');self.assertEqual((parsed.summary_count,len(parsed.section_ids)),(5,12))
   self.assertIn('待视觉验收',raw.decode());self.assertNotIn('未发布',raw.decode())
   self.assertEqual(parsed.image_count,{'harnessvln':6,'navharness':4,'holoagent-0':0}[pid])
   self.assertEqual(entry_path(pid,'stage1'),f'papers/{pid}/reading/stage1.html');self.assertIsNone(entry_path(pid,'stage2'));self.assertIsNone(entry_path(pid,'stage3'))
 def test_fixed_source_and_identity_reject_changes(self):
  for pid,(rec,raw)in self.sources.items():
   for update in [dict(stage='stage2',filename='writing-close-reading.html'),dict(version='v2'),dict(review_status='approved'),dict(review_status='content_approved'),dict(source_sha256='0'*64),dict(source_url='https://arxiv.org/abs/2609.39915v1'),dict(pdf_url='https://arxiv.org/pdf/2609.39915v1')]:
    with self.subTest(pid=pid,update=update),self.assertRaises(ValueError):r.split_report(self.root,dict(rec,**update),raw)
 def test_canonical_registry_rejects_preview_even_with_valid_formal_chunks(self):
  for pid,(rec,raw)in self.sources.items():
   # Exact valid sources and chunks must not turn a pending preview into a
   # canonical report through either public registry entry point.
   prepared=r.split_report(self.root,rec,raw)
   (self.root/'data/reports.json').write_text(json.dumps({'schema_version':1,'reports':[prepared]}))
   for loader in (r.load_reports,r.assemble_reports):
    with self.subTest(pid=pid,loader=loader.__name__),self.assertRaisesRegex(ValueError,'cannot enter the canonical report registry'):
     loader(self.root)
   self.assertFalse((self.root/r.report_path(prepared)).exists())
 def test_full_document_source_equations_images_sections_are_pinned(self):
  for pid,(rec,raw)in self.sources.items():
   changed=raw.replace(b'</body>',b'<p>changed</p></body>')
   with self.assertRaises(ValueError):r.split_report(self.root,rec,changed)
   changed=raw.replace(b'id="section-01"',b'id="section-99"',1)
   with self.assertRaisesRegex(ValueError,'sections'):self.admit(pid,changed)
   for exact in re.findall(rb'<math\b.*?</math>',raw,re.S):
    changed=raw.replace(exact,exact.replace(b'<mo>=</mo>',b'<mo>+</mo>',1),1)
    with self.assertRaisesRegex(ValueError,'MathML'):self.admit(pid,changed)
 def test_only_exact_previously_reviewed_script_allowed(self):
  for pid,(rec,raw)in self.sources.items():
   self.assertEqual(FROZEN[pid]['script_sha256'],'d6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798')
   changed=raw.replace(b'updatePosition();',b'alert(1);',1);script=re.search(rb'<script>(.*?)</script>',changed,re.S)[1]
   with self.assertRaisesRegex(ValueError,'script'):self.admit(pid,changed,script_sha256=r.sha(script))
 def test_active_content_rejected_even_after_document_repin(self):
  attacks=[b'<script>alert(1)</script>',b'<script src="https://example.com/a"></script>',b'<p onclick="alert(1)">x</p>',b'<img src="https://example.com/a.png">',b'<iframe src="https://example.com"></iframe>',b'<svg></svg>',b'<object data="https://example.com"></object>',b'<form></form>',b'<input type="text">',b'<a href="file:///tmp/x">x</a>',b'<a href="javascript:alert(1)">x</a>',b'<a href="https://127.0.0.1">x</a>',b'<meta http-equiv="refresh" content="0;url=https://example.com">',b'<blockquote>unreviewed</blockquote>']
  for pid,(rec,raw)in self.sources.items():
   for attack in attacks:
    with self.subTest(pid=pid,attack=attack),self.assertRaises(ValueError):self.admit(pid,raw.replace(b'</body>',attack+b'</body>'))
 def test_resource_css_stays_rejected_after_independent_rehash(self):
  for pid,(rec,raw)in self.sources.items():
   for css in [b'@import "https://example.com/a";',b'p{background:url(https://example.com/a)}',b'p{width:expression(alert(1))}']:
    changed=raw.replace(b'<style>',b'<style>'+css,1);style=re.search(rb'<style>(.*?)</style>',changed,re.S)[1]
    with self.assertRaisesRegex(ValueError,'CSS'):self.admit(pid,changed,style_sha256=r.sha(style))
 def test_holo_no_figure_reproduction_or_permission_claim(self):
  raw=self.sources['holoagent-0'][1];text=raw.decode()
  self.assertNotRegex(text,r'<(?:img|svg|iframe)\b|\bon(?:click|keydown)=')
  self.assertEqual(len(FROZEN['holoagent-0']['evidence_ids']),8)
  self.assertIn('并未取得或声称取得作者转载授权',text)
  self.assertNotIn('嵌入全部论文原图',text)
 def test_cc_by_attribution_and_no_private_inputs(self):
  for pid,(rec,raw)in self.sources.items():
   text=raw.decode()
   if pid!='holoagent-0':self.assertIn('href="https://creativecommons.org/licenses/by/4.0/"',text)
   for banned in ['libfile_','/workspace/','skill://','data:application/pdf','localhost','127.0.0.1']:self.assertNotIn(banned,text)
 def test_preview_seven_exact_files_and_no_catalog_mutation(self):
  before=(ROOT/'data/catalog.json').read_bytes();reports=(ROOT/'data/reports.json').read_bytes();outputs=preview.output_payloads(ROOT)
  self.assertEqual(len(outputs),7);self.assertEqual(before,(ROOT/'data/catalog.json').read_bytes());self.assertEqual(reports,(ROOT/'data/reports.json').read_bytes())
  self.assertTrue(all(p.startswith(preview.BASE+'/')for p in outputs))
  target=self.root/'out';target.mkdir();preview.write_preview(ROOT,target)
  self.assertEqual(preview.validate_preview(ROOT,target),set(outputs))
  for pid in IDS:
   view=outputs[f'{preview.BASE}/{pid}/stage1.html'].decode()
   self.assertIn('href="first-pass.html"',view);self.assertIn('待视觉验收',view);self.assertIn('f2-current-reader',view)
   self.assertIn(f'https://chunhui-lab.github.io/RoboPaperAtlas/papers/{pid}/index.html#reading',view)
   self.assertNotIn('href="stage2.html"',view);self.assertNotIn('href="stage3.html"',view)
  altered=target/f'{preview.BASE}/harnessvln/stage1.html';altered.write_text(altered.read_text().replace('</body>','<p>tampered</p></body>'))
  with self.assertRaises(ValueError):preview.validate_preview(ROOT,target)
 def test_preview_manifest_invalid_identity_parts_and_states(self):
  from unittest.mock import patch
  obj=json.loads((ROOT/preview.MANIFEST).read_text());original=r._read
  for mode in ('approval','path','part-order','part-hash','part-size','missing-part','unknown-paper','nonobject'):
   changed=copy.deepcopy(obj);rec=changed['reports'][0]
   if mode=='approval':rec['review_status']='content_approved'
   elif mode=='path':rec['parts'][0]['file']='../../escape.html'
   elif mode=='part-order':rec['parts'].reverse()
   elif mode=='part-hash':rec['parts'][0]['sha256']='0'*64
   elif mode=='part-size':rec['parts'][0]['bytes']=True
   elif mode=='missing-part':rec['parts'].pop()
   elif mode=='unknown-paper':rec['paper_id']='rpa-0062'
   else:changed['reports'][0]='bad'
   def read(root,path,limit):return json.dumps(changed).encode()if path==preview.MANIFEST else original(root,path,limit)
   with self.subTest(mode=mode),patch.object(r,'_read',side_effect=read),self.assertRaises(ValueError):preview.load_sources(ROOT)
 def test_in_memory_reader_route_is_not_general_override(self):
  record,raw=self.sources['harnessvln'];paper={'id':'harnessvln','stages':{'stage1':{'status':'imported','artifacts':[{'path':r.report_path(record)}]},'stage2':{'status':'not_imported','artifacts':[]},'stage3':{'status':'not_imported','artifacts':[]}}}
  with self.assertRaises(ValueError):render(ROOT,paper,'stage1',[record],preview_payload=raw+b'<script>x</script>')
  wrong=dict(record,sha256=r.sha(raw+b'changed'),bytes=len(raw)+7)
  with self.assertRaises(ValueError):render(ROOT,paper,'stage1',[wrong],preview_payload=raw+b'changed')
if __name__=='__main__':unittest.main()
