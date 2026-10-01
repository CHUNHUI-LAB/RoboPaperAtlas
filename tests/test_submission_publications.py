import json
from pathlib import Path
import unittest
import subprocess
ROOT = Path(__file__).resolve().parents[1]

class SubmissionPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT/'submit-preview/data/venues.json').read_text())

    def test_frontend_behavior(self):
        subprocess.run(['node', '--test', 'tests/test_submission_publications.cjs'], cwd=ROOT, check=True, capture_output=True, text=True)

    def test_counts_and_recommendation_boundary(self):
        d=self.data
        self.assertEqual(len(d['publications']),8)
        self.assertEqual(len({p['paper_id'] for p in d['publications']}),8)
        self.assertEqual(d['migration'],{'total':95,'normalized':8,'pending':87})
        self.assertEqual(len([v for v in d['venues'] if v['kind']!='preprint_server' and not v.get('publication_only')]),15)
        aaai=next(v for v in d['venues'] if v['id']=='aaai')
        self.assertTrue(aaai['publication_only'])
        self.assertEqual(aaai['admission']['state'],'historical_only')

    def test_same_record_channel_and_source_integrity(self):
        d=self.data;venues={v['id']:v for v in d['venues']};editions={e['id']:e for e in d['editions']};sources={s['id']:s for s in d['sources']}
        self.assertEqual(len(sources),len(d['sources']))
        for p in d['publications']:
            self.assertIn(p['venue_id'],venues)
            e=editions[p['edition_id']];self.assertEqual(e['venue_id'],p['venue_id'])
            channel=next(c for c in e['channels'] if c['id']==p['channel_id'])
            self.assertEqual(channel['parent_edition_id'],e['id'])
            for sid in p['evidence']['source_ids']:self.assertIn(sid,sources)
        for e in editions.values():
            if e.get('publication_only'):
                self.assertEqual(e['status'],'historical')
                self.assertFalse(e['deadlines']);self.assertFalse(e['templates'])
        def source_refs(obj):
            if isinstance(obj,dict):
                for k,v in obj.items():
                    if k=='source_ids':
                        for sid in v:self.assertIn(sid,sources)
                    else:source_refs(v)
            elif isinstance(obj,list):
                for x in obj:source_refs(x)
        source_refs(d)

    def test_publication_topics_follow_reviewed_classification(self):
        reviewed={r['id']:r for r in json.loads((ROOT/'data/classification.json').read_text())['records']}
        for paper in self.data['publications']:
            self.assertEqual(paper['primary_direction'],reviewed[paper['paper_id']]['primary_direction'],paper['paper_id'])

    def test_new_ral_experience_preserves_self_report_limits(self):
        records=self.data['experiences']['records']
        record=next(r for r in records if r['id']=='zhihu-ral-secondreview-lan-2023')
        self.assertEqual(record['venue_id'],'ral')
        self.assertEqual(record['source_type'],'first_person_self_report')
        self.assertEqual(record['source_url'],'https://www.zhihu.com/question/551995333/answer/3303533766')
        self.assertIn('另外2条未展开',record['reading_scope'])
        self.assertIn('身份和具体论文未独立核验',record['verification_limit'])
        self.assertEqual(len(record['comments']),3)
        self.assertTrue(any('不采信' in x for x in record['cautions']))
        self.assertNotIn(record['id'],{p['id'] for p in self.data['publications']})

    def test_formal_workshop_and_oral_are_distinct(self):
        d=self.data;p={p['paper_id']:p for p in d['publications']}
        self.assertEqual(p['rpa-0052']['record_kind'],'journal_article')
        self.assertIsNone(p['rpa-0052']['edition_year'])
        self.assertEqual(p['rpa-0012']['edition_year'],2022)
        self.assertEqual(p['rpa-0012']['publication_year'],2023)
        self.assertEqual(p['rpa-0026']['authors'][0],'Tifanny Portela')
        self.assertEqual(p['rpa-0042']['record_kind'],'conference_paper')
        self.assertEqual(len(d['workshop_contributions']),2)
        for w in d['workshop_contributions']:
            self.assertEqual(w['state'],'accepted_contribution')
            self.assertEqual(w['archival_publication_status'],'unknown')
            self.assertEqual(w['actual_presentation_status'],'unknown')
            self.assertNotIn(w['id'],{x['id'] for x in d['publications']})
        self.assertEqual(d['presentations'][0]['type'],'oral_selection')
        self.assertEqual(d['presentations'][0]['actual_presentation_status'],'unknown')
        for p in list(p.values())[3:]:
            self.assertIsNone(p['online_first_date'])
            self.assertEqual(p['preprint']['paper_id'],p['paper_id'])

if __name__=='__main__':unittest.main()
