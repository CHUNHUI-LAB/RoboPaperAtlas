"""Exact Stage 1 contracts: historical preview v1 and separate canonical v2.

V2 hashes define proposed acceptance boundaries, not completed approval gates.

This additive policy preserves all prior identities and exact v1 frozen bytes.
Only the existing, exact hash-pinned reader-controls script is removed for the
passive HTML check; CSS/URL/attribute/image checks are inherited without change.
"""
import base64,json,re
from reports import ReportHTML,ALLOWED_TAGS,TAG_ATTRS,require,sha,_read,_keys,_digest,_json_object,expected_review_status
IDS=('harnessvln','navharness','holoagent-0')
SOURCES=dict(zip(IDS,('2609.15195v3','2609.34276v1','2606.23565v1')))
POLICY_FIELDS={'paper_id','stage','version','filename','document_sha256','source_pdf_sha256','style_sha256','script_sha256','title'}
SECTION_IDS=tuple(f'section-{i:02}'for i in range(1,13))
MATH_TAGS=set('math mrow msub mi mo mn munderover'.split())
FROZEN={'harnessvln': {'source_pdf_sha256': '3d98a9c26613010599b0c865e1d6cf3e8fe47652c43ff0a0e081e8c4ae8a2ff1', 'script_sha256': 'd6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798', 'math_sha256': ['bca9be6b8148d975dc61e26f36b0778afee33f2dd06ccb1112262ae839751c76'], 'image_sha256': ['ec9bf21b58fe3443d7c271f01420dbc2c4dbb061fd50699b739454de077c7b6e', 'ed1394c65d28f3071e7c7f842161f24584fa0b409cc655b63204f01935275e22', '9f44501cb02757ce464cd0611dac0387de14657298791b13d8c3f8b67c8efbf4', 'eb3f2f1bdaca665a02946b387e63895a1390f53959431a883cc6126e55dad8a0', '8ffa5d77e6579cb7fa1133055df13e6c3e20410510c36e28afb3aa058a9315a1', '3eb7edb706d9c40769557a6c99de1f67a0ddc510b3c199a46e26edf4f38d50b6'], 'section_sha256': ['e8077b9b119f7dbcfcf2932f2c181b22b50b42ab4c9f5ff1f12526bfdcb2f802', 'e8021a3de951bc31e4cb7e7536109e1033b02c1c4098d73df6305f7cfba8027c', 'ddeb791682944a4553872d4ea47f579afa024b247889896b3f796f358ec734f2', '21d2efcf58b3260e27349322e342533eff3d112479d5b9a58988808d6b2bde6f', '08a9c6480691449bf3065f7897a0f6955ff9f887ac98bb9afd3df7caea338f8b', '45fe9751225d6bcc8d292e213ed83a83c09341798a0e8d44b2703d744f1c6a0b', '1f210cc4053e751be10005b0be328d05a6c2abbdfad6d9a5877742e715e18cc0', '80607521d2e0d8aef978736704b31a94c5c42374ca43c74ed2c8f767c0b074a7', '29df65457588045eb5f02fb00b4d9f1e2de6c9f0d05d645ae04ed170c58cca7d', 'd293887fcbfad883404d94ff622507bf58b6156a8974d652c437c9f6bfca32f4', '796cbedd87999300aee66b0944ccd5603a9129d794cf4a551382cb93ecf8de43', '515b85b45623c3e4083fe5b7618b1b95b30d08cb9224a55b1f2aff58ba3df584'], 'figure_ids': ['figure-2', 'figure-4', 'figure-3', 'figure-9', 'figure-10', 'figure-11'], 'input_ids': ['zoom-figure-2', 'zoom-figure-4', 'zoom-figure-3', 'zoom-figure-9', 'zoom-figure-10', 'zoom-figure-11'], 'evidence_ids': [], 'table_count': 13}, 'navharness': {'source_pdf_sha256': 'e98379dd46c4f4cb573d6c4352bb59362c17b6c59043cee1201d44dbc2b49fe0', 'script_sha256': 'd6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798', 'math_sha256': [], 'image_sha256': ['c93b17d35e754765bb26d53efb6923da25b25e91fd80ac0b308998c1553cf84c', '82a27dce3cfb013045f31a73f46314f7bec105f7cc1c96aee33c06650a016a27', '3830497d481e2fe1b5fd1aef3215e183e10c681b2082ce572241225eb173621b', 'f523dfb568a2985d6f9b49d6016208844122e3aa8adc2526888aeff4901c2078'], 'section_sha256': ['4391cf26ed29ce868098ce28f9435266ab0589de3790680c3fc536d36faff096', 'fc7c8751ae3cf55fcc47bea39eb7211b9f910b5ed80c953b7b31f8e7bd892185', '5b46ca7fa724411c1b6a81a2bae0b811e296471bd481c0c60ac05532d5baaa9f', '584e2a917146b9685e921bcf80d930a7fd330f0177fb0d0f772c6f1954843242', 'd830c27d962bba460286eb3ab2d5fe4eb36071914d7b7e7fcde08d31dc9ca167', '8488909a29981083423d53d55c73125fead5212c600956628c28ea7cf2fc222d', 'a993437b3c9abc740d2fa9a9e357cd78e8c4243cd9ecddb024f38963939f8141', '6d47319dcb452576e1eaf210a3a442b3735b3e76a5cc87f971109d42d7cf44a7', '571aef9da3464fcc2815316fcca87b6a20e38de938a5bf639f607f7d1f139d7b', '82c76ef708d8ede1cbebdd5bfcab37c5b360406ffe957b2976ff2b223c3a8b80', '33025f09e43ac2eff9923c641d70b6a062385de736e0fdd744acbcb3e8e799a5', '01507de5395cec6d1d9db40001f42cb5148aa2a861a0b8b680a2b2839c478268'], 'figure_ids': ['fig-framework', 'fig-ablation', 'fig-consolidation', 'fig-false-memory'], 'input_ids': ['zoom-fig-framework', 'zoom-fig-ablation', 'zoom-fig-consolidation', 'zoom-fig-false-memory'], 'evidence_ids': [], 'table_count': 8}, 'holoagent-0': {'source_pdf_sha256': 'ccd10a1e1ecbcd7d14b1da234539dbf3c5cb8135845dc602dd9946a54bb4f7ca', 'script_sha256': 'd6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798', 'math_sha256': ['3257bb244e2197852e683822c98b9b6f38badea76c3a114e3cbb7b85cd283e1e'], 'image_sha256': [], 'section_sha256': ['b60097a2a8402c8ca2ab7ab15057af03dc696ee436fdbfa5c21da2ab70c95487', '52dc6282ea6c7f3e07b15ded47f426598447346b82b52420057cdbf276d78bde', '191d5637bb30786add468462995f4f685ed0ab3bd76b7c06ed03ecf925dcec13', '9e9a0c1c5f39a18ff35e754e5e8211d8211d3d0eba111c136c72fd49f31847ce', '3fcc98f0d111bf562f4abed9010660378a7a200c0c989e5e5478288a2f78956f', '01fd579e57e062f5fe4e7c3c81b7b527e2cd71b7881f538acaf6e980afee959c', 'a0ed63ebc56d0edee0588b5e08def2ed49c132c137bcfc0a328f40f59cee9fd6', '2e8accf3db2fbb89a5a1a7ae2920d2d4331aba66b6bcca8769824210eb36d013', '5cdeb6e3c0a146d61b4e1310e999c73b6265ecbfbd2e81d2ec105d976f35b394', 'b9ea60be3ad270695fa129b9928f5f438da3eb7ae90c6fedff5f689420fa404b', '16b9230a2d3d4d060ab08b88b08cb903d8669261df77f8a615548111c2a4c7bf', '51a51820a4f4a113df4f5d39439c235ff43b0055bafd0f15cfe4fb61806a814d'], 'figure_ids': [], 'input_ids': [], 'evidence_ids': ['figure-1', 'figure-3', 'figure-4', 'figure-6', 'figure-7', 'figure-5', 'figure-8', 'figure-2'], 'table_count': 8}}

