import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from briefs import validate_brief,load_archive,section
class BriefTests(unittest.TestCase):
 def setUp(self):self.index,self.records=load_archive(ROOT);self.data=copy.deepcopy(json.loads((ROOT/'data/brief-history/2026-09-30-v1.0.json').read_text()))
 def test_bounded_selection_and_consistent_counts(self):
  validate_brief(self.data);self.assertLessEqual(len(self.data['new_papers'])+len(self.data['revised_papers']),5);self.assertEqual(self.data['counts']['new']+self.data['counts']['revisions'],self.data['counts']['window_candidates'])
 def test_automation_label_follows_verified_flag(self):
  self.assertIs(type(self.index['summary_automation_enabled']),bool)
  output=section(self.data,self.index)
  self.assertIn('每日摘要更新已安排' if self.index['summary_automation_enabled'] else '后续自动摘要更新尚未启用',output)
 def test_no_material_update_may_select_zero(self):
  self.data['status']='no_material_update';self.data['new_papers']=[];self.data['revised_papers']=[];self.data['reading_priority']=[];self.data['counts']['selected_new']=0;self.data['counts']['selected_revisions']=0;validate_brief(self.data)
 def test_unknown_field_rejected(self):
  self.data['unexpected']='x'
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_abstract_does_not_imply_reading(self):
  self.data['new_papers'][0]['evidence']['full_paper_read']=True
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_uncompared_revision_cannot_claim_changes(self):
  self.data['revised_papers'][0]['revision_comparison']['changes_verified']=['method changed']
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_count_mismatch_rejected(self):
  self.data['counts']['new']+=1
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_html_escapes_content(self):
  self.data['overview']='<script>bad</script>';out=section(self.data,self.index,prefix='../');self.assertIn('&lt;script&gt;',out);self.assertNotIn('<script>',out)
 def test_source_edition_pinned(self):
  self.data['new_papers'][0]['version_url']=self.data['new_papers'][0]['source_url']
  with self.assertRaises(ValueError):validate_brief(self.data)

class BriefBoundaryRegression(unittest.TestCase):
 def setUp(self):
  self.index,self.records=load_archive(ROOT);self.data=copy.deepcopy(json.loads((ROOT/'data/brief-history/2026-09-30-v1.0.json').read_text()))
 def test_string_counts_cannot_inject_html(self):
  self.data['counts']['new']='24';self.data['counts']['revisions']='<script>alert(1)</script>';self.data['counts']['window_candidates']='24<script>alert(1)</script>'
  with self.assertRaises(ValueError):validate_brief(self.data)
  self.assertNotIn('<script>',section(self.data,self.index))
 def test_boolean_count_rejected(self):
  self.data['counts']['complete_abstracts_checked_for_selection']=True
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_nested_fields_are_allowlisted(self):
  for target in ['snapshot','coverage','evidence','overlap']:
   d=copy.deepcopy(self.data);obj={'snapshot':d['source_snapshot'],'coverage':d['source_snapshot']['coverage'],'evidence':d['new_papers'][0]['evidence'],'overlap':d['new_papers'][0]['curated_catalog_overlap']}[target];obj['unapproved_field']='synthetic'
   with self.subTest(target=target):
    with self.assertRaises(ValueError):validate_brief(d)
 def test_fulltext_requires_full_read_scope(self):
  p=self.data['new_papers'][0];p['evidence_level']='full_text_checked';p['evidence'].update(level='primary_full_text',sections_checked=['method'],supporting_sources=[p['version_url']])
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_unrelated_evidence_source_rejected(self):
  self.data['new_papers'][0]['evidence']['source_url']='https://example.org/'
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_reversed_window_rejected(self):
  self.data['window']['start'],self.data['window']['end']=self.data['window']['end'],self.data['window']['start']
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_selection_must_be_in_candidate_set(self):
  self.data['candidate_ids']=[]
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_v1_cannot_be_labeled_revision(self):
  p=self.data['revised_papers'][0];p['arxiv_version']=1;p['versioned_id']=p['arxiv_id']+'v1';p['version_url']=p['source_url']+'v1';p['evidence']['source_url']=p['version_url']
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_no_material_or_error_cannot_show_five_cards(self):
  for status in ['no_material_update','error']:
   self.data['status']=status
   with self.subTest(status=status):
    with self.assertRaises(ValueError):validate_brief(self.data)
 def test_unindexed_archive_file_rejected(self):
  import shutil
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'data/briefs';shutil.copytree(ROOT/'data/briefs',dest);(dest/'unindexed.txt').write_text('synthetic fixture')
   with self.assertRaises(ValueError):load_archive(Path(tmp))
 def test_symlinked_index_rejected(self):
  import shutil
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'data/briefs';shutil.copytree(ROOT/'data/briefs',dest);index=dest/'index.json';other=Path(tmp)/'index-copy.json';index.rename(other);index.symlink_to(other)
   with self.assertRaises(ValueError):load_archive(Path(tmp))

class ComparisonScopeRegression(unittest.TestCase):
 def setUp(self):_,records=load_archive(ROOT);self.data=copy.deepcopy(json.loads((ROOT/'data/brief-history/2026-09-30-v1.0.json').read_text()))
 def test_new_paper_cannot_smuggle_revision_object(self):
  self.data['new_papers'][0]['revision_comparison']={'unapproved_field':'synthetic'}
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_comparison_label_requires_actual_comparison(self):
  p=self.data['revised_papers'][0];p['evidence_level']='version_comparison';p['evidence'].update(level='primary_version_comparison',version_sources=[p['source_url']+'v2',p['version_url']])
  with self.assertRaises(ValueError):validate_brief(self.data)
 def test_comparison_sources_must_be_distinct_same_paper_versions(self):
  for urls in [['https://example.org/','https://example.org/'],['https://arxiv.org/abs/2609.11111v1','https://arxiv.org/abs/2609.11111v2']]:
   d=copy.deepcopy(self.data);p=d['revised_papers'][0];p['evidence_level']='version_comparison';p['evidence'].update(level='primary_version_comparison',version_sources=urls);p['revision_comparison'].update(performed=True,compared_versions=urls)
   with self.subTest(urls=urls):
    with self.assertRaises(ValueError):validate_brief(d)
 def test_valid_pinned_comparison_contract(self):
  p=self.data['revised_papers'][0];urls=[p['source_url']+'v2',p['version_url']];p['evidence_level']='version_comparison';p['evidence'].update(level='primary_version_comparison',version_sources=urls);p['revision_comparison'].update(performed=True,compared_versions=urls,changes_verified=['Synthetic test statement, not published'])
  validate_brief(self.data)
