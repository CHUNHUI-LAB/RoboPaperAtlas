"""Explicitly reviewed Deep WBC Stage 1/2/3 documents, not a general HTML uploader.

The content approval does not claim browser QA. Whole-document and reader-script
fingerprints are required before parsing the remaining HTML with all existing
CSS, image, attribute, URL, fragment and path guards intact.
"""
import json
import re
from reports import ReportHTML, ALLOWED_TAGS, TAG_ATTRS, require, sha, _read, _keys, _digest, _json_object

POLICY_FIELDS = {'paper_id', 'stage', 'version', 'filename', 'document_sha256',
                 'script_sha256', 'source_pdf_sha256', 'title'}

class DeepWBCReader(ReportHTML):
    allowed_tags = ALLOWED_TAGS | {'button'}
    tag_attrs = dict(TAG_ATTRS, button={'type', 'disabled', 'data-reader-next', 'data-reader-previous'},
                     span={'data-reader-section-label'})

    def handle_starttag(self, tag, attrs):
        if tag == 'button':
            require(dict(attrs).get('type') == 'button', 'Only non-submitting reader controls allowed')
        super().handle_starttag(tag, attrs)


WRITING_UNIT_IDS = ({f'A{i}' for i in range(1, 10)}
                    | {f'P{p}-S{i}' for p,n in enumerate((6,7,6,3,9),1) for i in range(1,n+1)}
                    | {f'C1-S{i}' for i in range(1,6)})
POLICY_PATHS = {
    ('stage1','v1','first-pass.html'): 'data/report-rpa-0012-v1-policy.json',
    ('stage1','v2','first-pass.html'): 'data/report-rpa-0012-v2-policy.json',
    ('stage2','v1','writing-close-reading.html'): 'data/report-rpa-0012-stage2-v1-policy.json',
    ('stage3','v1','method-code-reading.html'): 'data/report-rpa-0012-stage3-v1-policy.json',
}

class DeepWBCWritingReader(DeepWBCReader):
    tag_attrs = dict(DeepWBCReader.tag_attrs, div={'data-source-row'})

    def __init__(self, filename, paper_id):
        super().__init__(filename, paper_id)
        self.source_rows = set()
        self.quote_count = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if 'data-source-row' in values:
            ident = values['data-source-row']
            require(tag == 'div' and ident in WRITING_UNIT_IDS and ident not in self.source_rows,
                    'Unknown or duplicated Deep WBC writing source unit')
            self.source_rows.add(ident)
        if tag == 'blockquote':
            require(values.get('class') == 'source-excerpt' and values.get('lang') == 'en',
                    'Writing excerpts must retain their explicit English source label')
            self.quote_count += 1
        super().handle_starttag(tag, attrs)

    def close(self):
        super().close()
        require(self.source_rows == WRITING_UNIT_IDS and self.quote_count == 45,
                'Deep WBC writing report requires exactly 45 reviewed source units and excerpts')


def prepare(root, record, payload):
    identity = {k:record[k] for k in ('paper_id','stage','version','filename')}
    key = (identity['stage'], identity['version'], identity['filename'])
    require(identity['paper_id'] == 'rpa-0012' and key in POLICY_PATHS,
            'Unapproved Deep WBC reader identity')
    policy = json.loads(_read(root, POLICY_PATHS[key], 20000).decode(),
                        object_pairs_hook=_json_object)
    _keys(policy, POLICY_FIELDS | ({'style_sha256'} if record['stage'] == 'stage3' else set()), 'Deep WBC policy')
    require(all(policy[k] == v for k,v in identity.items()), 'Wrong paper/stage reader policy')
    for key in ('document_sha256','script_sha256','source_pdf_sha256'):
        _digest(policy[key], 'Reader fingerprint')
    require(record['source_sha256'] == policy['source_pdf_sha256'], 'Wrong official source PDF fingerprint')
    require(sha(payload) == policy['document_sha256'], 'Reader document fingerprint differs from content-reviewed policy')
    text=payload.decode('utf-8')
    titles=re.findall(r'<title>(.*?)</title>',text,re.S)
    require(titles == [policy['title']], 'Reader title differs from the approved paper')
    scripts=re.findall(r'<script>(.*?)</script>',text,re.S)
    require(len(scripts)==1 and sha(scripts[0].encode())==policy['script_sha256'],
            'Unknown or modified reader-controls script')
    # Only the one exact reviewed script is removed from the strict parser input.
    # Other script tags/attributes remain and are rejected by ReportHTML.
    text=re.sub(r'<script>.*?</script>','',text,count=1,flags=re.S)
    if record['stage'] == 'stage3':
        from report_deep_wbc_method import prepare_style, DeepWBCMethodReader
        return prepare_style(text, policy), DeepWBCMethodReader(record['filename'], record['paper_id'])
    parser = DeepWBCWritingReader if record['stage'] == 'stage2' else DeepWBCReader
    return text,parser(record['filename'],record['paper_id'])
