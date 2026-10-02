"""Validate source-backed venue profiles and source-specific reading summaries."""
import re
from datetime import date
from validate import check_url, ensure

PROFILE_KEYS = {'identity', 'themes', 'style', 'robotics_fit', 'publication', 'boundary'}
EVIDENCE = {'official', 'editorial_synthesis'}


def text(value, name):
    ensure(isinstance(value, str) and bool(value.strip()), f'Missing {name}')
    ensure(not re.search(r'<\s*/?\s*[a-zA-Z][^>]*>', value), f'Markup in {name}')


def checked(value):
    ensure(isinstance(value, str), 'Invalid profile date')
    try:
        ensure(date.fromisoformat(value).isoformat() == value, 'Invalid profile date')
    except (TypeError, ValueError):
        raise ValueError('Invalid profile date')


def validate_submission_profiles(data, require_profiles=True):
    """Envelope v1 remains compatible; publication requires complete profile v1."""
    ensure(data.get('schema_version') == 1, 'Unsupported submission schema')
    pack = data.get('venue_profiles')
    if pack is None:
        ensure(not require_profiles, 'Missing venue profiles')
        return 0
    ensure(set(pack) == {'schema_version', 'checked_at', 'profile_note', 'profiles'} and pack['schema_version'] == 1,
           'Unsupported venue profile schema')
    checked(pack['checked_at'])
    text(pack['profile_note'], 'profile note')
    visible = {v['id'] for v in data['venues']
               if v['kind'] != 'preprint_server' and not v.get('publication_only')}
    profiles = pack['profiles']
    ensure(isinstance(profiles, list), 'Profiles must be a list')
    ensure(len(profiles) == len(visible) and {p['venue_id'] for p in profiles} == visible,
           'Profiles must cover each visible venue exactly once')
    sources = {s['id']: s for s in data['sources']}
    ensure(len(sources) == len(data['sources']), 'Duplicate submission source ID')
    for profile in profiles:
        required = {'venue_id', 'teaser', 'teaser_source_ids', 'teaser_evidence_kind', 'sections', 'checked_at', 'reference_years'}
        ensure(required <= set(profile) <= required | {'reference_note'}, 'Unknown venue profile field')
        ensure(profile['teaser_evidence_kind'] in EVIDENCE, 'Unknown teaser evidence kind')
        if 'reference_note' in profile: text(profile['reference_note'], 'reference note')
        text(profile['teaser'], 'venue teaser')
        checked(profile['checked_at'])
        years = profile['reference_years']
        ensure(isinstance(years, list) and bool(years) and len(set(years)) == len(years),
               'Profile reference years required')
        ensure(all(type(y) is int and 1900 <= y <= 2100 for y in years), 'Invalid reference year')
        sections = profile['sections']
        ensure(isinstance(sections, list) and len(sections) == len(PROFILE_KEYS)
               and {s['key'] for s in sections} == PROFILE_KEYS, 'Six unique profile sections required')
        refs = [('teaser', profile['teaser_source_ids'])]
        for section in sections:
            ensure(set(section) == {'key', 'label', 'text', 'evidence_kind', 'source_ids'},
                   'Unknown profile section field')
            text(section['label'], 'section label')
            text(section['text'], 'section text')
            ensure(section['evidence_kind'] in EVIDENCE, 'Unknown profile evidence kind')
            if section['key'] == 'style':
                ensure(section['evidence_kind'] == 'editorial_synthesis', 'Style must be labeled editorial')
            refs.append((section['key'], section['source_ids']))
        for scope, ids in refs:
            ensure(isinstance(ids, list) and bool(ids) and len(set(ids)) == len(ids),
                   'Nonempty unique profile sources required')
            for sid in ids:
                ensure(sid in sources, 'Unknown profile source')
                source = sources[sid]
                check_url(source['url'])
                text(source.get('title'), 'profile source title')
                text(source.get('claim_supported'), 'source claim scope')
                checked(source['checked_at'])
                ensure(source.get('authority') in {'official', 'primary'}, 'Profiles require official or primary source evidence')
                ensure(source.get('access_status') in {'source_text_observed', 'search_extract_only', 'fetch_failed'},
                       'Profile source access must be disclosed')
                ensure(source.get('access_status') != 'fetch_failed' or scope == 'boundary',
                       'Failed fetch can only support an explicit boundary')
    return len(profiles)


def validate_experience_overview(data):
    pack = data['experiences']
    overview = pack.get('overview')
    ensure(isinstance(overview, dict) and set(overview) == {'schema_version', 'updated_at',
            'summary', 'evidence_note', 'records'} and overview['schema_version'] == 1,
           'Invalid experience overview schema')
    checked(overview['updated_at'])
    for field in ('summary', 'evidence_note'):
        text(overview[field], field)
    records = {r['id']: r for r in pack['records']}
    summaries = overview['records']
    ensure(len(summaries) == len(records) and {s['record_id'] for s in summaries} == set(records),
           'Experience overview must cover each source exactly once')
    for summary in summaries:
        ensure(set(summary) == {'record_id', 'takeaway', 'context', 'outcome_label', 'outcome',
                'boundary', 'preview_boundary', 'evidence_kind'}, 'Unknown experience overview field')
        ensure(summary['evidence_kind'] == 'editorial_synthesis', 'Experience synopsis is editorial')
        for field in ('takeaway', 'context', 'outcome_label', 'outcome', 'boundary', 'preview_boundary'):
            text(summary[field], field)
    return len(summaries)
