"""One reviewed UMI Stage 2 v4 reader, not an arbitrary active-HTML importer.

The original v1-v3 policies are unchanged. This boundary requires the exact
paper/stage/version, source PDF, document, stylesheet and interaction-script
fingerprints, then applies the existing HTML, CSS, URL and resource guards.
"""
import json
import re

from reports import (ReportHTML, ALLOWED_TAGS, TAG_ATTRS, require, sha, _read,
                     _keys, _digest, _json_object)

IDENTITY = dict(paper_id='rpa-0062', stage='stage2', version='v4',
                filename='writing-close-reading.html')
POLICY_PATH = 'data/report-rpa-0062-stage2-v4-policy.json'
POLICY_FIELDS = set(IDENTITY) | {'document_sha256', 'source_pdf_sha256',
                               'style_sha256', 'script_sha256', 'title'}
UNIT_IDS = (tuple(f'A{i}' for i in range(1, 9))
            + tuple(f'P1-S{i}' for i in range(1, 6)) + ('P2-S1',)
            + tuple(f'T1-S{i}' for i in range(1, 4)) + ('T2-S1', 'T2-S2')
            + tuple(f'P3-S{i}' for i in range(1, 5)) + ('P4-S1', 'P4-S2')
            + tuple(f'P5-S{i}' for i in range(1, 4))
            + ('K1-S1', 'K1-S2', 'K2-S1', 'K2-S2', 'K3-S1',
               'C1-S1', 'C1-S2', 'C2-S1', 'C2-S2'))


class UMIWritingReader(ReportHTML):
    allowed_tags = ALLOWED_TAGS | {'button'}
    tag_attrs = dict(TAG_ATTRS,
                     button={'type', 'disabled', 'data-reader-next', 'data-reader-previous'},
                     span={'data-reader-section-label'}, div={'data-source-row'})

    def __init__(self, filename, paper_id):
        super().__init__(filename, paper_id)
        self.source_rows = []
        self.quote_count = 0
        self.reviewed_style_seen = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'style':
            require(not attrs and not self.reviewed_style_seen,
                    'Only one exact reviewed stylesheet is permitted')
            self.reviewed_style_seen = True
        if tag == 'button':
            require(values.get('type') == 'button', 'Only non-submitting reader controls allowed')
        if 'data-source-row' in values:
            ident = values['data-source-row']
            require(tag == 'div' and values.get('class') == 'source-unit-parallel'
                    and ident in UNIT_IDS and ident not in self.source_rows
                    and values.get('id') == ident, 'Unknown or duplicated UMI writing source unit')
            self.source_rows.append(ident)
        if tag == 'blockquote':
            require(values.get('class') == 'source-excerpt' and values.get('lang') == 'en',
                    'Writing excerpts must retain their explicit English source label')
            self.quote_count += 1
        super().handle_starttag(tag, attrs)

    def close(self):
        super().close()
        require(self.reviewed_style_seen, 'Missing reviewed stylesheet')
        require(tuple(self.source_rows) == UNIT_IDS and self.quote_count == len(UNIT_IDS),
                'UMI writing report requires exactly 37 ordered source units and excerpts')


def prepare(root, record, payload):
    require({key: record.get(key) for key in IDENTITY} == IDENTITY,
            'Unapproved UMI writing reader identity')
    policy = json.loads(_read(root, POLICY_PATH, 20000).decode(), object_pairs_hook=_json_object)
    _keys(policy, POLICY_FIELDS, 'UMI Stage 2 v4 policy')
    require(all(policy[key] == value for key, value in IDENTITY.items()),
            'Wrong paper/stage reader policy')
    for key in ('document_sha256', 'source_pdf_sha256', 'style_sha256', 'script_sha256'):
        _digest(policy[key], 'Reader fingerprint')
    require(record['source_sha256'] == policy['source_pdf_sha256'],
            'Wrong official source PDF fingerprint')
    require(sha(payload) == policy['document_sha256'],
            'Reader document fingerprint differs from content-reviewed policy')
    text = payload.decode('utf-8')
    require(re.findall(r'<title>(.*?)</title>', text, re.S) == [policy['title']],
            'Reader title differs from the approved paper')
    styles = re.findall(r'<style>(.*?)</style>', text, re.S)
    require(len(styles) == 1 and sha(styles[0].encode()) == policy['style_sha256'],
            'Unknown or modified reader stylesheet')
    scripts = re.findall(r'<script>(.*?)</script>', text, re.S)
    require(len(scripts) == 1 and sha(scripts[0].encode()) == policy['script_sha256'],
            'Unknown or modified reader-controls script')
    # Remove only this exact reviewed script. CSS still receives the unchanged
    # resource-free stylesheet checks; unknown scripts and attributes fail closed.
    text = re.sub(r'<script>.*?</script>', '', text, count=1, flags=re.S)
    return text, UMIWritingReader(record['filename'], record['paper_id'])