# The v2 candidate contract is independent of the immutable v1 preview pins.
EDITIONS = {'harnessvln': 'arXiv:2609.15195v3; explicitly requested preprint, official publication not verified', 'navharness': 'arXiv:2609.34276v1; explicitly requested preprint, official publication not verified', 'holoagent-0': 'arXiv:2606.23565v1; explicitly requested preprint, official publication not verified'}
V2_DOCUMENT_SHA256 = {'harnessvln': '83bd72851dd8ff67bb6c7dd56ef492848cabdf279481b3f4147070fead96fff2', 'navharness': '279d81743598ef2b1b2b95c4c1abc7b3197b5a296718891310a92f70db465fb5', 'holoagent-0': '8e10161884ccc7cea77ca6a98da6cef3829e6049635ea9923e8f5ed27acbd9b5'}
V2_SECTION_UPDATES = {'harnessvln': {4: 'd3f1a31b1efe1eff14fc73f04dea87977e9a23c6a583fac3fda6ac141b2f2327', 6: 'f1d66b1cc4c269e860a2091a22b571433674c377d5313e6e365c543f9038f138'}, 'navharness': {1: '3f727e61f89652b17a58ae6333c4d01186389518110b3002be1922fc9acd55c6', 7: 'dc2669ec85ca5954630b721e0f72647e6c03299003799c9266693e80d0aeaad3'}, 'holoagent-0': {2: '68467b9d65c0003bbd83a3c74e4d88ba76ef45de91e15ffb93a1e8e9a0b268f0', 3: '17b62d86e93243e793091b94f885f4b36aba8c1e197ee8f14dc61450ce8531eb', 4: '830e702fd81de97f8468adb7587e0a7b53b7095e955ec6bb07bb3d61f18cfc2d', 6: '43385935ea8a976cc8ed2d764fc49ececf4a368f58608096636c9c8eb1f984e6'}}
V2_IMAGE_UPDATES = {'harnessvln': ['ec9bf21b58fe3443d7c271f01420dbc2c4dbb061fd50699b739454de077c7b6e', '4c3b57022a08bd26c5c7ff8e14028913ea57513ff42bd82f2c25b2e2600038f0', 'ed1394c65d28f3071e7c7f842161f24584fa0b409cc655b63204f01935275e22', '9f44501cb02757ce464cd0611dac0387de14657298791b13d8c3f8b67c8efbf4', 'eb3f2f1bdaca665a02946b387e63895a1390f53959431a883cc6126e55dad8a0', '8ffa5d77e6579cb7fa1133055df13e6c3e20410510c36e28afb3aa058a9315a1', '3eb7edb706d9c40769557a6c99de1f67a0ddc510b3c199a46e26edf4f38d50b6'], 'navharness': ['c93b17d35e754765bb26d53efb6923da25b25e91fd80ac0b308998c1553cf84c', '82a27dce3cfb013045f31a73f46314f7bec105f7cc1c96aee33c06650a016a27', '3830497d481e2fe1b5fd1aef3215e183e10c681b2082ce572241225eb173621b', 'f523dfb568a2985d6f9b49d6016208844122e3aa8adc2526888aeff4901c2078'], 'holoagent-0': ['8abc40ae62ba5be877817a0d560b84f3d69325abb982319477594885cebe7a53']}
V2_FROZEN = {pid: dict(FROZEN[pid], document_sha256=digest, image_sha256=V2_IMAGE_UPDATES[pid], section_sha256=[V2_SECTION_UPDATES[pid].get(i, value) for i, value in enumerate(FROZEN[pid]['section_sha256'])]) for pid, digest in V2_DOCUMENT_SHA256.items()}

