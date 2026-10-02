"""One reviewed RoboDuet method reader: fixed sources and passive offline content.

This is a narrow importer for one report identity, not a general SVG/MathML or
JavaScript allowlist. Historical report security policies remain unchanged.
"""
import json
import re
from reports import (ReportHTML, ALLOWED_TAGS, TAG_ATTRS, require, sha, _read,
                     _keys, _digest, _json_object)

IDENTITY = dict(paper_id='rpa-0052', stage='stage3', version='v1',
                filename='method-code-reading.html')
POLICY_PATH = 'data/report-rpa-0052-stage3-v1-policy.json'
POLICY_FIELDS = set(IDENTITY) | {'document_sha256', 'source_pdf_sha256',
                               'style_sha256', 'script_sha256', 'title'}
SECTION_IDS = ('framework', 'mapping', 'observations', 'cooperation', 'control', 'rewards', 'inference', 'summary')
SVG_HASH = 'd997d1a8c7cd3dc46466ad29b5baede9efe632bf93df3414eac884430ece31f3'
MATH_HASHES = ('2d73ebac5f4354f8228a65474e7cabce63a27751800ad77bca123b94adf31dfd', '7d9e248a10ec504df8210ce320e86584ee16528cf5c8ee5f3dc176ba3cba8fb5', 'e68723fd7fd745dd2c463aa395b9c1c07057f9c486fd5cc3c9289ab34c8a49ea', 'c986dbf9ec2eff281cb658edbc019cf83b9676d955d071238cfeee4419d2af4b', '9fbbbf5a84e0e70af6c1bf8729b81fff930bd72fd27439431f134cd6aca33e47', '194177976e13079583b5705ef46cc447b35fb735aea6101c656d37eedbc77b46', 'b539f2930e5b0cb7120a2c839847ec8a6845d1e50bf6f068651c4017d9713599', 'bd1b029e56a74d3e5e49e3142268912a75e47978e703cd8b293386b32740a3bc', 'bf8181914fedb47e50642b8d797806cfaf6757090fd0e2d49c9d608622419d87', '4aa70fd58a2896792c20a14ddc3167f929b3b7905e3c7917cd3e9be42db2176b', 'af496c15f2c7e532afbc33f9c54ed8496f5a9f84c4a29b9453e8c33c239277e4', '76c52b13f82b4a8a3f5bbce727fcf8ecf27ac16b0d0552cf69d037ceadd232b9', '0b9c84c5ca31bbc8eb4a4212226c4af28a2190c5a01649190159e62ffbfe6af3', '4ef63c21647f0ab2df3501cfc7fcd7c3a814a86f65c4518b3fc34455614a8bdd')
CODE_LINES_HASH = '43b2c4d2ebe135b9981742d9f70a8c05dca535ca965425780b4b9fdfe278ceeb'
SVG_ATTRS = {'desc': {'id': ['flow-desc']},
 'g': {'fill': ['#26394b'], 'font-family': ['sans-serif'], 'font-size': ['17']},
 'marker': {'id': ['arrow'],
            'markerheight': ['8'],
            'markerwidth': ['8'],
            'orient': ['auto'],
            'refx': ['7'],
            'refy': ['4']},
 'path': {'d': ['M0 0L8 4L0 8',
                'M130 261V303',
                'M242 222H287',
                'M405 188V327',
                'M516 150H585',
                'M692 302V327',
                'M693 188V214'],
          'fill': ['#58786b', 'none'],
          'marker-end': ['url(#arrow)'],
          'stroke': ['#58786b'],
          'stroke-width': ['2']},
 'rect': {'fill': ['#edf4f0', '#f6f8fb', '#faf8fd', '#fff'],
          'height': ['394', '488', '69', '71', '74', '78'],
          'rx': ['12', '14', '9'],
          'stroke': ['#80b39c', '#b39bd4', '#c0d6c8', '#d4c9e6'],
          'width': ['170', '198', '210', '212', '487', '531', '850'],
          'x': ['26', '292', '314', '46', '589'],
          'y': ['113', '183', '219', '333', '58']},
 'svg': {'aria-labelledby': ['flow-title flow-desc'],
         'role': ['img'],
         'viewbox': ['0 0 850 488'],
         'xmlns': ['http://www.w3.org/2000/svg']},
 'text': {'fill': ['#637187'],
          'font-size': ['14', '15'],
          'font-weight': ['600'],
          'x': ['28', '312', '317', '332', '336', '424', '46', '47', '49', '606', '66'],
          'y': ['126',
                '141',
                '155',
                '168',
                '212',
                '238',
                '249',
                '263',
                '278',
                '339',
                '34',
                '362',
                '389',
                '420',
                '433',
                '93']},
 'title': {'id': ['flow-title']}}
MATH_TAGS = set('math mtext mi mn mo msup msub mrow msubsup mover munder mtable mtr mtd'.split())
SVG_TAGS = set('svg desc defs marker path rect g text'.split())

