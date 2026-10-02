"""Narrow, hash-pinned RoboDuet Stage 2 reading; not a general HTML importer.

The source is an explicitly labelled author manuscript. Only two fixed short
quotations (ten English words total) are allowed; neither the source PDF nor a
full sentence corpus is imported. Existing Stage 1 policy remains unchanged.
"""
import json
import re
from reports import (ReportHTML, ALLOWED_TAGS, TAG_ATTRS, require, sha, _read,
                     _keys, _digest, _json_object)

IDENTITY = dict(paper_id='rpa-0052', stage='stage2', version='v1',
                filename='writing-close-reading.html')
POLICY_PATH = 'data/report-rpa-0052-stage2-v1-policy.json'
POLICY_FIELDS = set(IDENTITY) | {'document_sha256', 'source_pdf_sha256',
                               'style_sha256', 'script_sha256', 'title'}
SECTION_IDS = ('structure', 'abstract', 'introduction', 'gap-insight',
               'conclusion', 'other-sections', 'language', 'skeleton')
UNIT_IDS = (tuple(f'A{i}' for i in range(1, 6))
            + tuple(f'P1-S{i}' for i in range(1, 6))
            + tuple(f'P2-S{i}' for i in range(1, 7))
            + tuple(f'P3-S{i}' for i in range(1, 4))
            + tuple(f'P4-S{i}' for i in range(1, 7))
            + tuple(f'C1-S{i}' for i in range(1, 4))
            + tuple(f'C2-S{i}' for i in range(1, 5)))
QUOTES = ('This distinction restricts the workspace of the arm.', 'We argue')


class RoboDuetWritingReader(ReportHTML):
    allowed_tags = (ALLOWED_TAGS - {'img'}) | {'button'}
    tag_attrs = dict(TAG_ATTRS,
                     button={'type', 'disabled', 'data-reader-next', 'data-reader-previous'},
                     span={'data-reader-section-label'},
                     div={'data-source-row'}, blockquote={'data-verbatim'})

    def __init__(self, filename, paper_id):
        super().__init__(filename, paper_id)
        self.source_rows = []
        self.section_ids = []
        self.quotes = []
        self.in_quote = False
        self.quote_text = []
        self.reviewed_style_seen = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'style':
            require(not attrs and not self.reviewed_style_seen,
                    'Only one exact reviewed stylesheet is permitted')
            self.reviewed_style_seen = True
        if tag == 'section':
            ident = values.get('id')
            require(ident in SECTION_IDS and ident not in self.section_ids,
                    'Unknown or duplicate RoboDuet writing section')
            self.section_ids.append(ident)
        if tag == 'button':
            require(values.get('type') == 'button', 'Only non-submitting reader controls allowed')
        if 'data-source-row' in values:
            ident = values['data-source-row']
            require(tag == 'div' and values.get('class') == 'source-unit-parallel'
                    and ident in UNIT_IDS and ident not in self.source_rows
                    and values.get('id') == ident, 'Unknown or duplicate RoboDuet source unit')
            self.source_rows.append(ident)
        if tag == 'blockquote':
            require(not self.in_quote and values.get('class') == 'source-excerpt'
                    and values.get('lang') == 'en' and values.get('data-verbatim') == 'paper',
                    'Only explicitly labelled RoboDuet short quotations are permitted')
            self.in_quote = True
            self.quote_text = []
        elif self.in_quote:
            raise ValueError('Short quotations must contain plain text only')
        super().handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self.in_quote:
            self.quote_text.append(data)
        super().handle_data(data)

    def handle_endtag(self, tag):
        if tag == 'blockquote':
            require(self.in_quote, 'Unexpected short-quotation end')
            self.quotes.append(''.join(self.quote_text))
            self.in_quote = False
            self.quote_text = []
        super().handle_endtag(tag)

    def close(self):
        super().close()
        require(self.reviewed_style_seen, 'Missing reviewed stylesheet')
        require(tuple(self.section_ids) == SECTION_IDS, 'Missing or reordered writing sections')
        require(tuple(self.source_rows) == UNIT_IDS, 'Missing or reordered RoboDuet source units')
        require(not self.in_quote and tuple(self.quotes) == QUOTES
                and sum(len(q.split()) for q in self.quotes) == 10,
                'RoboDuet permits only the two fixed short quotations totalling ten words')


def prepare(root, record, payload):
    require({key: record.get(key) for key in IDENTITY} == IDENTITY,
            'Unapproved RoboDuet writing reader identity')
    policy = json.loads(_read(root, POLICY_PATH, 20000).decode(), object_pairs_hook=_json_object)
    _keys(policy, POLICY_FIELDS, 'RoboDuet Stage 2 v1 policy')
    require(all(policy[key] == value for key, value in IDENTITY.items()),
            'Wrong paper/stage reader policy')
    for key in ('document_sha256', 'source_pdf_sha256', 'style_sha256', 'script_sha256'):
        _digest(policy[key], 'Reader fingerprint')
    require(record['source_sha256'] == policy['source_pdf_sha256'],
            'Wrong author-manuscript source fingerprint')
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
    # Strip only this exact pinned control script; preserve all common HTML,
    # CSS, URL, source-unit and short-quotation guards in the returned parser.
    text = re.sub(r'<script>.*?</script>', '', text, count=1, flags=re.S)
    return text, RoboDuetWritingReader(record['filename'], record['paper_id'])
