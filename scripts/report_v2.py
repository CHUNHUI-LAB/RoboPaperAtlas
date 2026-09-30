"""Validate the immutable v2 reader documents and their reviewed embedded assets.

This is deliberately not an arbitrary active-HTML uploader: document and asset
fingerprints must both match the explicit v2 policy. Legacy v1 stays script-free.
"""
import json,re
from reports import ReportHTML,ALLOWED_TAGS,GLOBAL_ATTRS,TAG_ATTRS,ARIA_ATTRS,STAGE_FILES,require,sha,_read,_keys,_digest,_json_object

STYLE_NAMES={'styles.css','experience.css','reader-v2.css','reader-document.css','vendor/katex/katex.min.css'}
SCRIPT_NAMES={'app.js','frontier.js','interface.js','motion.js','brief-reader.js','experience.js','reader-v2.js'}
MATH_TAGS=set('math semantics mrow mi annotation mo mn msubsup msup msub mtext mfrac mover munder munderover mspace mtable mtr mtd msqrt mroot menclose mpadded mstyle'.split())
EXTRA_ATTRS={
 'body':{'data-root','data-data-version'},
 'button':{'type','disabled','data-copy-code','data-code-focus','data-reader-next','data-reader-previous','data-source-unit','data-source-toggle','data-source-previous','data-source-next'},
 'span':{'data-math-id','data-reader-section-label'},
 'input':{'type','autocomplete','placeholder'},
 'tr':{'data-source-row'},'td':{'data-label'},
 'p':{'data-source-id','data-source-location','data-source-paraphrase'},
 'blockquote':{'data-source-quote'},'a':{'data-source-open'},
 'math':{'display','xmlns'},'mi':{'mathvariant'},'annotation':{'encoding'},
 'mo':{'fence','lspace','rspace','separator','stretchy'},'mover':{'accent'},
 'mspace':{'width','height','depth'},'mtable':{'columnalign','columnspacing','rowspacing'},
 'mstyle':{'mathsize','scriptlevel','displaystyle'},
}

class ReaderHTML(ReportHTML):
    allowed_tags=(ALLOWED_TAGS-{'style'})|MATH_TAGS|{'button','dialog','form'}
    global_attrs=GLOBAL_ATTRS
    tag_attrs={key:TAG_ATTRS.get(key,set())|EXTRA_ATTRS.get(key,set()) for key in set(TAG_ATTRS)|set(EXTRA_ATTRS)}
    aria_attrs=ARIA_ATTRS|{'aria-haspopup','aria-pressed'}
    meta_names={'viewport','description','author','robots','color-scheme','theme-color'}
    input_types={'checkbox','search'}
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag=='math':require(values.get('xmlns')=='http://www.w3.org/1998/Math/MathML','Only MathML namespace allowed')
        if tag=='annotation':require(values.get('encoding')=='application/x-tex','Only accessible TeX annotations allowed')
        if tag=='body':require(values.get('data-root')=='https://chunhui-lab.github.io/RoboPaperAtlas/','Reader site root must be the public site')
        if tag=='button':require(values.get('type')=='button','Only non-submitting reader buttons are allowed')
        super().handle_starttag(tag,attrs)


def prepare(root,record,payload):
    require(record.get('version') in {'v2','v3'},'Unknown immutable reader version')
    policy=json.loads(_read(root,'data/report-'+record['version']+'-policy.json',20000).decode(),object_pairs_hook=_json_object)
    _keys(policy,{'version','styles','scripts','documents'},'Reader v2 policy')
    require(policy['version']==record['version'],'Unknown reader policy version')
    for key,names in [('styles',STYLE_NAMES),('scripts',SCRIPT_NAMES),('documents',set(STAGE_FILES.values()))]:
        _keys(policy[key],names,'Reader '+key)
        for digest in policy[key].values():_digest(digest,'Reader fingerprint')
    require(sha(payload)==policy['documents'][record['filename']],'Reader document fingerprint differs from reviewed policy')
    text=payload.decode('utf-8');seen_styles=set();seen_scripts=set()
    def style(m):
        name=m[1];require(name in STYLE_NAMES and name not in seen_styles,'Unknown or repeated reader CSS')
        require(sha(m[2].encode())==policy['styles'][name],'Reader CSS fingerprint mismatch')
        # The approved immutable CSS may embed fonts and decoration. No network load.
        require(not re.search(r'@import\b',m[2],re.I),'External CSS import forbidden')
        for url in re.findall(r'url\(([^)]+)\)',m[2]):require(url.startswith(('data:font/woff2;base64,','data:image/svg+xml;base64,')),'Nonembedded CSS resource forbidden')
        seen_styles.add(name);return''
    text=re.sub(r'<style data-report-style="([^"]+)">(.*?)</style>',style,text,flags=re.S)
    def script(m):
        name=m[1];require(name in SCRIPT_NAMES and name not in seen_scripts,'Unknown or repeated reader script')
        require(sha(m[2].encode())==policy['scripts'][name],'Reader script fingerprint mismatch')
        seen_scripts.add(name);return''
    text=re.sub(r'<script data-report-script="([^"]+)">(.*?)</script>',script,text,flags=re.S)
    require(seen_scripts==SCRIPT_NAMES,'Missing reviewed reader script')
    require(seen_styles==STYLE_NAMES-({'vendor/katex/katex.min.css'}if record['stage']!='stage3'else set()),'Missing reviewed reader style')
    if record['stage']=='stage2':
        matches=re.findall(r'<script type="application/json" data-source-units id="reader-source-units">(.*?)</script>',text,re.S)
        require(len(matches)==1,'Stage2 must have one reviewed source-location payload')
        units=json.loads(matches[0],object_pairs_hook=_json_object)
        require(isinstance(units,list) and len(units)==37,'Exactly37 reviewed source units required')
        ids=set();words=0
        for unit in units:
            _keys(unit,{'id','location','paraphrase','quote','page','url'},'Source unit')
            require(isinstance(unit['id'],str) and re.fullmatch(r'(?:A[1-8]|[PTKC][1-5]-S[1-5])',unit['id']) and unit['id']not in ids,'Invalid source unit ID')
            ids.add(unit['id'])
            require(type(unit['page'])is int and 1<=unit['page']<=17,'Invalid formal PDF page')
            require(unit['url']=='https://raw.githubusercontent.com/mlresearch/v270/main/assets/ha25a/ha25a.pdf#page='+str(unit['page']),'Unexpected source PDF URL')
            for k in ['location','paraphrase']:require(isinstance(unit[k],str) and len(unit[k])<4000,'Invalid source-unit text')
            require(unit['quote'] is None or isinstance(unit['quote'],str) and len(unit['quote'])<4000,'Invalid short quote')
            words+=len((unit['quote']or'').split())
        require(words<=25,'Source quote budget exceeded')
        text=re.sub(r'<script type="application/json" data-source-units id="reader-source-units">.*?</script>','',text,flags=re.S)
    return text,ReaderHTML(record['filename'])