class RoboDuetMethodReader(ReportHTML):
    allowed_tags = (ALLOWED_TAGS - {'img','input','blockquote'}) | {'button'} | MATH_TAGS | SVG_TAGS
    tag_attrs = dict(TAG_ATTRS,
        button={'type','disabled','data-reader-next','data-reader-previous','data-copy-code','data-code-focus'},
        span={'data-reader-section-label'}, math={'xmlns','display'},
        **{tag:set(attrs) for tag,attrs in SVG_ATTRS.items() if tag!='title'})
    aria_attrs = ReportHTML.aria_attrs | {'aria-pressed'}

    def __init__(self, filename, paper_id):
        super().__init__(filename, paper_id)
        self.section_ids=[]
        self.svg_depth=0
        self.math_count=self.svg_count=self.copy_count=self.focus_count=self.pre_count=0
        self.code_depth=0
        self.code_lines=[]
        self.line=[]
        self.reviewed_style_seen=False

    def handle_starttag(self, tag, attrs):
        values=dict(attrs)
        if tag=='style':
            require(not attrs and not self.reviewed_style_seen, 'Only one exact reviewed stylesheet is permitted')
            self.reviewed_style_seen=True
        if tag=='section':
            ident=values.get('id')
            require(ident in SECTION_IDS and ident not in self.section_ids, 'Unknown or duplicate method section')
            self.section_ids.append(ident)
        if tag=='svg':
            require(not self.svg_depth, 'Nested SVG is not permitted')
            self.svg_count+=1
        if tag=='svg' or self.svg_depth:
            require(tag in SVG_ATTRS or tag in {'defs','title','desc'}, 'Unsupported SVG content')
            expected=SVG_ATTRS.get(tag,{})
            require(set(values)<=set(expected), 'Unsupported static SVG attribute')
            for k,v in values.items():
                require(v in expected[k], 'Unexpected static SVG attribute value')
            self.svg_depth+=1
        elif tag in SVG_TAGS:
            raise ValueError('SVG content outside the reviewed SVG')
        if tag in MATH_TAGS:
            require(values==({'xmlns':'http://www.w3.org/1998/Math/MathML','display':'block'} if tag=='math' else {}), 'Unsupported passive math attribute')
            if tag=='math': self.math_count+=1
        if tag=='button': require(values.get('type')=='button', 'Only non-submitting reader controls allowed')
        for attr,counter in [('data-copy-code','copy_count'),('data-code-focus','focus_count')]:
            if attr in values:
                require(tag=='button' and values[attr] is None, 'Invalid static code control')
                setattr(self,counter,getattr(self,counter)+1)
        if tag=='pre': self.pre_count+=1
        if self.code_depth:
            require(tag=='span' and set(values)=={'class'} and values['class'].startswith('tok-'), 'Only inert syntax token spans allowed')
            self.code_depth+=1
        elif tag=='span' and values.get('class')=='code-text':
            self.code_depth=1;self.line=[]
        super().handle_starttag(tag,attrs)

    def handle_data(self,data):
        if self.code_depth:self.line.append(data)
        super().handle_data(data)

    def handle_endtag(self,tag):
        if self.code_depth:
            require(tag=='span', 'Unbalanced syntax token span')
            self.code_depth-=1
            if not self.code_depth:self.code_lines.append(''.join(self.line))
        if self.svg_depth:
            self.svg_depth-=1
            require((tag=='svg')==(self.svg_depth==0), 'Unbalanced static SVG')
        super().handle_endtag(tag)

    def close(self):
        super().close()
        require(self.reviewed_style_seen and tuple(self.section_ids)==SECTION_IDS, 'Missing or reordered method sections')
        require(not self.svg_depth and not self.code_depth, 'Unclosed method content')
        require((self.math_count,self.svg_count,self.copy_count,self.focus_count,self.pre_count)==(14,1,12,12,15), 'Method reader requires fourteen math blocks, one original schematic, twelve excerpts and three license notices')
        require(sha('\n'.join(self.code_lines).encode())==CODE_LINES_HASH, 'Source excerpts differ from reviewed fixed-commit lines')

def prepare(root,record,payload):
    require({key:record.get(key) for key in IDENTITY}==IDENTITY, 'Unapproved RoboDuet method reader identity')
    policy=json.loads(_read(root,POLICY_PATH,20000).decode(),object_pairs_hook=_json_object)
    _keys(policy,POLICY_FIELDS,'RoboDuet Stage 3 v1 policy')
    require(all(policy[key]==value for key,value in IDENTITY.items()), 'Wrong paper/stage reader policy')
    for key in ('document_sha256','source_pdf_sha256','style_sha256','script_sha256'):_digest(policy[key],'Reader fingerprint')
    require(record['source_sha256']==policy['source_pdf_sha256'], 'Wrong author-manuscript source fingerprint')
    require(sha(payload)==policy['document_sha256'], 'Reader document fingerprint differs from reviewed policy')
    text=payload.decode('utf-8')
    require(re.findall(r'<title>(.*?)</title>',text,re.S)==[policy['title']], 'Reader or SVG title differs from approved content')
    styles=re.findall(r'<style>(.*?)</style>',text,re.S)
    require(len(styles)==1 and sha(styles[0].encode())==policy['style_sha256'], 'Unknown or modified reader stylesheet')
    scripts=re.findall(r'<script>(.*?)</script>',text,re.S)
    require(len(scripts)==1 and sha(scripts[0].encode())==policy['script_sha256'], 'Unknown or modified reader-controls script')
    svgs=re.findall(r'<svg\b.*?</svg>',text,re.S)
    require(len(svgs)==1 and sha(svgs[0].encode())==SVG_HASH, 'Original SVG differs from the reviewed inert schematic')
    maths=re.findall(r'<math\b.*?</math>',text,re.S)
    require(tuple(sha(x.encode()) for x in maths)==MATH_HASHES, 'MathML differs from reviewed formula blocks')
    text=re.sub(r'<script>.*?</script>','',text,count=1,flags=re.S)
    return text,RoboDuetMethodReader(record['filename'],record['paper_id'])
