"""Offline synthetic fixtures; no network, external libraries, or real papers."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import collect_arxiv as c

RAW = (ROOT / 'tests/fixtures/basic.xml').read_bytes()
START = c.parse_time('2026-09-23T06:00:00Z')
END = c.parse_time('2026-09-30T06:00:00Z')
NOW = lambda: END


def page(indices, start=0, total=None):
    root = ET.fromstring(RAW)
    source = list(root.findall('atom:entry', c.NS))
    for entry in source:
        root.remove(entry)
    for i in indices:
        root.append(copy.deepcopy(source[i]))
    root.find('os:startIndex', c.NS).text = str(start)
    root.find('os:totalResults', c.NS).text = str(total if total is not None else len(indices))
    return ET.tostring(root)


class StubClient:
    def __init__(self, pages):
        self.pages = iter(pages)
        self.urls = []
    def get(self, url):
        self.urls.append(url)
        value = next(self.pages)
        if isinstance(value, Exception):
            raise value
        return value


class Parsing(unittest.TestCase):
    def test_new_and_revision_and_metadata(self):
        p = c.parse_atom(RAW)
        self.assertEqual(p.total, 4)
        self.assertEqual(p.entries[0]['change_type'], 'new')
        revised = p.entries[1]
        self.assertEqual(revised['change_type'], 'revision')
        self.assertEqual(revised['canonical_id'], '2608.00002')
        self.assertEqual(revised['arxiv_version'], 3)
        self.assertEqual(revised['first_submitted_at'], '2026-08-02T10:00:00Z')
        self.assertEqual(revised['updated_at'], '2026-09-28T12:00:00Z')
        self.assertEqual(revised['source_url'], 'https://arxiv.org/abs/2608.00002')
        self.assertEqual(revised['review_status'], 'candidate_not_reviewed')
        self.assertFalse(revised['deep_read'])
        self.assertEqual(len(p.entries[0]['authors']), 2)

    def test_id_variants(self):
        for value in ('2609.12345v2', 'arXiv:2609.12345v2', 'https://arxiv.org/abs/2609.12345v2', 'http://export.arxiv.org/pdf/2609.12345v2.pdf'):
            self.assertEqual(c.canonical_id(value), ('2609.12345', 2))
        self.assertEqual(c.canonical_id('hep-ex/0307015v1'), ('hep-ex/0307015', 1))
        self.assertEqual(c.canonical_id('math.GT/0301001'), ('math.gt/0301001', None))

    def test_ids_reject_other_hosts_and_malformed(self):
        for value in ('https://evil.invalid/abs/2609.12345', 'banana', '2609.12345v0', 'https://arxiv.org/search/x'):
            with self.assertRaises(ValueError):
                c.canonical_id(value)

    def test_date_timezone(self):
        self.assertEqual(c.iso(c.parse_time('2026-09-29T18:00:00-04:00')), '2026-09-29T22:00:00Z')
        with self.assertRaises(ValueError):
            c.parse_time('2026-09-29T18:00:00')

    def test_malformed_and_missing_metadata(self):
        for data in (b'<broken>', b'<html/>', RAW.replace(b'<published>', b'<notpublished>'), RAW.replace(b'Fixture Author One', b'')):
            with self.assertRaises(c.FeedError):
                c.parse_atom(data)

    def test_reject_entity_declarations(self):
        with self.assertRaises(c.FeedError):
            c.parse_atom(b'<!DOCTYPE x [<!ENTITY x "y">]>' + RAW)

    def test_reject_api_error_entry(self):
        with self.assertRaises(c.FeedError):
            c.parse_atom(RAW.replace(b'http://arxiv.org/abs/2609.00001v1', b'http://arxiv.org/api/errors#bad_query'))

    def test_dedupe_keeps_latest_version(self):
        paper = c.parse_atom(RAW).entries[1]
        old = dict(paper, arxiv_version=2, updated_at='2026-08-03T00:00:00Z')
        deduped = c.deduplicate([paper, old, paper])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]['arxiv_version'], 3)


class Heuristics(unittest.TestCase):
    def topics(self, title, abstract=''):
        return c.relevance(title, abstract)[0]
    def test_vln_objectnav(self):
        self.assertIn('vln_objectnav', self.topics('Vision–Language Navigation'))
        self.assertIn('vln_objectnav', self.topics('ObjectNav'))
    def test_robot_gates_reject_generic_ai(self):
        for text in ('A world model for video generation', 'Mixture-of-experts language models', 'Episodic memory for web agents', 'Whole-body control for animated movie characters'):
            self.assertEqual(self.topics(text), [])
    def test_incidental_robot_or_navigation_mentions_are_not_enough(self):
        generic = 'Video diffusion improves image quality. ' * 25 + ' Applications include world modeling and robotics.'
        self.assertEqual(self.topics('Distillation for Video Generation', generic), [])
        generic_nn = 'Neural network geometry and mode connectivity are analyzed. ' * 20 + ' RL agents have different navigation strategies.'
        self.assertEqual(self.topics('Hessian Geometry of Neural Networks', generic_nn), [])
        soil = 'A robot estimates soil friction. ' * 25 + ' The data could support world models.'
        self.assertNotIn('robot_world_models', self.topics('Soil friction from robot forces', soil))

    def test_digital_agents_do_not_count_as_robot_navigation(self):
        for title in ('Web Navigation Agents', 'A Mobile GUI Agent', 'Semantic Navigation for Issue Localization in Code Repository', 'World Models for Autonomous Cyber Defense', 'A Navigable Game Map Generator via World Models'):
            self.assertEqual(self.topics(title, 'Embodied agents use navigation, memory and world models. These ideas are related to robotics.'), [])
        self.assertEqual(self.topics('Video World Models', 'Video diffusion serves embodied AI. Novel attention kernels improve video generation.'), [])
        self.assertEqual(self.topics('A Video World Model Benchmark', 'World models are evaluated in games, real scenes and embodied-robotic videos.'), [])
        self.assertIn('robot_world_models', self.topics('Efficient Visual World Models', 'Visual world models enable robotic planning by predicting future observations.'))

    def test_memory_and_navigation_agent(self):
        self.assertIn('spatial_episodic_memory', self.topics('Spatial memory for a robot'))
        self.assertIn('navigation_agents', self.topics('An agent harness for robot navigation'))
    def test_quadruped_arm_gate(self):
        self.assertNotIn('mobile_manipulation', self.topics('Quadruped locomotion'))
        self.assertIn('mobile_manipulation', self.topics('Quadruped arm manipulation'))
    def test_manipulation_and_control(self):
        topics = self.topics('Robot whole-body control for mobile manipulation', 'End-effector trajectories coordinate a robot arm.')
        for t in ('mobile_manipulation', 'whole_body_control', 'end_effector_trajectories'):
            self.assertIn(t, topics)
    def test_direct_robot_models(self):
        self.assertIn('robot_vla', self.topics('VLA for robotic manipulation'))
        self.assertIn('robot_moe', self.topics('Robot mixture-of-experts policy'))
        self.assertIn('robot_world_models', self.topics('A world model for robot navigation'))
    def test_evidence_transparency(self):
        topics, reasons = c.relevance('Robot spatial memory', 'An agent learns navigation.')
        self.assertIn('navigation_agents', topics)
        for reason in reasons:
            self.assertEqual(reason['method'], 'title_abstract_keyword_heuristic')
            self.assertTrue(reason['evidence'])
            for item in reason['evidence']:
                self.assertIn(item['field'], ('title', 'abstract'))
                self.assertTrue(item['matched_phrases'])


class Collection(unittest.TestCase):
    def collect(self, pages, **kwargs):
        return c.collect(client=StubClient(pages), window_start=START, window_end=END, now=NOW, **kwargs)
    def test_valid_full_window_includes_old_first_submission_revision(self):
        result = self.collect([RAW])
        self.assertEqual(result['status'], 'ok')
        self.assertTrue(result['coverage']['complete'])
        self.assertEqual(result['coverage']['stopped_at'], 'reached_window_start')
        self.assertEqual(result['coverage']['matched_entries'], 2)
        self.assertEqual(len(result['papers']), 2)
        self.assertEqual(result['papers'][1]['first_submitted_at'], '2026-08-02T10:00:00Z')
    def test_pagination_query_uses_update_sort_not_submission_filter(self):
        client = StubClient([page([0, 1], 0, 4), page([2, 3], 2, 4)])
        result = c.collect(client=client, window_start=START, window_end=END, page_size=2, now=NOW)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['coverage']['pages_fetched'], 2)
        self.assertIn('sortBy=lastUpdatedDate', client.urls[0])
        self.assertNotIn('submittedDate', client.urls[0])
        self.assertIn('start=2', client.urls[1])
    def test_page_bound_discloses_truncation(self):
        result = self.collect([page([0, 1], 0, 4)], page_size=2, max_pages=1)
        self.assertEqual(result['status'], 'limited')
        self.assertFalse(result['coverage']['complete'])
        self.assertTrue(result['coverage']['truncated'])
        self.assertEqual(result['coverage']['stopped_at'], 'page_limit')
    def test_display_cap_preserves_full_scan_and_total(self):
        result = self.collect([RAW], max_papers=1)
        self.assertEqual(result['status'], 'limited')
        self.assertTrue(result['coverage']['complete'])
        self.assertTrue(result['coverage']['truncated'])
        self.assertEqual(result['coverage']['matched_entries'], 2)
        self.assertEqual(len(result['papers']), 1)
    def test_true_empty_window_is_success(self):
        result = self.collect([page([], 0, 0)])
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['papers'], [])
        self.assertTrue(result['coverage']['complete'])
    def test_initial_failure_is_truthful_error(self):
        result = self.collect([c.FetchError('offline')])
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['papers'], [])
        self.assertIsNone(result['last_successful_fetch_at'])
        self.assertIsNone(result['fetched_at'])
        self.assertEqual(result['fetch_error'], 'offline')
    def test_transient_failure_preserves_all_previous_data_and_success_timestamp(self):
        previous = self.collect([RAW])
        expected = copy.deepcopy(previous)
        result = c.collect(client=StubClient([c.FetchError('offline')]), window_start=START + timedelta(days=1),
                           window_end=END + timedelta(days=1), previous=previous, now=lambda: END + timedelta(days=1))
        self.assertEqual(result['status'], 'stale')
        for key in ('papers', 'coverage', 'last_successful_fetch_at', 'fetched_at'):
            self.assertEqual(result[key], expected[key])
        self.assertEqual(previous, expected)
        self.assertEqual(result['last_failed_fetch_at'], '2026-10-01T06:00:00Z')
        self.assertNotEqual(result['attempted_coverage']['window_end'], result['coverage']['window_end'])
    def test_partial_failure_does_not_replace_previous(self):
        previous = self.collect([RAW])
        result = self.collect([page([0, 1], 0, 4), c.FetchError('offline')], previous=previous, page_size=2)
        self.assertEqual(result['status'], 'stale')
        self.assertEqual(result['papers'], previous['papers'])
        self.assertEqual(result['attempted_coverage']['pages_fetched'], 1)
    def test_reject_bad_page_order_or_index_or_count(self):
        cases = [([page([1, 0], 0, 2)], 100), ([page([0], 9, 1)], 100),
                 ([page([0, 1], 0, 4), page([2, 3], 2, 5)], 2)]
        for pages, size in cases:
            with self.subTest(size=size):
                self.assertEqual(self.collect(pages, page_size=size)['status'], 'error')
    def test_reject_repeated_page(self):
        result = self.collect([page([0, 1], 0, 4), page([0, 1], 2, 4)], page_size=2)
        self.assertEqual(result['status'], 'error')
        self.assertIn('repeated', result['fetch_error'])
    def test_observation_preserves_first_seen(self):
        previous = self.collect([RAW])
        previous['papers'][0]['first_seen_at'] = '2026-09-29T11:00:00Z'
        result = self.collect([RAW], previous=previous)
        self.assertEqual(result['papers'][0]['observation'], 'unchanged')
        self.assertEqual(result['papers'][0]['first_seen_at'], '2026-09-29T11:00:00Z')
    def test_bounds(self):
        for args in ({'page_size': 501}, {'max_pages': 31}, {'max_papers': 0}):
            with self.assertRaises(ValueError):
                self.collect([], **args)
    def test_public_output_has_only_verbatim_abstract_excerpt(self):
        result = self.collect([RAW])
        paper = result['papers'][0]
        self.assertNotIn('abstract', paper)
        self.assertFalse(paper['abstract_truncated'])
        raw = 'Robot manipulation. ' * 100
        long_paper = c.public_excerpt({'abstract': raw})
        self.assertEqual(long_paper['abstract_excerpt'], raw[:600].rstrip())
        self.assertTrue(long_paper['abstract_truncated'])
        self.assertLessEqual(len(long_paper['abstract_excerpt']), 600)
        self.assertNotIn('abstract', long_paper)

    def test_atomic_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'frontier.json'
            c.atomic_json(path, {'unicode': '机器人', 'papers': []})
            self.assertEqual(json.loads(path.read_text()), {'unicode': '机器人', 'papers': []})
            self.assertEqual(len(list(Path(directory).iterdir())), 1)


class Transport(unittest.TestCase):
    def test_retries_are_bounded_and_delay_enforced(self):
        errors = [urllib.error.URLError('offline')] * 3
        sleeps = []
        calls = []
        def opener(*args, **kwargs):
            calls.append(1)
            raise errors.pop()
        client = c.APIClient(opener=opener, sleep=sleeps.append, monotonic=lambda: 0)
        with self.assertRaises(c.FetchError):
            client.get(c.ENDPOINT)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(s >= 3 for s in sleeps))
    def test_does_not_retry_bad_request(self):
        def opener(*args, **kwargs):
            raise urllib.error.HTTPError(c.ENDPOINT, 400, 'Bad request', {}, None)
        client = c.APIClient(opener=opener, sleep=lambda s: None)
        with self.assertRaises(c.FetchError):
            client.get(c.ENDPOINT)
        self.assertEqual(client.request_count, 1)
    def test_honors_retry_after_and_success(self):
        calls, sleeps = [], []
        def opener(*args, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise urllib.error.HTTPError(c.ENDPOINT, 429, 'Slow down', {'Retry-After': '10'}, None)
            return io.BytesIO(RAW)
        client = c.APIClient(opener=opener, sleep=sleeps.append, monotonic=lambda: 0)
        self.assertEqual(client.get(c.ENDPOINT), RAW)
        self.assertIn(10, sleeps)
    def test_long_retry_after_stops_without_early_retry(self):
        def opener(*args, **kwargs):
            raise urllib.error.HTTPError(c.ENDPOINT, 429, 'Slow down', {'Retry-After': '900'}, None)
        client = c.APIClient(opener=opener, sleep=lambda s: None)
        with self.assertRaises(c.FetchError):
            client.get(c.ENDPOINT)
        self.assertEqual(client.request_count, 1)
    def test_cannot_relax_rate_limit(self):
        with self.assertRaises(ValueError):
            c.APIClient(min_interval=1)


if __name__ == '__main__':
    unittest.main()
