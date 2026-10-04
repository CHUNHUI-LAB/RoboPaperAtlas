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
        keys={'id','title','shortName','classificationSearch','authors','category','mapTopic','topics','classification','tags','year','yearBasis','display','originalRecord','sourceChecked','hasVerifiedOverlay','verificationScope','summary','paperUrl','pdfUrl','pdfKind','pdfNote','projectUrl','codeUrls','codeNote','detailUrl','catalogUrl','stages'}
        for paper in self.data['papers']:
            self.assertEqual(set(paper),keys)
            self.assertEqual(set(paper['display']),{'methodLabels','yearLabel','metadataLabel','pdfNoteHeading','codeNote','classificationRationale','classificationEvidenceScope'})
            self.assertEqual(set(paper['display']['methodLabels']),{t['label'] for t in paper['classification']['methodTags']})
            self.assertTrue(all(isinstance(k,str) and isinstance(v,str) for k,v in paper['display']['methodLabels'].items()))
            self.assertIsInstance(paper['classificationSearch'],str)
            self.assertTrue(all(isinstance(value,str) for key,value in paper['display'].items() if key != 'methodLabels'))
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
        from urllib.parse import quote
        self.assertTrue(all(p['catalogUrl']==f'../index.html?q={quote(p["title"], safe="")}#catalog' for p in data['papers']))
    def test_renderer_has_explicit_truth_legend(self):
        for text in ['不是引用或方法继承','不代表学术影响力','73 条原始书目','22 条增补记录','0','阅读状态']:
            self.assertIn(text,self.html)


    def test_display_labels_keep_original_evidence_and_date_scope(self):
        from atlas_taxonomy import atlas_projection
        before=copy.deepcopy(self.catalog)
        projected=map_data(self.catalog,report_records=self.reports)
        self.assertEqual(self.catalog,before)
        taxonomy=atlas_projection(self.catalog['papers'])
        for raw,p in zip(self.catalog['papers'],projected['papers']):
            self.assertEqual(p['year'],raw.get('bibliographic_year'))
            self.assertEqual(p['yearBasis'],raw.get('year_basis'))
            self.assertEqual(p['classification'],taxonomy['placements'][raw['id']])
            self.assertEqual(p['codeNote'],raw.get('code_note') or '')
            self.assertEqual(p['pdfNote'],raw.get('pdf_note') or '')
        deep=next(p for p in projected['papers'] if p['id']=='rpa-0012')
        self.assertEqual(deep['display']['yearLabel'],'2023 · 正式出版年（独立核验）；2022 · 原始记录年')
        self.assertIn('2026-09-30',deep['display']['pdfNoteHeading'])
        self.assertIn('后续阅读范围见各阶段报告',deep['display']['pdfNoteHeading'])
        self.assertEqual(deep['display']['metadataLabel'],'正式书目已核验（独立补充）')
        self.assertNotIn('Author-linked',deep['display']['codeNote'])
        self.assertIn('未运行代码或独立复现',deep['display']['codeNote'])
        self.assertIn('2023 · 正式出版年（独立核验）；2022 · 原始记录年',self.html)

if __name__=='__main__':unittest.main()
