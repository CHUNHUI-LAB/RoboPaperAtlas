"""One exact CC BY 4.0 RoLoMa writing report; no general quotation importer.

Pins 36 reviewed source units, their licensed original sentences, one passive
MathML objective and offline reader chrome. Historical policies stay unchanged.
"""
import json,re
from reports import (ReportHTML,ALLOWED_TAGS,TAG_ATTRS,require,sha,_read,
                     _keys,_digest,_json_object)
IDENTITY=dict(paper_id='rpa-0054',stage='stage2',version='v1',filename='writing-close-reading.html')
POLICY_PATH='data/report-rpa-0054-stage2-v1-policy.json'
POLICY_FIELDS=set(IDENTITY)|{'document_sha256','source_pdf_sha256','style_sha256','script_sha256','title'}
SECTION_IDS=('structure','abstract','introduction','gap-insight','conclusion','other-sections','language','skeleton')
UNIT_IDS=('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'P1-S1', 'P1-S2', 'P1-S3', 'P2-S1', 'P2-S2', 'P2-S3', 'P3-S1', 'P3-S2', 'P4-S1', 'P4-S2', 'P4-S3', 'P5-S1', 'P5-S2', 'P5-S3', 'P5-S4', 'P5-S5', 'P5-S6', 'P5-S7', 'C1-S1', 'C1-S2', 'C1-S3', 'C1-S4', 'C1-S5', 'C2-S1', 'C2-S2', 'C2-S3', 'C2-S4', 'C2-S5')
QUOTE_HASHES=('cd15ddc1c31c0262ff3736f61cf7e87163500b225f9f8ab751beee255128dbe2', '7d96ba900376c493df0c6a2e59deefb9d31ecd7f98127118b917f631780b1700', 'ad00c19642a1282b8154df924989c9a9b9a56b1232cb0a71e52ccb738276f170', 'f6c7a58a4e78252c4589ce2afed17217ff474677a18057ebf16a31cd22598732', '529c7f3ecdfa9bc036059bbec6dbcfb23398b45de4dc3241764395760f7a4785', '40f474e0a4d88cdbe20193d631ba2205e07e3763301deb49216d4a406029b81c', 'c21a16884d3e45e77d8e27144428065cce3ab886b102b9b0d527862d43f35cf8', 'fdfd3428baf1a9e528c433fd286d33df8897f488df341570b75bf0c591663e5d', 'a74be3245dbee2bb6e2ba8932fc0438d31acb2226b767ec75160448dfc53fd2c', '463f6aaa71d497d23754bb5490bc809f4b864a71d9e7544adfc696cd2b54a83d', 'a3a249a0039729184a8190e8df3c25662ddb9da357aa37271a368ba5c8c62860', '784686352846735c8a824391b420b07f55503693e9a319f18aecb2641e00d81b', '7af0d5a100b21e03d7cebbcc47fbb4f0f740dfadba52df8ed5de82a80674142f', 'fe753700279cd1aca23cdde88a8783a4cc5046f42e5d0e1e4b390802c7ad3ae2', '4066669055ed28bb70f8536f4b284ce256eb3b0b04d5c06b1b77921a773e0dbb', '2fb786c282219abf0fb5c3c7565e7474f259ee2b0b271501481269fd2c1024ab', '0e96af30a7b46e8407d3437959f3fa8518c8c1b856939d1ca5590235b91178b0', '3c0f43adbaa2f160c0f4d2847a9b4fc0193868e992df5b9a5c71dbb963c0b436', 'dea97a10a966a9505d35818048131268983ca05dfb9c4984ee66d415a9dec378', 'aa1495ab1bf6de4962dc5178e72867aa54cbd01cbcc49aaedcc2899fadc8fd14', '116c2ee053751a95a8354644197507362246e2629a0f775249337342bf9c534b', 'd561732389540cc6dcc9838f50cc7e3328c061528349b2f68a00783b1a2794ae', '6031d11e1b646de6aa7fb3838df828cd104c5460291e8293abb10caf04db2283', '8573b5de9c145e6dd626730b92b63b552b66606e0a057fe1bc51a9badbace338', 'ae41825066ba0822677337421a0573e902128bf0c62fd93b3fc7c12370ef6f17', '0be582d3bd87ce119a12b60e545826a6fabc44f5a413e5bbbd1f80bce118de68', 'dc92459ce4e03a98b1b60c9f35be646c5e1acbbfbaad899de37137aff83e2cba', 'a9b00888cd859332f57ebe311fc4f9f468e8eab48cbf48f72a94fa60c26ea2a2', '9c89d6446a1302597536cf5f39c1ef1e4ba4a3273242156caaa2dd68a1967338', '974a9a1976f5eb7757e59c330bba7c4e43c92a863db472e4a9534ea7058c26f7', '7ce6539053866d595a905ee1bd114181b2884801c8ac102379a4ae84d6ef8353', 'eba64b7b7926f8c8f7092a6f2d46ef597daa56088d6d7df850eac9e992d9d86f', '4021fd157b0a6d91e6fcc51d68ca3057f5d84d517bddd4c63959ff250532062f', 'd31624c7682a8a8184314aa81b468d58a5c35c8674e1e3df1d2e8b604dc73676', '4f5b564aa09ab2ff113cedd1b05ffc2a3acf9bf59da139af3a91d656ff68a62c', '363396e190b56794964a21e5b6cf20cb40cfc4a8f6704278e1c51b871321822f')
MATH_HASH='00f231d3b19b305b23476fe5a7d2162a592679536a8f31ac3fcab610c661c6a5'
MATH_TAGS=set('math mrow munderover msub mi mn mo mspace'.split())

class RoLoMaWritingReader(ReportHTML):
    allowed_tags=(ALLOWED_TAGS-{'img','input'})|{'button'}|MATH_TAGS
    tag_attrs=dict(TAG_ATTRS,button={'type','disabled','data-reader-next','data-reader-previous'},
                   span={'data-reader-section-label'},div={'data-source-row'},
                   blockquote={'data-verbatim'},math={'display'},mspace={'width'})
    def __init__(self,filename,paper_id):
        super().__init__(filename,paper_id)
        self.section_ids=[];self.source_rows=[];self.quotes=[]
        self.in_quote=False;self.quote_text=[];self.math_count=0;self.reviewed_style_seen=False
    def handle_starttag(self,tag,attrs):
        v=dict(attrs)
        if tag=='style':
            require(not attrs and not self.reviewed_style_seen,'Only one exact reviewed stylesheet is permitted')
            self.reviewed_style_seen=True
        if tag=='section':
            ident=v.get('id');require(ident in SECTION_IDS and ident not in self.section_ids,'Unknown or duplicate writing section')
            self.section_ids.append(ident)
        if tag=='button':require(v.get('type')=='button','Only non-submitting reader controls allowed')
        if 'data-source-row' in v:
            ident=v['data-source-row']
            require(tag=='div' and v.get('class')=='source-unit-parallel' and ident in UNIT_IDS
                    and ident not in self.source_rows and v.get('id')==ident,'Unknown or duplicate source unit')
            self.source_rows.append(ident)
        if tag=='blockquote':
            require(not self.in_quote and v.get('class')=='source-excerpt' and v.get('lang')=='en'
                    and v.get('data-verbatim')=='paper','Only labelled reviewed quotations are permitted')
            self.in_quote=True;self.quote_text=[]
        elif self.in_quote:raise ValueError('Quotations must contain plain text only')
        if tag in MATH_TAGS:
            expected=({'display':'block'} if tag=='math' else {'width':'.6em'} if tag=='mspace' else {})
            require(v==expected,'Unsupported passive math attribute')
            if tag=='math':self.math_count+=1
        super().handle_starttag(tag,attrs)
    def handle_data(self,data):
        if self.in_quote:self.quote_text.append(data)
        super().handle_data(data)
    def handle_endtag(self,tag):
        if tag=='blockquote':
            require(self.in_quote,'Unexpected quotation end')
            self.quotes.append(''.join(self.quote_text));self.in_quote=False;self.quote_text=[]
        super().handle_endtag(tag)
    def close(self):
        super().close()
        require(self.reviewed_style_seen and tuple(self.section_ids)==SECTION_IDS,'Missing or reordered writing sections')
        require(tuple(self.source_rows)==UNIT_IDS,'Missing or reordered RoLoMa source units')
        require(not self.in_quote and tuple(sha(q.encode()) for q in self.quotes)==QUOTE_HASHES,
                'RoLoMa allows only the 36 fixed licensed quotations in reviewed order')
        require(self.math_count==1,'Exactly one reviewed passive formula required')

def prepare(root,record,payload):
    require({key:record.get(key) for key in IDENTITY}==IDENTITY,'Unapproved RoLoMa writing identity')
    policy=json.loads(_read(root,POLICY_PATH,20000).decode(),object_pairs_hook=_json_object)
    _keys(policy,POLICY_FIELDS,'RoLoMa Stage 2 v1 policy')
    require(all(policy[k]==v for k,v in IDENTITY.items()),'Wrong paper/stage reader policy')
    for key in ('document_sha256','source_pdf_sha256','style_sha256','script_sha256'):_digest(policy[key],'Reader fingerprint')
    require(record['source_sha256']==policy['source_pdf_sha256'],'Wrong formal-paper source fingerprint')
    require(sha(payload)==policy['document_sha256'],'Reader document fingerprint differs from reviewed policy')
    text=payload.decode('utf-8')
    require(re.findall(r'<title>(.*?)</title>',text,re.S)==[policy['title']],'Reader title differs from reviewed content')
    styles=re.findall(r'<style>(.*?)</style>',text,re.S)
    require(len(styles)==1 and sha(styles[0].encode())==policy['style_sha256'],'Unknown or modified reader stylesheet')
    scripts=re.findall(r'<script>(.*?)</script>',text,re.S)
    require(len(scripts)==1 and sha(scripts[0].encode())==policy['script_sha256'],'Unknown or modified reader-controls script')
    maths=re.findall(r'<math\b.*?</math>',text,re.S)
    require(len(maths)==1 and sha(maths[0].encode())==MATH_HASH,'MathML differs from reviewed objective')
    text=re.sub(r'<script>.*?</script>','',text,count=1,flags=re.S)
    return text,RoLoMaWritingReader(record['filename'],record['paper_id'])
