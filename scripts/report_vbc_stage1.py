"""Exact reviewed VBC Stage 1; other report identities and policies stay closed."""
import base64
import json
import re
from reports import (ReportHTML, ALLOWED_TAGS, TAG_ATTRS, require, sha, _read,
                     _keys, _digest, _json_object)

IDENTITY = dict(paper_id='rpa-0067', stage='stage1', version='v1', filename='first-pass.html')
POLICY_PATH = 'data/report-rpa-0067-stage1-v1-policy.json'
POLICY_FIELDS = set(IDENTITY) | {'document_sha256', 'source_pdf_sha256',
                               'style_sha256', 'script_sha256', 'title'}
SECTION_IDS = tuple(f'section-{i:02}' for i in range(1, 13))
EVIDENCE_IDS = tuple(f'evidence-E{i:02}' for i in range(1, 11))
FIGURE_IDS = ('figure-01', 'figure-02', 'figure-03', 'figure-05', 'figure-13',
              'table-01', 'figure-06', 'figure-07', 'table-04', 'table-05')
# Image hashes are filled from the independently checked, unchanged crops.
IMAGE_HASHES = ('35dbcc6f0fae43a107a8e3a507325968a521dfce7d376a8f85f9c3950bd4cfa3', '33680a3f71875d47c8478ce4b42ea66fcd55b0415fc56ef1865777a6a05613c5', '3dd785847eef1f41977726b5e21d867e694f707827c4cce34a45dda5413ecf30', '7755352b58d03e2df09a73564e1a0fd7d7e6cea37c2849f4134794ab309ae4a0', '8d6baf38b005bcb9a4d1155c2c0fb5e88f0624086b2c63cd91ea2bf5a74e3e6a', '35c141cfc1badd0939562f89f3d94be78d7b51926c36770c65803aba7946b798', '4377147aafec578b61eb1c7479de1c66c2c091b227cddbfefd487f5c6a73c606', '50cb9ed0a97a877aba1d2c21a53bcd1dad8c13a2dafbf88707089982233416c2', '0351c2368551f3a01425e89814c52056af66ac42fef2620a444c7f6b58d73005', 'cd5147b791c5a8675bd55fdaa6c51b6be6fe296988be9ddab3130ee19bd21d41')


class VBCFirstReader(ReportHTML):
    allowed_tags = (ALLOWED_TAGS - {'blockquote'}) | {'button'}
    tag_attrs = dict(TAG_ATTRS,
        button={'type', 'disabled', 'data-reader-next', 'data-reader-previous'},
        span={'data-reader-section-label'})

    def __init__(self, filename, paper_id):
        super().__init__(filename, paper_id)
        self.section_ids=[]
        self.figure_ids=[]
        self.image_count=self.input_count=self.summary_count=self.summary_depth=0
        self.reviewed_style_seen=False

    def handle_starttag(self, tag, attrs):
        values=dict(attrs)
        if tag=='style':
            require(not attrs and not self.reviewed_style_seen, 'Only one exact reviewed stylesheet is permitted')
            self.reviewed_style_seen=True
        if tag=='section':
            ident=values.get('id')
            require(ident in SECTION_IDS and ident not in self.section_ids, 'Unknown or duplicate VBC first-reading section')
            self.section_ids.append(ident)
        if tag=='figure':
            ident=values.get('id')
            require(ident in FIGURE_IDS and ident not in self.figure_ids, 'Unknown or duplicate VBC figure identity')
            self.figure_ids.append(ident)
        if tag=='img':self.image_count+=1
        if tag=='button':require(values.get('type')=='button', 'Only non-submitting reader controls allowed')
        if tag=='input':
            require(set(values)=={'class','type','id','aria-controls'} and values['type']=='checkbox'
                    and values['class']=='figure-size-switch', 'Only reviewed figure-size checkboxes are allowed')
            ident=values['id'].removeprefix('zoom-')
            require(ident in FIGURE_IDS and values['id']=='zoom-'+ident
                    and values['aria-controls']=='scroll-'+ident, 'Unknown VBC image-size control identity')
            self.input_count+=1
        if tag=='ol' and values.get('id')=='five-takeaways':self.summary_depth=1
        elif self.summary_depth:
            if tag=='ol':self.summary_depth+=1
            elif tag=='li' and self.summary_depth==1:self.summary_count+=1
        super().handle_starttag(tag,attrs)

    def handle_endtag(self, tag):
        if tag=='ol' and self.summary_depth:self.summary_depth-=1
        super().handle_endtag(tag)

    def close(self):
        super().close()
        require(self.reviewed_style_seen and tuple(self.section_ids)==SECTION_IDS, 'Missing or reordered VBC first-reading sections')
        require(set(EVIDENCE_IDS)<=self.ids, 'Missing reviewed VBC evidence anchors')
        require(tuple(self.figure_ids)==FIGURE_IDS, 'Missing or reordered VBC figures')
        require((self.image_count,self.input_count,self.summary_count)==(10,10,5),
                'VBC first reading requires ten licensed crops, ten passive image controls and five conclusions')


def prepare(root,record,payload):
    require({key:record.get(key) for key in IDENTITY}==IDENTITY, 'Unapproved VBC first-reader identity')
    policy=json.loads(_read(root,POLICY_PATH,20000).decode(),object_pairs_hook=_json_object)
    _keys(policy,POLICY_FIELDS,'VBC Stage 1 v1 policy')
    require(all(policy[key]==value for key,value in IDENTITY.items()), 'Wrong VBC reader policy')
    for key in ('document_sha256','source_pdf_sha256','style_sha256','script_sha256'):_digest(policy[key],'Reader fingerprint')
    require(record['source_sha256']==policy['source_pdf_sha256'], 'Wrong VBC formal-paper source fingerprint')
    require(sha(payload)==policy['document_sha256'], 'Reader document fingerprint differs from reviewed policy')
    text=payload.decode('utf-8')
    require(re.findall(r'<title>(.*?)</title>',text,re.S)==[policy['title']], 'Reader title differs from reviewed content')
    styles=re.findall(r'<style>(.*?)</style>',text,re.S)
    require(len(styles)==1 and sha(styles[0].encode())==policy['style_sha256'], 'Unknown or modified reader stylesheet')
    scripts=re.findall(r'<script>(.*?)</script>',text,re.S)
    require(len(scripts)==1 and sha(scripts[0].encode())==policy['script_sha256'], 'Unknown or modified reader-controls script')
    images=re.findall(r'<img\b[^>]*\bsrc="data:image/png;base64,([A-Za-z0-9+/=]+)"',text)
    require(tuple(sha(base64.b64decode(image,validate=True)) for image in images)==IMAGE_HASHES,
            'Licensed VBC figures differ from reviewed crops or order')
    text=re.sub(r'<script>.*?</script>','',text,count=1,flags=re.S)
    return text,VBCFirstReader(record['filename'],record['paper_id'])
