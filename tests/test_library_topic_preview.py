import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('topicbuild',ROOT/'scripts/build_topic_preview.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class TopicPreview(unittest.TestCase):
 def test_valid_public_allowlist(self):
  data=mod.validate_source(ROOT);self.assertEqual(len(data['records']),95)
 def test_unsafe_urls_rejected(self):
  for url in ['javascript:alert(1)','http://arxiv.org/abs/1','https://localhost/a','https://arxiv.org@localhost/a','https://arxiv.org.evil.test/a','file:///etc/passwd','https://arxiv.org:81/a']:
   with self.assertRaises(ValueError,msg=url):mod.public_url(url)
 def test_unknown_public_fields_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'data').mkdir();shutil.copy(ROOT/'data/catalog.json',root/'data/catalog.json');shutil.copytree(ROOT/'previews',root/'previews')
   p=root/'previews/library-topic-preview/topics.json';d=json.loads(p.read_text());d['records'][0]['private_notes']='do not publish';p.write_text(json.dumps(d))
   with self.assertRaises(ValueError):mod.validate_source(root)
 def test_static_links(self):
  text=(ROOT/'previews/library-topic-preview/index.html').read_text()
  for link in ['../assets/preview-base.css','../atlas-global-preview/','preview.css','preview.js'] : self.assertIn(link,text)
  self.assertIn('另外 82 篇',text);self.assertIn('13 个边界示例',text)
 def fixture(self,root):
  (root/'data').mkdir();shutil.copy(ROOT/'data/catalog.json',root/'data/catalog.json');shutil.copytree(ROOT/'previews',root/'previews')
 def test_source_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.fixture(root);p=root/'previews/library-topic-preview/preview.css';original=p.read_bytes();p.unlink();(root/'outside.css').write_bytes(original);p.symlink_to(root/'outside.css')
   with self.assertRaises(ValueError):mod.validate_source(root)
 def test_target_symlink_rejected_without_external_write(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.fixture(root);outside=root/'outside';outside.mkdir();sentinel=outside/'sentinel';sentinel.write_text('unchanged');target=root/'output';target.symlink_to(outside,target_is_directory=True)
   with self.assertRaises(ValueError):mod.write_preview(root,target)
   self.assertEqual(sentinel.read_text(),'unchanged');self.assertEqual(list(outside.iterdir()),[sentinel])
 def test_target_file_symlink_and_unexpected_file_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.fixture(root);target=root/'output';mod.write_preview(root,target);dest=target/mod.ROUTE;file=dest/'preview.css';file.unlink();outside=root/'outside';outside.write_text('unchanged');file.symlink_to(outside)
   with self.assertRaises(ValueError):mod.write_preview(root,target)
   self.assertEqual(outside.read_text(),'unchanged');file.unlink();file.write_text('css');(dest/'private.txt').write_text('extra')
   with self.assertRaises(ValueError):mod.write_preview(root,target)
 def test_source_parent_symlink_and_traversal_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);self.fixture(root);src=root/'previews';src.rename(root/'moved');src.symlink_to(root/'moved',target_is_directory=True)
   with self.assertRaises(ValueError):mod.validate_source(root)
   with self.assertRaises(ValueError):mod.safe_path(root,root/'output/../../escape')
 def test_editorial_boundary_and_locators(self):
  data=mod.validate_source(ROOT);rows={r['id']:r for r in data['records']}
  for id in ['rpa-0052','rpa-0062']:
   self.assertIn('阅读线索',rows[id]['note']);self.assertIn('不否认',rows[id]['note'])
  self.assertIn('示教训练',rows['rpa-0062']['note'])
  e=next(e for e in rows['rpa-0064']['evidence'] if e['url']=='https://umi-gripper.github.io/')
  self.assertEqual(e['scope'],'官方项目页');self.assertIn('Policy Robustness',e['locator']);self.assertNotIn('prior section',e['locator'])
if __name__=='__main__':unittest.main()
