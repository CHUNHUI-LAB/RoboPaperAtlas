"""Exact reviewed RoboDuet Stage 1 document; no general report upload surface."""
import json
import re
from reports import ReportHTML, ALLOWED_TAGS, TAG_ATTRS, require, sha, _read, _keys, _digest, _json_object

POLICY_FIELDS = {'paper_id','stage','version','filename','document_sha256','script_sha256','source_pdf_sha256','title'}
class RoboDuetReader(ReportHTML):
    allowed_tags = ALLOWED_TAGS | {'button'}
    tag_attrs = dict(TAG_ATTRS, button={'type','disabled','data-reader-next','data-reader-previous'}, span={'data-reader-section-label'})
    def handle_starttag(self,tag,attrs):
        if tag == 'button':
            require(dict(attrs).get('type') == 'button','Only non-submitting reader controls allowed')
        super().handle_starttag(tag,attrs)

def prepare(root,record,payload):
    identity = {k:record[k] for k in ('paper_id','stage','version','filename')}
    require(identity == dict(paper_id='rpa-0052',stage='stage1',version='v1',filename='first-pass.html'),'Unapproved RoboDuet reader identity')
    policy=json.loads(_read(root,'data/report-rpa-0052-v1-policy.json',20000).decode(),object_pairs_hook=_json_object)
    _keys(policy,POLICY_FIELDS,'RoboDuet policy')
    require(all(policy[k]==v for k,v in identity.items()),'Wrong paper/stage reader policy')
    for key in ('document_sha256','script_sha256','source_pdf_sha256'):_digest(policy[key],'Reader fingerprint')
    require(record['source_sha256']==policy['source_pdf_sha256'],'Wrong author-manuscript source fingerprint')
    require(sha(payload)==policy['document_sha256'],'Reader document fingerprint differs from content-reviewed policy')
    text=payload.decode('utf-8')
    require(re.findall(r'<title>(.*?)</title>',text,re.S)==[policy['title']],'Reader title differs from approved paper')
    scripts=re.findall(r'<script>(.*?)</script>',text,re.S)
    require(len(scripts)==1 and sha(scripts[0].encode())==policy['script_sha256'],'Unknown or modified reader-controls script')
    # Remove only the exact hash-pinned interaction script; retain all other guards.
    text=re.sub(r'<script>.*?</script>','',text,count=1,flags=re.S)
    return text,RoboDuetReader(record['filename'],record['paper_id'])
