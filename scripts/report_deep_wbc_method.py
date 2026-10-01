"""One fingerprinted Deep WBC method report: passive math and static code only."""
import base64
import binascii
import re
from reports import require, sha, _digest, _safe_css
from report_deep_wbc import DeepWBCReader

MATH_TAGS = set('math semantics mrow mi annotation mo mn msubsup msup msub mtext mfrac mover munder mspace'.split())
MATH_ATTRS = {
    'math': {'xmlns': {'http://www.w3.org/1998/Math/MathML'}, 'display': {'block'}},
    'mi': {'mathvariant': {'double-struck', 'normal', 'script'}},
    'annotation': {'encoding': {'application/x-tex'}},
    'mo': {k: {'true','false'} for k in ('fence','separator','stretchy')},
    'mover': {'accent': {'true'}}, 'mspace': {'width': {'1em','2em'}},
    'svg': {'xmlns': {'http://www.w3.org/2000/svg'}, 'width': {'100%','400em'},
            'height': {'0.26em','0.548em'}, 'viewbox': {'0 0 600 260','0 0 400000 548'},
            'preserveaspectratio': {'none','xMaxYMin slice','xMidYMin slice','xMinYMin slice'}},
    'path': {'d': None},
}

class DeepWBCMethodReader(DeepWBCReader):
    allowed_tags = DeepWBCReader.allowed_tags | MATH_TAGS | {'svg','path'}
    tag_attrs = dict(DeepWBCReader.tag_attrs, **{t:set(a) for t,a in MATH_ATTRS.items()})
    tag_attrs['button'] = DeepWBCReader.tag_attrs['button'] | {'data-copy-code','data-code-focus'}
    aria_attrs = DeepWBCReader.aria_attrs | {'aria-pressed'}

    def __init__(self, filename, paper_id):
        super().__init__(filename, paper_id)
        self.math_count = self.image_count = self.copy_count = self.focus_count = self.pre_count = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in MATH_TAGS | {'svg','path'}:
            # No arbitrary globals, URLs, event handlers or foreign content in math/SVG.
            require(set(values) <= set(MATH_ATTRS.get(tag, {})), 'Unsupported passive math attribute')
            for k,v in values.items():
                allowed = MATH_ATTRS[tag][k]
                if allowed is not None:
                    require(v in allowed, 'Unexpected passive math attribute value')
                else:
                    require(isinstance(v,str) and re.fullmatch(r'[MmZzLlHhVvCcSsQqTtAa0-9.,+\s-]+',v), 'Only numeric SVG path geometry allowed')
        if tag == 'math':
            require(values == {'xmlns':'http://www.w3.org/1998/Math/MathML','display':'block'}, 'Expected static display MathML')
            self.math_count += 1
        if tag == 'annotation': require(values == {'encoding':'application/x-tex'}, 'Only TeX annotation allowed')
        if tag == 'img': self.image_count += 1
        if tag == 'pre': self.pre_count += 1
        for attr,counter in [('data-copy-code','copy_count'),('data-code-focus','focus_count')]:
            if attr in values:
                require(tag == 'button' and values[attr] is None, 'Invalid static code control')
                setattr(self,counter,getattr(self,counter)+1)
        super().handle_starttag(tag, attrs)

    def close(self):
        super().close()
        require((self.math_count,self.image_count,self.copy_count,self.focus_count,self.pre_count) == (9,4,11,11,23),
                'Method reader requires its reviewed nine equations, four images, eleven code controls and twenty-three preformatted blocks')


def prepare_style(text, policy):
    _digest(policy['style_sha256'], 'Method stylesheet fingerprint')
    styles = re.findall(r'<style>(.*?)</style>', text, re.S)
    require(len(styles)==1 and sha(styles[0].encode())==policy['style_sha256'], 'Unknown method stylesheet')
    fonts=[]
    def font(match):
        encoded=match[1]
        try: raw=base64.b64decode(encoded,validate=True)
        except (ValueError,binascii.Error) as exc: raise ValueError('Invalid embedded font') from exc
        require(base64.b64encode(raw).decode()==encoded and raw.startswith(b'wOF2'), 'Only canonical embedded WOFF2 fonts allowed')
        fonts.append(raw)
        return 'none'
    css=re.sub(r'url\(data:font/woff2;base64,([A-Za-z0-9+/]*={0,2})\)',font,styles[0])
    require(len(fonts)==20, 'Method reader requires its twenty embedded fonts')
    # The stylesheet is fingerprinted first. Permit only @font-face in addition
    # to the existing safe CSS set, with every font URL validated above.
    _safe_css(re.sub(r'@font-face\b','@media',css))
    return re.sub(r'<style>.*?</style>','',text,count=1,flags=re.S)
