"""One explicitly reviewed Deep WBC Stage 1 document, not a general HTML uploader.

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


def prepare(root, record, payload):
    identity = {k:record[k] for k in ('paper_id','stage','version','filename')}
    require(identity['version'] in {'v1', 'v2'} and identity == dict(paper_id='rpa-0012',stage='stage1',version=identity['version'],filename='first-pass.html'),
            'Unapproved Deep WBC reader identity')
    policy_path = {'v1': 'data/report-rpa-0012-v1-policy.json', 'v2': 'data/report-rpa-0012-v2-policy.json'}[identity['version']]
    policy = json.loads(_read(root, policy_path, 20000).decode(),
                        object_pairs_hook=_json_object)
    _keys(policy, POLICY_FIELDS, 'Deep WBC policy')
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
    return text,DeepWBCReader(record['filename'],record['paper_id'])
