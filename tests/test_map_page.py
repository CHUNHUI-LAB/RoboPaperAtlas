import copy
import json
import os
import re
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('ATLAS_SOURCE',str(ROOT)))
sys.path.insert(0,str(SOURCE/'scripts'))
sys.path.insert(0,str(ROOT/'scripts'))
from map_page import map_data, map_html
from reports import load_reports

class MapPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((SOURCE/'data/catalog.json').read_text());cls.reports=load_reports(SOURCE)
        cls.data=map_data(cls.catalog,report_records=cls.reports)
        cls.html=map_html(cls.catalog,report_records=cls.reports)
    def test_all_records_preserved(self):
        self.assertEqual(len(self.data['papers']),95)
        self.assertEqual({p['id'] for p in self.catalog['papers']},{p['id'] for p in self.data['papers']})
    def test_metadata_is_not_reclassified(self):
        for p,projected in zip(self.catalog['papers'],self.data['papers']):
            self.assertEqual(p['category'],projected['category'])
            self.assertEqual(p['tags'],projected['tags'])
            self.assertEqual(p['citation_verified'],projected['sourceChecked'])
            self.assertEqual((p.get('verified_overlay') or {}).get('title') or p['title'],projected['title'])
    def test_original_and_supplemental_provenance(self):
        self.assertEqual(sum(p['originalRecord'] for p in self.data['papers']),73)
        self.assertEqual(sum(p['sourceChecked'] for p in self.data['papers']),22)
        for p in self.data['papers']:
            if p['originalRecord']:self.assertFalse(p['sourceChecked'])
    def test_resource_links_and_pdf_edition_unchanged(self):
        for p,projected in zip(self.catalog['papers'],self.data['papers']):
            for src,dst in [('paper_url','paperUrl'),('pdf_url','pdfUrl'),('pdf_kind','pdfKind'),('code_urls','codeUrls')]:
                self.assertEqual(p[src],projected[dst])
    def test_no_invented_relations_or_stages(self):
        self.assertEqual(self.data['relationMode'],'topic-only')
        self.assertEqual(self.data['verifiedRelations'],[])
        for p in self.data['papers']:
            source=next(x for x in self.catalog['papers'] if x['id']==p['id'])
            for key,state in p['stages'].items():
                self.assertEqual(state['status'],source['stages'][key]['status'])
                self.assertEqual(state['artifacts'],[{'url':'../'+a['path'],'version':a['version']} for a in source['stages'][key]['artifacts']])
    def test_strict_upstream_validation_reused(self):
        data=copy.deepcopy(self.catalog);data['private_skill']='must never publish'
        with self.assertRaises(ValueError):map_data(data,report_records=self.reports)
        data=copy.deepcopy(self.catalog);data['papers'][0]['pdf_url']='javascript:alert(1)'
        with self.assertRaises(ValueError):map_data(data,report_records=self.reports)
        data=copy.deepcopy(self.catalog);data['papers'][0]['stages']['stage1']={'status':'complete','artifacts':[]}
        with self.assertRaises(ValueError):map_data(data,report_records=self.reports)
    def test_public_projection_allowlist(self):
        keys={'id','title','shortName','authors','category','mapTopic','topics','tags','year','yearBasis','originalRecord','sourceChecked','hasVerifiedOverlay','verificationScope','summary','paperUrl','pdfUrl','pdfKind','pdfNote','projectUrl','codeUrls','codeNote','detailUrl','catalogUrl','stages'}
        for paper in self.data['papers']:self.assertEqual(set(paper),keys)
    def test_html_fallback_and_accessibility(self):
        self.assertEqual(self.html.count('data-map-paper='),95)
        self.assertEqual(self.html.count('data-map-row='),95)
        self.assertIn('<noscript>',self.html)
        self.assertIn('role="combobox"',self.html)
        self.assertIn('aria-controls="map-suggestions"',self.html)
        self.assertIn('id="map-legend"',self.html)
        self.assertNotIn('<html',self.html)
    def test_script_injection_cannot_escape_json(self):
        data=copy.deepcopy(self.catalog);data['papers'][0]['title']='Hostile </script><script>alert(1)</script>'
        rendered=map_html(data,report_records=self.reports)
        payload=re.search(r'<script type="application/json" id="paper-map-data">(.*?)</script>',rendered,re.S).group(1)
        self.assertNotIn('</script>',payload)
        self.assertIn('Hostile </script>',json.loads(payload)['papers'][0]['title'])
        self.assertNotIn('<script>alert(1)</script>',rendered)
    def test_generated_links_stay_under_site_subpath(self):
        data=map_data(self.catalog,base='../',report_records=self.reports)
        self.assertTrue(all(p['detailUrl']==f'../papers/{p["id"]}/index.html' for p in data['papers']))
        self.assertNotIn('href="/papers/',self.html)
        self.assertTrue(all(p['catalogUrl']==f'../index.html?topic={p["mapTopic"]}#catalog' for p in data['papers']))
    def test_renderer_has_explicit_truth_legend(self):
        for text in ['不是引用或方法继承','不代表学术影响力','73 条原始书目','22 条增补记录','0','阅读状态']:
            self.assertIn(text,self.html)

if __name__=='__main__':unittest.main()
