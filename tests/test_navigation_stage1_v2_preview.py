"""Strict, non-approval v2 preview boundary and immutable report reuse."""
import copy,json,hashlib,re,shutil,sys,tempfile,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
import navigation_stage1_preview as v1
import navigation_stage1_v2_preview as v2
import current_reader as reader
from report_navigation_stage1 import prepare_candidate_v2

class V2PreviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.sources=v2.load_sources(ROOT);cls.original=r.load_reports(ROOT)
  cls.protected={p:(ROOT/p).read_bytes()for p in ('data/reports.json','data/catalog.json','data/classification.json','submit-preview/data/venues.json','submit-preview/app.js')}
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='v2-preview-');self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  for record,raw in self.sources:
   pid=record['paper_id'];d=self.root/r._parts_path(record);d.mkdir(parents=True)
   for part in record['parts']:shutil.copyfile(ROOT/r._parts_path(record)/part['file'],d/part['file'])
   p=f'data/report-{pid}-stage1-v2-policy.json';shutil.copyfile(ROOT/p,self.root/p)
  (self.root/'candidates').mkdir();shutil.copyfile(ROOT/v2.MANIFEST,self.root/v2.MANIFEST)
 def test_packaged_toc_focus_controls(self):
  subprocess.run(['node',str(ROOT/'tests/test_reader_toc_focus_v1.cjs')],check=True,cwd=ROOT,capture_output=True,text=True)
 def test_exact_seven_outputs_and_fixed_raw_bytes(self):
  output=v2.output_payloads(ROOT);self.assertEqual(len(output),7)
  for rec,raw in self.sources:
   pid=rec['paper_id'];self.assertEqual(output[f'{v2.BASE}/{pid}/first-pass.html'],raw)
   page=output[f'{v2.BASE}/{pid}/stage1.html'].decode()
   self.assertEqual(re.findall(r'<section\b.*?</section>',page,re.S),re.findall(r'<section\b.*?</section>',raw.decode(),re.S))
   self.assertEqual(re.findall(r'<script>(.*?)</script>',page,re.S),re.findall(r'<script>(.*?)</script>',raw.decode(),re.S))
   digest=hashlib.sha256((ROOT/'assets/reader-toc-focus-v1.js').read_bytes()).hexdigest()[:12]
   self.assertEqual(page.count(f'../../../assets/reader-toc-focus-v1.js?v={digest}'),1)
   self.assertIn('href="first-pass.html"',page);self.assertNotIn('href="stage2.html"',page);self.assertNotIn('href="stage3.html"',page)
   self.assertIn('noindex,follow',page);self.assertNotIn('尚未正式收录',raw.decode());self.assertNotIn('待视觉验收',raw.decode())
 def test_no_registry_state_changes_and_v1_stays_seven(self):
  self.assertEqual(len(r.load_reports(ROOT)),21);self.assertEqual(len(v1.output_payloads(ROOT)),7)
  self.assertTrue(all(b'reader-toc-focus-v1' not in raw for raw in v1.output_payloads(ROOT).values()))
  for p,b in self.protected.items():self.assertEqual((ROOT/p).read_bytes(),b)
  cat=json.loads(self.protected['data/catalog.json'])
  for p in cat['papers']:
   if p['id']in v2.IDS:self.assertTrue(all(x=={'status':'not_imported','artifacts':[]}for x in p['stages'].values()))
 def test_candidates_cannot_enter_canonical_loader_or_legacy_preview(self):
  for rec,raw in self.sources:
   with self.assertRaises(ValueError):r._validate_record(rec)
   with self.assertRaises(ValueError):r._parse_html(rec,raw,ROOT)
   with self.assertRaises(ValueError):r.report_path(rec)
   (self.root/'data/reports.json').write_text(json.dumps({'schema_version':1,'reports':[rec]}))
   with self.assertRaises(ValueError):r.load_reports(self.root)
   paper={'id':rec['paper_id'],'stages':{s:{'status':'not_imported','artifacts':[]}for s in ('stage1','stage2','stage3')}}
   paper['stages']['stage1']={'status':'imported','artifacts':[{'path':f'artifacts/{rec["paper_id"]}/v2/first-pass.html'}]}
   with self.assertRaises(ValueError):reader.render(ROOT,paper,'stage1',[rec],preview_payload=raw)
 def test_candidate_entry_rejects_approval_relabel_versions_stages(self):
  for rec,raw in self.sources:
   changes=[{'review_status':'content_approved'},{'review_status':'preview_pending'},{'version':'v1'},{'version':'v3'},{'stage':'stage2','filename':'writing-close-reading.html'},{'source_edition':'arXiv unversioned'},{'source_sha256':'0'*64},{'sha256':'0'*64},{'bytes':rec['bytes']+1}]
   for change in changes:
    with self.subTest(pid=rec['paper_id'],change=change),self.assertRaises(ValueError):reader.render_navigation_v2_candidate(ROOT,dict(rec,**change),raw)
  for rec,raw in v1.load_sources(ROOT):
   with self.assertRaises(ValueError):prepare_candidate_v2(ROOT,rec,raw)
 def test_manifest_unknown_missing_duplicate_and_reordered_rejected(self):
  path=self.root/v2.MANIFEST;orig=json.loads(path.read_text())
  for change in [dict(orig,extra=True),dict(orig,status='content_approved'),dict(orig,reports=orig['reports'][::-1]),dict(orig,reports=orig['reports'][:2]),dict(orig,reports=[orig['reports'][0]]*3),dict(orig,base_B_commit='0'*40)]:
   path.write_text(json.dumps(change))
   with self.assertRaises(ValueError):v2.load_sources(self.root)
 def test_rehashing_every_json_field_does_not_authorize_new_document(self):
  for rec,raw in self.sources:
   for insertion in [b'<p>unreviewed prose</p>',b'<script>alert(1)</script>',b'<iframe></iframe>',b'<img src="https://example.com/x">',b'<p onclick="alert(1)">x</p>']:
    changed=raw.replace(b'</body>',insertion+b'</body>');proposed=dict(rec,bytes=len(changed),sha256=r.sha(changed),parts=[{'file':'part-001.txt','bytes':len(changed),'sha256':r.sha(changed)}])
    # Preserve structurally valid 48KB parts; attacker can change all manifest hashes.
    parts=[];start=0
    while start<len(changed):
     end=min(start+48000,len(changed))
     while end<len(changed)and changed[end]&0xC0==0x80:end-=1
     b=changed[start:end];parts.append({'file':f'part-{len(parts)+1:03d}.txt','bytes':len(b),'sha256':r.sha(b)});start=end
    proposed['parts']=parts;p=self.root/f'data/report-{rec["paper_id"]}-stage1-v2-policy.json';policy=json.loads(p.read_text());policy['document_sha256']=r.sha(changed);p.write_text(json.dumps(policy))
    with self.assertRaisesRegex(ValueError,'code-pinned'):prepare_candidate_v2(self.root,proposed,changed)
 def test_chunk_tamper_and_symlink_rejected(self):
  rec=self.sources[0][0];p=self.root/r._parts_path(rec)/rec['parts'][0]['file'];b=p.read_bytes();p.write_bytes(b+b'x')
  with self.assertRaises(ValueError):v2.load_sources(self.root)
  p.unlink();p.symlink_to(ROOT/r._parts_path(rec)/rec['parts'][0]['file'])
  with self.assertRaises(ValueError):v2.load_sources(self.root)
 def test_output_guard_rejects_missing_tampered_and_unexpected(self):
  target=self.root/'out';target.mkdir();v2.write_preview(ROOT,target);self.assertEqual(len(v2.validate_preview(ROOT,target)),7)
  p=target/v2.BASE/'index.html';original=p.read_bytes();p.write_bytes(original+b'x')
  with self.assertRaises(ValueError):v2.validate_preview(ROOT,target)
  p.write_bytes(original);extra=p.with_name('extra.html');extra.write_text('x')
  with self.assertRaises(ValueError):v2.validate_preview(ROOT,target)
  extra.unlink();p.unlink()
  with self.assertRaises(ValueError):v2.validate_preview(ROOT,target)

if __name__=='__main__':unittest.main()