def frozen_spec(paper_id, version):
    require(paper_id in IDS and version in ('v1', 'v2'), 'Unknown navigation Stage 1 version')
    return (FROZEN if version == 'v1' else V2_FROZEN)[paper_id]

class NavigationFirstReader(ReportHTML):
    allowed_tags=(ALLOWED_TAGS-{'blockquote'})|{'button'}|MATH_TAGS
    tag_attrs=dict(TAG_ATTRS,button={'type','disabled','data-reader-next','data-reader-previous'},span={'data-reader-section-label'},math={'xmlns','display'},mi={'mathvariant'})
    def __init__(self,filename,paper_id,version='v1'):
        require(paper_id in IDS,'Unknown navigation Stage 1 identity')
        super().__init__(filename,paper_id)
        self.pid=paper_id;self.frozen=frozen_spec(paper_id,version);self.section_ids=[];self.figure_ids=[];self.input_ids=[];self.evidence_ids=[]
        self.math_count=self.image_count=self.table_count=self.summary_count=0
        self.in_summary=False;self.reviewed_style_seen=False
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag=='style':
            require(not attrs and not self.reviewed_style_seen,'Only one reviewed stylesheet is permitted')
            self.reviewed_style_seen=True
        if tag=='section':
            self.section_ids.append(values.get('id'));self.in_summary=values.get('id')=='section-11'
        if self.in_summary and tag=='li':self.summary_count+=1
        if tag=='figure':self.figure_ids.append(values.get('id'))
        if tag=='div' and values.get('class')=='evidence-card':self.evidence_ids.append(values.get('id'))
        if tag=='img':self.image_count+=1
        if tag=='table':self.table_count+=1
        if tag=='button':require(values.get('type')=='button','Only non-submitting reader controls allowed')
        if tag=='input':
            require(set(values)=={'class','type','id','aria-controls'} and values['type']=='checkbox' and values['class']=='figure-size-switch','Only reviewed passive image controls allowed')
            figure=values['id'].removeprefix('zoom-')
            require(figure in self.frozen['figure_ids'] and values['id']=='zoom-'+figure and values['aria-controls']=='scroll-'+figure,'Unknown passive image-control identity')
            self.input_ids.append(values['id'])
        if tag in MATH_TAGS:
            expected=({'xmlns':'http://www.w3.org/1998/Math/MathML','display':'block'} if tag=='math' else {'mathvariant':'bold'} if tag=='mi' and values else {})
            require(values==expected,'Unsupported passive MathML attribute')
            if tag=='math':self.math_count+=1
        super().handle_starttag(tag,attrs)
    def handle_endtag(self,tag):
        if tag=='section':self.in_summary=False
        super().handle_endtag(tag)
    def close(self):
        super().close();f=self.frozen
        require(self.reviewed_style_seen and tuple(self.section_ids)==SECTION_IDS,'Missing, duplicate or reordered Stage 1 sections')
        require(self.summary_count==5,'Exactly five closing conclusions required')
        require(self.figure_ids==f['figure_ids'] and self.input_ids==f['input_ids'] and self.evidence_ids==f['evidence_ids'],'Unknown or reordered figure/control/evidence identities')
        require(self.image_count==len(f['image_sha256']) and self.math_count==len(f['math_sha256']) and self.table_count==f['table_count'],'Unexpected image, formula or table count')

