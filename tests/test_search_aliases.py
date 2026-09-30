import json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import card,SEARCH_ALIASES
from global_preview import read_preview
class SearchAliasTests(unittest.TestCase):
 def test_only_curated_original_umi_alias_is_added(self):
  self.assertEqual(SEARCH_ALIASES,{'rpa-0064':['UMI']})
  papers=json.loads((ROOT/'data/catalog.json').read_text())['papers']
  p=next(p for p in papers if p['id']=='rpa-0064')
  self.assertEqual(p['title'],'Universal Manipulation Interface: In-The-Wild Robot Teaching Without In-The-Wild Robots')
  self.assertIn(' umi ',card(p).split('data-search="',1)[1].split('"',1)[0])
 def test_isolated_global_uses_same_alias_without_changing_titles(self):
  page=read_preview(ROOT).decode();data=json.loads(re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>',page,re.S)[1]);papers={p['id']:p for p in data['papers']}
  self.assertIn('UMI',papers['rpa-0064']['searchAliases']);self.assertTrue(papers['rpa-0064']['title'].startswith('Universal Manipulation Interface:'))
 def test_mobile_labels_do_not_display_every_relation_neighbor(self):
  page=read_preview(ROOT).decode();self.assertIn("const priority=[hovered,selected,...(w>=800?",page);self.assertIn("function placeLabels(near)",page)
