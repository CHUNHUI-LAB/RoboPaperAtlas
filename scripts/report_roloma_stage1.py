"""One reviewed RoLoMa formal-version first reading, with passive licensed figures.

This exact-identity importer does not relax any historical report policy. It pins
the document, controls, stylesheet, figure bytes and one macro MathML objective.
"""
import base64
import json
import re
from reports import (ReportHTML, ALLOWED_TAGS, TAG_ATTRS, require, sha, _read,
                     _keys, _digest, _json_object)

IDENTITY = dict(paper_id='rpa-0054', stage='stage1', version='v1', filename='first-pass.html')
POLICY_PATH = 'data/report-rpa-0054-stage1-v1-policy.json'
POLICY_FIELDS = set(IDENTITY) | {'document_sha256', 'source_pdf_sha256',
                               'style_sha256', 'script_sha256', 'title'}
SECTION_IDS = tuple(f'section-{i:02}' for i in range(1, 13))
EVIDENCE_IDS = tuple(f'evidence-E{i:02}' for i in range(1, 13))
# Fixed review fingerprints are filled from the independently reviewed artifact.
MATH_HASH = 'aa49c4773f8a8deb10a45e262603082e64343bcf53a4be24e6df15efdd347533'
IMAGE_HASHES = ('fc87d0d91de9d2f902d1f68d51f3ad35a1067554b5bf7a62454c385ab58cfe11', '32ad20cd8d82cc7750546ff0ea852b79fb90906bfb6d1e1a5af55dadee137c90', '792f3e3f78b94ef191a25a37d3e2a864f92e13ed9a75ae7703a81047dc429cb8', 'ab13428f2d0f8f4a073921694fbc96ec0d02649164932f4228d9d4754f7cdbbc', '1f256e246e015f45f5f79b0dc62396be97f5469c296df416651257b56814be5a', '13f3c642cfb2d56533cd0e84a850ce4f54409c0c9bd834e705097660d88c7b93', '431217928a4c6ae281e021c4b6c1be460166aedecf3f8b1771928cd568c73f2c', 'c544ad0ca10145dca7f11e9701d814be8f0e34708f3aed5c8f48db0b0ca6b85c', 'df461af240deb0b0881641f8601905fa3b09fbd15edd8f97def011ed06cbb0c9', 'cca1caf24b8f8698db2ac754df3a2af1cb889bc6aebbb008b622527d9c9d7782', '2162c926286565ed16ac0a47c1994b14d39f2c019b0d437cce8279dadd11d9d4')
MATH_TAGS = set('math munder munderover msub mrow mtext mi mn mo mspace'.split())