def prepare(root,record,payload):
    require(record.get('review_status')==expected_review_status(record),'Wrong exact-version navigation review state')
    return _prepare_exact(root,record,payload)


def prepare_candidate_v2(root,record,payload):
    """Dedicated pending-v2 boundary; never relabel or register a candidate."""
    from reports import _validate_record_fields
    _validate_record_fields(record)
    require(record['paper_id'] in IDS and record['stage']=='stage1' and record['version']=='v2' and record['filename']=='first-pass.html' and record['review_status']=='pending_candidate','Wrong exact v2 candidate context/state')
    require(isinstance(payload,bytes) and len(payload)==record['bytes'] and sha(payload)==record['sha256'],'V2 candidate source fingerprint differs')
    return _prepare_exact(root,record,payload)


def _prepare_exact(root,record,payload):
    pid=record.get('paper_id')
    version=record.get('version')
    require(pid in IDS and version in ('v1','v2') and record.get('stage')=='stage1' and record.get('filename')=='first-pass.html','Unapproved navigation report identity')
    require(record.get('source_edition')==EDITIONS[pid],'Wrong specified navigation-paper edition label')
    require(record['source_url']==f'https://arxiv.org/abs/{SOURCES[pid]}' and record['pdf_url']==f'https://arxiv.org/pdf/{SOURCES[pid]}','Wrong specified navigation-paper edition')
    policy=json.loads(_read(root,f'data/report-{pid}-stage1-{version}-policy.json',20000).decode(),object_pairs_hook=_json_object)
    _keys(policy,POLICY_FIELDS,'Navigation Stage 1 preview policy')
    require({k:policy[k]for k in ('paper_id','stage','version','filename')}==dict(paper_id=pid,stage='stage1',version=version,filename='first-pass.html'),'Wrong navigation report policy')
    for key in ('document_sha256','source_pdf_sha256','style_sha256','script_sha256'):_digest(policy[key],'Reader fingerprint')
    f=frozen_spec(pid,version)
    if version=='v2':require(sha(payload)==f['document_sha256'],'V2 document differs from exact code-pinned candidate bytes')
    require(record['source_sha256']==policy['source_pdf_sha256']==f['source_pdf_sha256'],'Wrong source PDF fingerprint')
    require(sha(payload)==policy['document_sha256'],'Reader document fingerprint differs from preview policy')
    text=payload.decode('utf-8')
    require(re.findall(r'<title>(.*?)</title>',text,re.S)==[policy['title']],'Reader title differs')
    styles=re.findall(r'<style>(.*?)</style>',text,re.S)
    require(len(styles)==1 and sha(styles[0].encode())==policy['style_sha256'],'Unknown or modified stylesheet')
    scripts=re.findall(r'<script>(.*?)</script>',text,re.S)
    require(len(scripts)==1 and sha(scripts[0].encode())==policy['script_sha256']==f['script_sha256'],'Unknown or modified reader-controls script')
    maths=re.findall(r'<math\b.*?</math>',text,re.S)
    require([sha(m.encode())for m in maths]==f['math_sha256'],'Passive MathML differs from checked equations')
    images=re.findall(r'<img\b[^>]*\bsrc="data:image/(?:png|jpeg);base64,([A-Za-z0-9+/=]+)"',text)
    require([sha(base64.b64decode(i,validate=True))for i in images]==f['image_sha256'],'Licensed images differ from checked bytes/order')
    sections=re.findall(r'<section\b.*?</section>',text,re.S)
    require([sha(section.encode())for section in sections]==f['section_sha256'],'Scientific sections differ from exact version-pinned content')
    text=re.sub(r'<script>.*?</script>','',text,count=1,flags=re.S)
    return text,NavigationFirstReader(record['filename'],pid,version)
