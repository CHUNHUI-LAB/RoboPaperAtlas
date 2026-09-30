#!/usr/bin/env python3
"""Collect a bounded, transparent arXiv candidate feed using only Python stdlib.

No authentication, LLM calls, scheduler, PDF downloads, or HTML scraping.
All times UTC. A successful scan covers the declared query, not all literature.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import email.utils
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UTC = timezone.utc
ENDPOINT = "https://export.arxiv.org/api/query"
SCHEMA_VERSION = "1.0"
RULE_VERSION = "2026-09-30.3"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom", "os": "http://a9.com/-/spec/opensearch/1.1/"}
TOPICS = {
    "vln_objectnav": "VLN / ObjectNav",
    "navigation_agents": "Navigation agents / harnesses",
    "spatial_episodic_memory": "Spatial / episodic memory and feedback",
    "mobile_manipulation": "Quadruped-arm / mobile manipulation",
    "whole_body_control": "Whole-body control",
    "end_effector_trajectories": "End-effector trajectories",
    "robot_vla": "Robot VLA",
    "robot_moe": "Robot mixture-of-experts",
    "robot_world_models": "Robot world models",
}
# Retrieval is deliberately wider than local title+abstract matching. Quoted
# phrases plus spelling variants make the query reproducible and explainable.
QUERY_TERMS = (
    'all:"vision-language navigation"', 'all:"vision language navigation"',
    'all:VLN', 'all:ObjectNav', 'all:"object-goal"', 'all:"object goal"',
    '((ti:navigation OR abs:navigation) AND (all:agent OR all:memory OR all:feedback OR all:harness OR all:reflection))',
    'all:"spatial memory"', 'all:"episodic memory"', 'all:"mobile manipulation"',
    'all:"mobile manipulator"', 'all:quadruped', 'all:"whole-body"', 'all:"whole body"',
    'all:"end-effector"', 'all:"end effector"', 'all:"vision-language-action"',
    'all:"vision language action"', 'all:"world-action model"', 'all:"world action model"',
    '((all:VLA OR all:MoE OR all:"mixture of experts" OR all:"mixture-of-experts" OR all:"world model" OR all:"world models") AND (all:robot OR all:robotic OR all:robotics OR all:manipulation OR all:navigation OR all:embodied))',
)
SEARCH_QUERY = '(cat:cs.RO OR cat:cs.CV OR cat:cs.AI OR cat:cs.LG OR cat:cs.CL) AND (' + ' OR '.join(QUERY_TERMS) + ')'
BASE_LIMITATIONS = [
    "Candidates are heuristic title-and-abstract matches, not reviewed or deep-read recommendations.",
    "Coverage is limited to the declared arXiv query and categories; indexing delay and terminology can omit relevant work.",
    "This feed discovers preprints. Curated reading should prefer an available formally published version.",
    "New/revision describes the retrieved arXiv version, not novelty, publication acceptance, or first appearance on this site.",
]


def utcnow():
    return datetime.now(UTC)


def iso(dt):
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_time(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timezone required')
    return dt.astimezone(UTC)


def clean(value):
    return ' '.join((value or '').split())


def norm(value):
    value = unicodedata.normalize('NFKC', value).lower()
    return re.sub(r'[\s\-‐‑‒–—]+', ' ', value)


def canonical_id(value):
    """Return validated canonical ID and optional version, including old IDs."""
    value = value.strip()
    if '://' in value:
        parts = urllib.parse.urlparse(value)
        if parts.hostname not in ('arxiv.org', 'www.arxiv.org', 'export.arxiv.org'):
            raise ValueError('Unexpected arXiv identifier host')
        if not parts.path.startswith(('/abs/', '/pdf/')):
            raise ValueError('Unexpected arXiv identifier path')
        value = parts.path.split('/', 2)[2].removesuffix('.pdf')
    value = re.sub(r'^arxiv:', '', value, flags=re.I)
    match = re.fullmatch(r'(?P<id>\d{4}\.\d{4,5}|[a-z][a-z.-]+/\d{7})(?:v(?P<version>[1-9]\d*))?', value, re.I)
    if not match:
        raise ValueError('Invalid arXiv identifier')
    return match['id'].lower(), int(match['version']) if match['version'] else None


def relevance(title, abstract):
    """Deterministic labels and exact matching evidence; no semantic claims."""
    fields = {'title': norm(title), 'abstract': norm(abstract)}
    digital_title = r'\b(web agent\w*|web navigation|web environment\w*|gui|browser|cyber\w*|software engineering|code repository|codebase|game map|mobile agents|app interfaces|information spaces|reasoning space)\b'
    if re.search(digital_title, fields['title']) and not re.search(r'\b(robot\w*|quadruped\w*|humanoid\w*)\b', fields['title']):
        return [], []
    text = fields['title'] + ' ' + fields['abstract']
    nav = bool(re.search(r'\b(navigation|navigat\w*|objectnav|vln)\b', text))
    robot = bool(re.search(r'\b(robot\w*|embodied|manipulat\w*|quadruped\w*|legged|humanoid\w*)\b', text))
    # Incidental robotics mentions in a generic AI paper are not enough.
    # This deliberately conservative first version requires direct domain
    # context in the title or first 600 normalized abstract characters.
    focus = fields['title'] + ' ' + fields['abstract'][:600]
    domain_focus = bool(re.search(r'\b(robot\w*|embodied|manipulat\w*|quadruped\w*|legged|humanoid\w*|objectnav|vln|visual navigation|vision language navigation|pointnav|habitat|matterport|sensorimotor)\b', focus))
    nav_focus = bool(re.search(r'\b(navigation|navigat\w*|objectnav|vln)\b', focus))
    world_focus = bool(re.search(r'\b(world (?:action )?model\w*)\b', focus))
    physical_mentions = re.findall(r'\b(robot\w*|quadruped\w*|legged|humanoid\w*|dexterous|bimanual)\b', fields['abstract'])
    model_robot_focus = bool(re.search(r'\b(robot\w*|quadruped\w*|legged|humanoid\w*|dexterous|bimanual|navigation|manipulat\w*)\b', fields['title'])) or len(physical_mentions) >= 2 or bool(re.search(r'\b(robot(?:ic)? (?:\w+ ){0,2}(?:polic\w*|control|planning|manipulat\w*|learning|interaction\w*|action\w*)|(?:dexterous|bimanual|contact rich) manipulat\w*|embodied (?:navigation|control|visual tracking))\b', focus))
    mobile = bool(re.search(r'\b(mobile manipulat\w*|quadruped\w*|legged|loco manipulation|locomanipulation)\b', text))
    manip = bool(re.search(r'\b(manipulat\w*|arm\w*|grasp\w*)\b', text))
    rules = [
        ('vln_objectnav', True, r'\b(vision (?:and )?language navigation|vln|objectnav|object goal navigation|object navigation)\b'),
        ('navigation_agents', nav and nav_focus and domain_focus, r'\b(agent\w*|harness\w*|tool use|tool calling|replanning|reflection|self correction)\b'),
        ('spatial_episodic_memory', (nav or robot) and domain_focus, r'\b(spatial memory|episodic memory|semantic memory|long term memory|memory bank|memory augmented|memory driven|self reflection|self correction|closed loop feedback)\b'),
        ('mobile_manipulation', mobile and manip, r'\b(mobile manipulat\w*|quadruped\w*|legged|loco manipulation|locomanipulation)\b'),
        ('whole_body_control', robot, r'\b(whole body control|whole body motion|whole body coordination|whole body planning|wbc)\b'),
        ('end_effector_trajectories', robot and bool(re.search(r'\b(trajector\w*|planning|control)\b', text)), r'\b(end effector\w*|ee trajector\w*)\b'),
        ('robot_vla', robot and domain_focus, r'\b(vision language action|vla|vlas)\b'),
        ('robot_moe', robot and domain_focus, r'\b(mixture of experts|mixture of expert|moe)\b'),
        ('robot_world_models', (robot or nav) and domain_focus and world_focus and model_robot_focus, r'\b(world (?:action )?model\w*)\b'),
    ]
    topics, reasons = [], []
    for topic, gate, pattern in rules:
        if not gate:
            continue
        matches = []
        for field, contents in fields.items():
            phrases = list(dict.fromkeys(m.group(0) for m in re.finditer(pattern, contents)))
            if phrases:
                matches.append({'field': field, 'matched_phrases': phrases[:8]})
        if matches:
            topics.append(topic)
            reasons.append({'topic': topic, 'label': TOPICS[topic], 'method': 'title_abstract_keyword_heuristic', 'evidence': matches,
                            'reason': 'Keyword evidence in title/abstract with navigation or robot context where required; relevance is not human-verified.'})
    return topics, reasons


class FeedError(Exception):
    pass


class FetchError(Exception):
    pass


@dataclass
class Page:
    entries: list
    total: int
    start: int
    feed_updated_at: str | None


def parse_atom(payload):
    if len(payload) > 8_000_000:
        raise FeedError('Atom response exceeds 8 MB bound')
    # ElementTree does not fetch remote entities, but reject declarations too.
    if re.search(br'<!DOCTYPE|<!ENTITY', payload, re.I):
        raise FeedError('Unexpected XML declarations')
    try:
        root = ET.fromstring(payload)
        if root.tag != '{' + NS['atom'] + '}feed':
            raise FeedError('Response is not an Atom feed')
        total = int(root.findtext('os:totalResults', namespaces=NS))
        start = int(root.findtext('os:startIndex', namespaces=NS))
        if total < 0 or start < 0:
            raise ValueError('Negative OpenSearch metadata')
        entries = []
        for e in root.findall('atom:entry', NS):
            raw_id = clean(e.findtext('atom:id', namespaces=NS))
            if '/api/errors' in raw_id:
                raise FeedError('arXiv returned an Atom error entry')
            paper_id, version = canonical_id(raw_id)
            published = parse_time(e.findtext('atom:published', namespaces=NS))
            updated = parse_time(e.findtext('atom:updated', namespaces=NS))
            if updated < published:
                raise FeedError('Entry updated date precedes first submission')
            title = clean(e.findtext('atom:title', namespaces=NS))
            abstract = clean(e.findtext('atom:summary', namespaces=NS))
            authors = [clean(a.findtext('atom:name', namespaces=NS)) for a in e.findall('atom:author', NS)]
            if not title or not abstract or not authors or not all(authors):
                raise FeedError('Entry has missing required bibliographic metadata')
            if version == 1 and updated != published:
                raise FeedError('Version 1 has inconsistent publication/update dates')
            topics, reasons = relevance(title, abstract)
            primary = e.find('arxiv:primary_category', NS)
            entries.append({
                'id': paper_id, 'canonical_id': paper_id, 'arxiv_version': version,
                'versioned_id': paper_id + (f'v{version}' if version else ''),
                'title': title, 'authors': authors, 'abstract': abstract,
                'first_submitted_at': iso(published), 'updated_at': iso(updated),
                'change_type': 'revision' if updated > published or (version or 1) > 1 else 'new',
                'source_url': 'https://arxiv.org/abs/' + paper_id,
                'version_url': 'https://arxiv.org/abs/' + paper_id + (f'v{version}' if version else ''),
                'categories': list(dict.fromkeys(c.attrib['term'] for c in e.findall('atom:category', NS))),
                'primary_category': primary.attrib.get('term') if primary is not None else None,
                'doi': clean(e.findtext('arxiv:doi', namespaces=NS)) or None,
                'journal_reference': clean(e.findtext('arxiv:journal_ref', namespaces=NS)) or None,
                'matched_topics': topics, 'relevance_reasons': reasons,
                'review_status': 'candidate_not_reviewed', 'deep_read': False,
            })
        return Page(entries, total, start, root.findtext('atom:updated', namespaces=NS))
    except (ET.ParseError, TypeError, ValueError, KeyError) as exc:
        raise FeedError('Malformed or incomplete arXiv Atom response') from exc


class APIClient:
    """One connection; >=3 seconds between request starts; bounded backoff."""
    def __init__(self, *, min_interval=3.1, attempts=3, timeout=35, user_agent='RoboPaperAtlas/1.0 (arXiv metadata discovery)', opener=None, sleep=time.sleep, monotonic=time.monotonic):
        if min_interval < 3 or not 1 <= attempts <= 4:
            raise ValueError('Use >=3-second interval and 1..4 attempts')
        self.min_interval, self.attempts, self.timeout = min_interval, attempts, timeout
        self.user_agent, self.opener, self.sleep, self.monotonic = user_agent, opener or urllib.request.urlopen, sleep, monotonic
        self.last_start = None
        self.request_count = 0

    def get(self, url):
        for attempt in range(self.attempts):
            if self.last_start is not None:
                self.sleep(max(0, self.min_interval - (self.monotonic() - self.last_start)))
            self.last_start = self.monotonic()
            self.request_count += 1
            retry_after = None
            try:
                request = urllib.request.Request(url, headers={'User-Agent': self.user_agent, 'Accept': 'application/atom+xml'})
                with self.opener(request, timeout=self.timeout) as response:
                    data = response.read(8_000_001)
                    if len(data) > 8_000_000:
                        raise FetchError('API response exceeds 8 MB bound')
                    return data
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504):
                    raise FetchError(f'arXiv HTTP {exc.code}; not retried') from exc
                error = f'arXiv HTTP {exc.code}'
                raw = exc.headers.get('Retry-After', '') if exc.headers else ''
                try:
                    retry_after = float(raw)
                except ValueError:
                    try:
                        retry_after = (email.utils.parsedate_to_datetime(raw) - utcnow()).total_seconds()
                    except (TypeError, ValueError, OverflowError):
                        pass
                if retry_after is not None and retry_after > 120:
                    raise FetchError(f'{error}; server requested a long Retry-After, stopping') from exc
            except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as exc:
                error = 'Network connection or timeout error fetching arXiv'
            if attempt + 1 == self.attempts:
                raise FetchError(f'{error}; exhausted {self.attempts} attempts')
            self.sleep(max(self.min_interval, retry_after or 0, 2 ** (attempt + 1)))
        raise AssertionError('Unreachable')


def public_excerpt(paper):
    """Publish only a source-text prefix; selection still sees the full abstract."""
    if 'abstract' in paper:
        abstract = paper.pop('abstract')
        paper['abstract_excerpt'] = abstract[:600].rstrip()
        paper['abstract_truncated'] = len(abstract) > 600
        paper['abstract_original_chars'] = len(abstract)
        paper['abstract_excerpt_method'] = 'verbatim_prefix_whitespace_normalized'
    return paper


def deduplicate(entries):
    result = {}
    for paper in entries:
        key = paper['canonical_id']
        prev = result.get(key)
        if prev is None or (paper['updated_at'], paper['arxiv_version'] or 0) > (prev['updated_at'], prev['arxiv_version'] or 0):
            result[key] = paper
    return sorted(result.values(), key=lambda p: (p['updated_at'], p['canonical_id']), reverse=True)


def collect(*, client, window_start, window_end, previous=None, page_size=100, max_pages=12, max_papers=300, query=SEARCH_QUERY, now=utcnow):
    if not 1 <= page_size <= 500 or not 1 <= max_pages <= 30 or not 1 <= max_papers <= 1000:
        raise ValueError('Bounded pagination required')
    if window_start >= window_end or window_end - window_start > timedelta(days=31):
        raise ValueError('Window must be positive and at most 31 days')
    started = iso(now())
    coverage = {'window_start': iso(window_start), 'window_end': iso(window_end), 'window_inclusive': True,
                'date_field': 'updated_at', 'complete': False, 'truncated': False,
                'api_total_results': None, 'fetched_entries': 0, 'pages_fetched': 0,
                'window_entries': 0, 'matched_entries': 0, 'displayed_entries': 0,
                'stopped_at': None, 'source': 'arxiv_api', 'limitations': list(BASE_LIMITATIONS)}
    document = {'schema_version': SCHEMA_VERSION, 'generated_at': started, 'fetched_at': None,
                'last_successful_fetch_at': None, 'last_failed_fetch_at': None, 'fetch_error': None,
                'status': 'pending', 'coverage': coverage,
                'collection': {'endpoint': ENDPOINT, 'search_query': query, 'sort_by': 'lastUpdatedDate',
                    'sort_order': 'descending', 'page_size': page_size, 'max_pages': max_pages,
                    'max_papers': max_papers, 'rule_version': RULE_VERSION},
                'topic_labels': TOPICS, 'papers': []}
    entries, page_hashes = [], set()
    oldest_seen = None
    try:
        for page_number in range(max_pages):
            start_index = page_number * page_size
            url = ENDPOINT + '?' + urllib.parse.urlencode({'search_query': query, 'start': start_index,
                     'max_results': page_size, 'sortBy': 'lastUpdatedDate', 'sortOrder': 'descending'})
            raw = client.get(url)
            page = parse_atom(raw)
            if page.start != start_index:
                raise FeedError('API returned unexpected pagination index')
            page_hash = hashlib.sha256(json.dumps([p['versioned_id'] for p in page.entries]).encode()).hexdigest()
            if page.entries and page_hash in page_hashes:
                raise FeedError('API repeated a page; coverage cannot be trusted')
            page_hashes.add(page_hash)
            if coverage['api_total_results'] is not None and coverage['api_total_results'] != page.total:
                raise FeedError('API result count changed during pagination; retry next run')
            coverage['api_total_results'] = page.total
            coverage['pages_fetched'] += 1
            coverage['fetched_entries'] += len(page.entries)
            document['fetched_at'] = iso(now())
            dates = [parse_time(p['updated_at']) for p in page.entries]
            if dates != sorted(dates, reverse=True) or (dates and oldest_seen is not None and dates[0] > oldest_seen):
                raise FeedError('API lastUpdatedDate ordering is inconsistent')
            if dates:
                oldest_seen = dates[-1]
            entries.extend(p for p in page.entries if window_start <= parse_time(p['updated_at']) <= window_end)
            if dates and dates[-1] < window_start:
                coverage['complete'], coverage['stopped_at'] = True, 'reached_window_start'
                break
            if start_index + len(page.entries) >= page.total:
                coverage['complete'], coverage['stopped_at'] = True, 'exhausted_query'
                break
            if not page.entries or len(page.entries) < page_size:
                raise FeedError('Unexpected short page before end of API results')
        else:
            coverage['truncated'], coverage['stopped_at'] = True, 'page_limit'
            coverage['limitations'].append('Page limit reached before covering the full UTC window; older candidates may be missing.')
        unique = deduplicate(entries)
        matched = [p for p in unique if p['matched_topics']]
        coverage['window_entries'], coverage['matched_entries'] = len(unique), len(matched)
        if len(matched) > max_papers:
            coverage['truncated'] = True
            coverage['limitations'].append(f'Display capped at {max_papers} most recently updated candidates; full-query scan status is shown separately.')
        document['papers'] = matched[:max_papers]
        coverage['displayed_entries'] = len(document['papers'])
        stamp = iso(now())
        document['generated_at'] = stamp
        document['last_successful_fetch_at'] = stamp
        document['status'] = 'ok' if coverage['complete'] and not coverage['truncated'] else 'limited'
        previous_by_id = {p['canonical_id']: p for p in (previous or {}).get('papers', [])}
        for paper in document['papers']:
            old = previous_by_id.get(paper['canonical_id'])
            paper['fetched_at'] = document['fetched_at']
            paper['first_seen_at'] = old.get('first_seen_at', stamp) if old else stamp
            paper['observation'] = 'first_seen' if not old else ('version_updated' if paper['updated_at'] != old.get('updated_at') or paper['arxiv_version'] != old.get('arxiv_version') else 'unchanged')
            public_excerpt(paper)
        return document
    except (FetchError, FeedError) as exc:
        failed_at = iso(now())
        # Never wipe the last usable feed or claim its content was just fetched.
        if previous and previous.get('last_successful_fetch_at'):
            preserved = copy.deepcopy(previous)
            preserved.update({'status': 'stale', 'generated_at': failed_at, 'last_failed_fetch_at': failed_at,
                              'fetch_error': str(exc), 'attempted_coverage': coverage,
                              'attempted_collection': document['collection']})
            return preserved
        document.update({'status': 'error', 'generated_at': failed_at, 'last_failed_fetch_at': failed_at,
                         'fetch_error': str(exc), 'papers': []})
        coverage['stopped_at'] = 'fetch_failed'
        coverage['limitations'].append('No successful complete feed is available. Empty candidates do not mean no relevant papers exist.')
        return document


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.write('\n')
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/frontier.json'))
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--as-of', help='UTC ISO timestamp; default now')
    parser.add_argument('--page-size', type=int, default=100)
    parser.add_argument('--max-pages', type=int, default=12)
    parser.add_argument('--max-papers', type=int, default=300)
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--cache-hours', type=float, default=23, help='Skip repeat successful scans inside this age; 0 explicitly refreshes')
    args = parser.parse_args(argv)
    if not 1 <= args.days <= 31 or not 0 <= args.cache_hours <= 168:
        parser.error('days must be 1..31 and cache-hours 0..168')
    previous = None
    if args.output.exists():
        try:
            previous = json.loads(args.output.read_text(encoding='utf-8'))
            if previous.get('schema_version') != SCHEMA_VERSION or not isinstance(previous.get('papers'), list):
                raise ValueError('Unknown schema')
        except (ValueError, OSError) as exc:
            print('Refusing to overwrite an unreadable or incompatible existing feed.', file=sys.stderr)
            return 2
    end = parse_time(args.as_of) if args.as_of else utcnow().replace(microsecond=0)
    start = end - timedelta(days=args.days)
    if previous and previous.get('status') in ('ok', 'limited') and previous.get('last_successful_fetch_at') and not args.as_of:
        age = (utcnow() - parse_time(previous['last_successful_fetch_at'])).total_seconds() / 3600
        old_collection = previous.get('collection', {})
        old_coverage = previous.get('coverage', {})
        old_days = (parse_time(old_coverage['window_end']) - parse_time(old_coverage['window_start'])).days
        same_config = (old_collection.get('search_query') == SEARCH_QUERY and old_collection.get('rule_version') == RULE_VERSION
                       and old_collection.get('page_size') == args.page_size and old_collection.get('max_pages') == args.max_pages
                       and old_collection.get('max_papers') == args.max_papers and old_days == args.days)
        if same_config and 0 <= age < args.cache_hours:
            print(json.dumps({'status': 'cached', 'last_successful_fetch_at': previous['last_successful_fetch_at'], 'papers': len(previous['papers'])}))
            return 0
    try:
        client = APIClient(attempts=args.attempts)
        result = collect(client=client, window_start=start, window_end=end, previous=previous,
                         page_size=args.page_size, max_pages=args.max_pages, max_papers=args.max_papers)
    except ValueError as exc:
        parser.error(str(exc))
    atomic_json(args.output, result)
    print(json.dumps({'status': result['status'], 'papers': len(result['papers']), 'coverage': result['coverage'],
                      'request_count': client.request_count, 'fetch_error': result['fetch_error']}, ensure_ascii=False))
    return 1 if result['status'] in ('error', 'stale') else 0


if __name__ == '__main__':
    raise SystemExit(main())