class RoLoMaFirstReader(ReportHTML):
    allowed_tags = (ALLOWED_TAGS - {'blockquote'}) | {'button'} | MATH_TAGS
    tag_attrs = dict(TAG_ATTRS,
        button={'type', 'disabled', 'data-reader-next', 'data-reader-previous'},
        span={'data-reader-section-label'},
        math={'xmlns', 'display'}, mspace={'width'})

    def __init__(self, filename, paper_id):
        super().__init__(filename, paper_id)
        self.section_ids=[]
        self.math_count=self.image_count=self.figure_count=self.input_count=0
        self.summary_count=0
        self.summary_depth=0
        self.reviewed_style_seen=False

    def handle_starttag(self, tag, attrs):
        values=dict(attrs)
        if tag=='style':
            require(not attrs and not self.reviewed_style_seen, 'Only one exact reviewed stylesheet is permitted')
            self.reviewed_style_seen=True
        if tag=='section':
            ident=values.get('id')
            require(ident in SECTION_IDS and ident not in self.section_ids, 'Unknown or duplicate first-reading section')
            self.section_ids.append(ident)
        if tag in MATH_TAGS:
            expected=({'xmlns':'http://www.w3.org/1998/Math/MathML','display':'block'} if tag=='math'
                      else {'width':'0.8em'} if tag=='mspace' else {})
            require(values==expected, 'Unsupported passive math attribute')
            if tag=='math': self.math_count+=1
        if tag=='img': self.image_count+=1
        if tag=='figure': self.figure_count+=1
        if tag=='button': require(values.get('type')=='button', 'Only non-submitting reader controls allowed')
        if tag=='input':
            require(set(values)=={'class','type','id','aria-controls'} and values['type']=='checkbox'
                    and values['class']=='figure-size-switch', 'Only reviewed figure-size checkboxes are allowed')
            n=values['id'].removeprefix('figure-zoom-')
            require(n.isdigit() and 1<=int(n)<=11 and values['id']==f'figure-zoom-{int(n)}'
                    and values['aria-controls']==f'figure-scroll-{n}', 'Unknown image-size control identity')
            self.input_count+=1
        if tag=='ol' and values.get('id')=='evidence-E11': self.summary_depth=1
        elif self.summary_depth:
            if tag=='ol':self.summary_depth+=1
            elif tag=='li' and self.summary_depth==1:self.summary_count+=1
        super().handle_starttag(tag,attrs)

    def handle_endtag(self, tag):
        if tag=='ol' and self.summary_depth:self.summary_depth-=1
        super().handle_endtag(tag)

    def close(self):
        super().close()
        require(self.reviewed_style_seen and tuple(self.section_ids)==SECTION_IDS, 'Missing or reordered first-reading sections')
        require(set(EVIDENCE_IDS)<=self.ids, 'Missing reviewed evidence-unit anchors')
        require((self.math_count,self.image_count,self.figure_count,self.input_count,self.summary_count)==(1,11,11,11,5),
                'First reading requires one formula, eleven licensed figures, eleven passive size controls and exactly five conclusions')


def prepare(root,record,payload):
    require({key:record.get(key) for key in IDENTITY}==IDENTITY, 'Unapproved RoLoMa first-reader identity')
    policy=json.loads(_read(root,POLICY_PATH,20000).decode(),object_pairs_hook=_json_object)
    _keys(policy,POLICY_FIELDS,'RoLoMa Stage 1 v1 policy')
    require(all(policy[key]==value for key,value in IDENTITY.items()), 'Wrong paper/stage reader policy')
    for key in ('document_sha256','source_pdf_sha256','style_sha256','script_sha256'):_digest(policy[key],'Reader fingerprint')
    require(record['source_sha256']==policy['source_pdf_sha256'], 'Wrong formal-paper source fingerprint')
    require(sha(payload)==policy['document_sha256'], 'Reader document fingerprint differs from reviewed policy')
    text=payload.decode('utf-8')
    require(re.findall(r'<title>(.*?)</title>',text,re.S)==[policy['title']], 'Reader title differs from reviewed content')
    styles=re.findall(r'<style>(.*?)</style>',text,re.S)
    require(len(styles)==1 and sha(styles[0].encode())==policy['style_sha256'], 'Unknown or modified reader stylesheet')
    scripts=re.findall(r'<script>(.*?)</script>',text,re.S)
    require(len(scripts)==1 and sha(scripts[0].encode())==policy['script_sha256'], 'Unknown or modified reader-controls script')
    maths=re.findall(r'<math\b.*?</math>',text,re.S)
    require(len(maths)==1 and sha(maths[0].encode())==MATH_HASH, 'MathML differs from reviewed macro objective')
    images=re.findall(r'<img\b[^>]*\bsrc="data:image/jpeg;base64,([A-Za-z0-9+/=]+)"',text)
    require(tuple(sha(base64.b64decode(image,validate=True)) for image in images)==IMAGE_HASHES,
            'Licensed figures differ from reviewed crops or order')
    text=re.sub(r'<script>.*?</script>','',text,count=1,flags=re.S)
    return text,RoLoMaFirstReader(record['filename'],record['paper_id'])
