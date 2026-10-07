'use strict';
// Deterministic local DOM/model contracts only. No browser, server, or network.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {fixture}=require('./entry_dom_fixture.cjs');
const root=path.resolve(__dirname,'..');
const baseline=require('./entry-baseline.json'),sha=b=>require('node:crypto').createHash('sha256').update(b).digest('hex');
let count=0,failed=0;
function test(name,fn){try{fn();count++;console.log('PASS '+name);}catch(err){failed++;console.error('FAIL '+name+'\n'+err.stack);}}
function start(){const f=fixture();assert.deepEqual(f.errors,[]);return f;}
function json(v){return JSON.parse(JSON.stringify(v));}
function files(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(x=>x.isDirectory()?files(path.join(dir,x.name)):path.join(dir,x.name));}
function choose(f){f.click('#global-tab-a');assert.equal(f.app.getState().globalTree,'a');return f.$('#global-panel-a');}
function selector(f){return f.$('#analysis-paper-select');}
function rootButton(f,key,id){if(key==='l'){const group=f.window.TreeModel.taskMap.groupFor(id);assert(group,'unmapped original protocol '+id);if(f.app.getState().taskGroup!==group)f.click('.task-family[data-id="'+group+'"]');const el=f.$('#global-panel-l').querySelector('.protocol-card[data-id="'+id+'"]');assert(el,'missing protocol '+id);return el;}const T=f.window.TreeModel.atlas,t=T.paths(f.app.model,key),n=t.nodes.find(n=>n.sourceId===id&&n.parent===t.root);assert(n,'unknown original root '+id);const el=f.$('#global-panel-'+key).querySelector('[data-atlas-id="'+n.id+'"]');assert(el,'missing atlas root '+id);return el;}
function atlasRoots(f){return ['l','c'].flatMap(key=>f.$('#global-panel-'+key).querySelectorAll('.atlas-root'));}
function assertCompleteAtlas(f,key,mode='semantic'){const T=f.window.TreeModel.atlas,t=T.paths(f.app.model,key);let panel=f.$('#global-panel-'+key);if(key==='l'){const detached=new panel.constructor('section');detached.innerHTML=T.html(t,{selected:t.root,view:'source-l',mode});panel=detached;}const svg=panel.querySelector('.atlas-svg'),selected=panel.querySelector('.atlas-vertex.current').dataset.atlasId,scene=T.layout(t,{selected,mode:svg.dataset.mode}),nodes=panel.querySelectorAll('.atlas-vertex'),edges=panel.querySelector('.atlas-edges').querySelectorAll('path');assert.deepEqual(nodes.map(n=>n.dataset.atlasId).sort(),json(scene.nodes.map(n=>n.id).sort()));assert.equal(Number(svg.dataset.totalCount),t.nodes.length);assert.equal(Number(svg.dataset.nodeCount),nodes.length);assert.equal(scene.visibleCount+scene.foldedCount,t.nodes.length);assert.equal(edges.length,nodes.length-1);for(const edge of edges)assert.equal(t.by.get(edge.dataset.target).parent,edge.dataset.source);return t;}

function openSelection(f,id){const select=selector(f);assert(select);select.value=id;select.emit('change');if(!f.c2.isOpen()){const b=f.$('#global-panel-a').querySelectorAll('[data-open-analysis]').find(x=>x.dataset.openAnalysis===id);assert(b,'selected paper entry is missing');b.emit('click');}}
// PROPOSED ONLY: archive fixed bytes, then compare current scientific projections.
const {spawnSync}=require('node:child_process');
const historicalNames=new Set(['analysis/data/bundle.js','all-papers.html','analysis/reading.html']);
const historicalRoot=path.join(root,'tests/historical-single-paper');
const preservationPython=String.raw`
import json,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote,quote

payload=json.load(sys.stdin); root=Path(payload['root']); overrides=payload.get('overrides',{})
import hashlib
APPROVED_INPUTS = {'data/catalog.json': 'bf1ba3b0887334803f08a11e80dd8bb0db0f2d3427f8d3787f1e5cc704f37bf4', 'data/literature-seed.json': '4e3cd8b898acf82a1dcfbcd78a8903dc5a79ecd98bad06b1178fb88841da7bad', 'data/challenge-seed.json': '857e0d0f719ea651ede20f49384ae8fcdba878a58b3821e186b7e4115e8d417d', 'analysis/data/method.json': '3680f02c8d06f266c9975c7d1ea677e031ed15f6ede1cd18cedca63682f29c53', 'analysis/data/mapping.json': '2bb837879bf6e4ad4d44cb83ee7203428169a6ef9219e193bdf30ce27f932d20', 'analysis/data/analysis.compat.json': 'e665093f8001af87d7f46882fd68dbd00e3fa236b6c4efeb9cf8bca181baff15', 'analysis/data/ledger.json': 'b0aa5113e36eb34f4fa7fc8b2d71460678baa6c54de1e038802937a6fe9effac', 'analysis/data/UPSTREAM-VERIFICATION.json': 'bf846ca9b440ebde6333dff6104ca6a1d7ff60a246bb6634be969fc60f518589', 'analysis/data/navharness.mapping.json': '23e0eb70374965f85184b36ba3c33e91732477d8aeee2c047e583e08c29ca7ec', 'analysis/data/navharness.ledger.json': 'e81ef8f9aa101301f3feb310ebfcc406ddd92885c192bad6586560cd1814b7ee', 'analysis/data/navharness.unknowns.json': '10803d91f96ae6d85770769dfd3405af68e6f069de60ccf93b1df0e1d15106b8', 'analysis/data/MULTI-PAPER-VERIFICATION.json': 'c6812cfad5bb4ed3aaae31145632b1a7b7c9a95eaf5448adb3d259ccd3f55a0d'}
for name,digest in APPROVED_INPUTS.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,('Approved input source hash mismatch',name)

def source(name): return overrides.get(name,(root/name).read_text())
# This is an exact reviewed delta replay, never an exemption for literature edits.
from copy import deepcopy
original=json.loads((root/'data/literature-seed.json').read_text())
original_bytes=('window.LITERATURE_TREE = '+json.dumps(original,ensure_ascii=False,indent=2)+';\n').encode()
assert hashlib.sha256(original_bytes).hexdigest()=='3e7891c1797fe58627787b583d29e1bc8c1467793db49a6207b2f6b1f6576de3','Original literature runtime baseline changed'
delta_bytes=(root/'data/task-contract-corrections-20261007.json').read_bytes()
assert hashlib.sha256(delta_bytes).hexdigest()=='dd9f1990f1f68b04b37183231b9a362938ee4596543d0957eed5e86529163748','Reviewed literature correction delta changed'
delta=json.loads(delta_bytes)
assert delta['baseline_sha256']==hashlib.sha256(original_bytes).hexdigest()
corrected=deepcopy(original); by={n['node_id']:n for n in corrected['nodes']}
for collection in ('nodes','implementation_variants'):
    for record in delta[collection]:
        node=by[record['node_id']] if collection=='nodes' else corrected[collection][record['selector']['variant_id']]
        for field in record['fields']:
            name=field['field']
            assert (name in node)==field['before_present'] and node.get(name)==field['before'],('Correction before-value mismatch',collection,name)
            node[name]=deepcopy(field['after'])
for key,extra in delta['append_only_additions'].items():corrected.setdefault(key,[]).extend(deepcopy(extra))
corrected.update(deepcopy(delta['top_level_additions']))
assert corrected['paths']==original['paths'] and corrected['edges']==original['edges'],'Original path/edge graph changed'
assert [n['node_id'] for n in corrected['nodes']]==[n['node_id'] for n in original['nodes']],'Original node inventory/order changed'
literature=source('data/literature.js')
assert literature.startswith('window.LITERATURE_TREE = ') and literature.endswith(';\n')
assert json.loads(literature[len('window.LITERATURE_TREE = '):-2])==corrected,'Runtime literature differs from exact reviewed field replay'
assert hashlib.sha256(literature.encode()).hexdigest()=='44a1645269740d0f1bda0cbaddc6097d915f43171b6c4739fde7a745b80efc66','Corrected literature runtime bytes changed'

def load(name): return json.loads((root/name).read_text())
def assigned(text):
    assert text.startswith('window.C2_DATA = ') and text.endswith(';\n')
    return json.loads(text[len('window.C2_DATA = '):-2])
bundle=assigned(source('analysis/data/bundle.js'))
harness=load('analysis/data/mapping.json'); nav=load('analysis/data/navharness.mapping.json')
expected={'schema':load('analysis/data/method.json'),'mapping':harness,'compat':load('analysis/data/analysis.compat.json'),
 'mappingsByPaperId':{'harnessvln':harness,'navharness':nav},
 'ledgersByPaperId':{'harnessvln':load('analysis/data/ledger.json'),'navharness':load('analysis/data/navharness.ledger.json')},
 'unknownsByPaperId':{'harnessvln':harness['unresolvedQuestions'],'navharness':load('analysis/data/navharness.unknowns.json')}}
assert bundle==expected,'Current complete bundle differs from approved source values'
legacy={k:bundle[k] for k in ('schema','mapping','compat')}
legacy_bytes=('window.C2_DATA = '+json.dumps(legacy,ensure_ascii=False)+';\n').encode()
assert legacy_bytes==(root/'tests/historical-single-paper/analysis/data/bundle.js').read_bytes(), 'Legacy source bytes not reproduced'

class Node:
    def __init__(self,tag='',attrs=()): self.tag=tag;self.attrs=dict(attrs);self.children=[]
    def text(self): return ''.join(c if isinstance(c,str) else c.text() for c in self.children)
    def direct(self,tag=None): return [c for c in self.children if isinstance(c,Node) and (tag is None or c.tag==tag)]
    def walk(self):
        yield self
        for c in self.direct(): yield from c.walk()
class Document(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root];self.feed(text)
    def handle_starttag(self,tag,attrs):
        node=Node(tag,attrs);self.stack[-1].children.append(node)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}: self.stack.append(node)
    def handle_endtag(self,tag):
        assert len(self.stack)>1 and self.stack[-1].tag==tag,('Unbalanced HTML',tag)
        self.stack.pop()
    def handle_data(self,text): self.stack[-1].children.append(text)
def nodes(doc): return list(doc.root.walk())
def one(items,label):
    assert len(items)==1,(label,len(items))
    return items[0]
def cls(node,value): return value in node.attrs.get('class','').split()
def scalar(value):
    if value is None:return 'null'
    if isinstance(value,bool):return str(value).lower()
    return str(value)
def record(node,expected,label):
    dl=one(node.direct('dl'),label+' dl')
    fields=dl.direct('dd')
    keys=[f.attrs.get('data-field') for f in fields]
    assert keys==list(expected),(label,'field inventory/order',keys,list(expected))
    assert [d.text() for d in dl.direct('dt')]==list(expected),(label,'field labels')
    for f,(key,value) in zip(fields,expected.items()): typed(f,value,label+'.'+key)
def typed(node,value,label):
    if isinstance(value,dict): return record(node,value,label)
    if isinstance(value,list):
        if not value:
            if label.endswith('.sourceLocators'):
                listing=one(node.direct('ol'),label)
                assert cls(listing,'source-locators') and not listing.direct() and not listing.text(),(label,'empty locator sequence')
                return
            raw=one([n for n in node.direct('span') if cls(n,'raw-value')],label)
            assert raw.text()=='[]',(label,'empty array')
            assert not node.direct('ul') and not node.direct('ol'),(label,'extra array')
            return
        listing=one([n for n in node.direct() if n.tag in ('ul','ol')],label)
        items=listing.direct('li');assert len(items)==len(value),(label,'array length')
        for i,(item,entry) in enumerate(zip(items,value)):typed(item,entry,label+'['+str(i)+']')
        return
    primary=[n for n in node.direct() if n.tag=='a' or (n.tag=='span' and cls(n,'raw-value'))]
    actual=one(primary,label)
    assert actual.text()==scalar(value),(label,'scalar',actual.text(),scalar(value))
    if isinstance(value,str) and urlsplit(value).scheme in ('https','http'):
        assert actual.attrs.get('href')==value,(label,'URL href')

reading=Document(source('analysis/reading.html')); current_nodes=nodes(reading)
ids=[n.attrs['id'] for n in current_nodes if 'id' in n.attrs];assert len(ids)==len(set(ids)),'Duplicate HTML ID'
by_id={n.attrs['id']:n for n in current_nodes if 'id' in n.attrs}
all_papers=Document(source('all-papers.html'))
current_docs={'analysis/reading.html':reading,'all-papers.html':all_papers}
missing_dynamic=[]
for name,doc in current_docs.items():
    old=Document((root/'tests/historical-single-paper'/name).read_text())
    old_nodes=nodes(old); new_nodes=nodes(doc)
    old_ids={n.attrs['id'] for n in old_nodes if 'id' in n.attrs}
    new_ids=[n.attrs['id'] for n in new_nodes if 'id' in n.attrs]
    assert len(new_ids)==len(set(new_ids)),(name,'duplicate HTML IDs')
    assert old_ids<=set(new_ids),(name,'missing legacy IDs',old_ids-set(new_ids))
    new_links={n.attrs['href'] for n in new_nodes if 'href' in n.attrs}
    for url in {n.attrs['href'] for n in old_nodes if 'href' in n.attrs}:
        if url in new_links:continue
        parsed=urlsplit(url)
        assert not parsed.scheme and not parsed.netloc,(name,'missing original external link',url)
        if parsed.fragment.startswith(('state=','analysis=')):
            missing_dynamic.append(url);continue
        target=(root/name).parent/unquote(parsed.path) if parsed.path else root/name
        relative=target.resolve().relative_to(root.resolve()).as_posix()
        assert target.is_file(),(name,'unresolved legacy target',url)
        if parsed.fragment:
            target_doc=current_docs.get(relative) or Document(source(relative))
            assert unquote(parsed.fragment) in {n.attrs.get('id') for n in nodes(target_doc)},(name,'unresolved legacy fragment',url)

for pid,mapping in expected['mappingsByPaperId'].items():
    paper_nodes=[n for n in current_nodes if n.tag=='article' and n.attrs.get('data-paper-id')==pid and 'data-node-key' in n.attrs]
    expected_nodes=expected['schema']['nodes']+[dict(n,id=n['nodeId']) for n in mapping['expandedNodes']]
    assert [n.attrs['data-node-key'] for n in paper_nodes]==[n['id'] for n in expected_nodes],(pid,'node inventory/order')
    prefix='node-' + ('' if pid=='harnessvln' else pid+'-')
    for rendered,n in zip(paper_nodes,expected_nodes):
        assert rendered.attrs['id']==prefix+n['id'],(pid,'node namespace')
        label=one([x for x in rendered.direct('h3') if cls(x,'original')],pid+' label')
        assert label.text()==n['labelOriginal'],(pid,n['id'],'label')
        direct_links=[x.attrs['href'] for p in rendered.direct('p') for x in p.direct('a')]
        expected_links=['#'+prefix+n[key] for key in ('parentId','repeatOfSchemaNode','expansionSlot') if n.get(key)]
        assert direct_links==expected_links,(pid,n['id'],'parent/instance topology')
    rendered_answers=[n for n in current_nodes if n.tag=='section' and 'data-answer-node' in n.attrs and any(n is child for p in paper_nodes for child in p.direct('section'))]
    assert [n.attrs['data-answer-node'] for n in rendered_answers]==[a['nodeId'] for n in expected_nodes for a in mapping['answers'] if a['nodeId']==n['id']],(pid,'answer inventory')
    answers={a['nodeId']:a for a in mapping['answers']}
    for rendered in rendered_answers:
        answer=answers[rendered.attrs['data-answer-node']]
        body=one([x for x in rendered.direct('div') if cls(x,'answer')],pid+' answer')
        assert body.text()==answer['answer'],(pid,answer['nodeId'],'answer text')
        record(rendered,{k:v for k,v in answer.items() if k!='answer'},pid+'/'+answer['nodeId'])
    for kind,attribute,records in [('unknown','data-unknown-id',expected['unknownsByPaperId'][pid]),('evidence','data-evidence-id',expected['ledgersByPaperId'][pid]['records'])]:
        articles=[n for n in current_nodes if n.tag=='article' and n.attrs.get('data-paper-id')==pid and attribute in n.attrs]
        wanted=[str(x.get('id',x.get('evidenceRecordId',i+1))) for i,x in enumerate(records)]
        assert [n.attrs[attribute] for n in articles]==wanted,(pid,kind,'inventory/order')
        for article,key,value in zip(articles,wanted,records):
            assert article.attrs['id']==kind+'-'+pid+'-'+key,(pid,kind,'namespace')
            record(article,value,pid+'/'+kind+'/'+key)
# Compare every original catalog article as a complete parsed tree. Only the
# explicitly approved two-paper status paragraph and provenance clarification
# have named transformations; all other original content/attributes stay exact.
def signature(node):
    if isinstance(node,str):return node
    return [node.tag,sorted(node.attrs.items()),[signature(c) for c in node.children]]
def catalog_signature(article,current):
    pid=article.attrs['id'].removeprefix('paper-')
    children=article.children[:]
    if pid not in expected['mappingsByPaperId']:return signature(article)
    structural=[(i,c) for i,c in enumerate(children) if isinstance(c,Node)]
    analysis_heading=one([(i,c) for i,c in structural if c.tag=='h3' and c.text()=='论文解析树'],pid+' analysis heading')[0]
    following=one([(i,c) for i,c in structural if i>analysis_heading][:1],pid+' analysis summary')
    assert following[1].tag=='p',(pid,'analysis summary element')
    if current:
        mapping=expected['mappingsByPaperId'][pid]
        original_count=len(expected['schema']['nodes']);instances=len(mapping['expandedNodes'])
        answer_count=len(mapping['answers']);unknown_count=len(expected['unknownsByPaperId'][pid])
        route='index.html#analysis='+quote(json.dumps({'paperId':pid},separators=(',',':')),safe='')
        approved_paragraph=(f'<p>{original_count} 个原模板节点 + {instances} 个论文实例 = {original_count+instances} 个节点；'
            f'{answer_count} 项内容记录、{unknown_count} 项未答 / 未知。既有 Stage 未改；未独立复现实验。 '
            f'<a href="analysis/reading.html#paper-{pid}">完整解析文字替代</a> · '
            f'<a href="analysis/reading.html#unknowns-{pid}">全部未答 / 未知</a> · '
            f'<a href="{route}">打开论文解析树</a></p>')
        approved_node=one(Document(approved_paragraph).root.direct('p'),pid+' approved summary')
        assert signature(following[1])==signature(approved_node),(pid,'approved exact analysis summary changed')
    children[following[0]]='APPROVED_PAPER_ANALYSIS_STATUS'
    if current:
        scope_heading=one([(i,c) for i,c in structural if c.tag=='h3' and c.text()=='原目录记录的已读位置与未读范围'],pid+' scope heading')
        replacement=Node('h3',scope_heading[1].attrs.items());replacement.children=['已读位置与未读范围'];children[scope_heading[0]]=replacement
        scope_note=one([(i,c) for i,c in structural if i>scope_heading[0]][:1],pid+' scope note')
        note=scope_note[1]
        assert note.tag=='p' and note.attrs=={'class':'muted'},(pid,'scope clarification element')
        assert note.text()=='此处保留原目录范围；本次已审解析的完整核读范围与边界见解析来源范围。',(pid,'scope clarification text')
        assert [a.attrs for a in note.direct('a')]==[{'href':'analysis/reading.html#source-coverage'+('' if pid=='harnessvln' else '-'+pid)}],(pid,'scope clarification URL')
        del children[scope_note[0]]
    projected=Node(article.tag,article.attrs.items());projected.children=children
    return signature(projected)
old_catalog=Document((root/'tests/historical-single-paper/all-papers.html').read_text())
old_articles=[n for n in nodes(old_catalog) if n.tag=='article']
all_articles=[n for n in nodes(all_papers) if n.tag=='article']
new_articles=[n for n in all_articles if n.attrs.get('id','').startswith('paper-')]
protocol_articles=[n for n in all_articles if n not in new_articles]
protocol_variants={v['id']:v for n in corrected['nodes'] for v in n.get('protocol_variants',[])}
assert len(protocol_articles)==len(protocol_variants)==7,'Exact reviewed protocol supplement inventory changed'
assert {n.attrs.get('data-protocol-variant') for n in protocol_articles}==set(protocol_variants),'Unknown or missing protocol supplement'
protocol_fields=[('目标如何给定','goal_spec'),('目标发放与顺序','goal_delivery'),('怎样移动','action_regime'),('是否预先有地图','environment_prior'),('记忆何时重置','memory_regime'),('怎样判成功','success_contract'),('评测范围','evaluation_scope'),('oracle 转场','oracle_phase'),('tour 排序','tour_ordering'),('适用范围','scope_note'),('边界','boundary')]
for article in protocol_articles:
    variant=protocol_variants[article.attrs['data-protocol-variant']]
    assert article.attrs=={'class':'current-protocol-version','data-protocol-variant':variant['id']},'Protocol supplement attributes changed'
    support=variant.get('supporting_sources',[])
    assert [n.tag for n in article.direct()]==['h4','dl','p','p','a']+['p']*len(support),'Protocol supplement structure changed'
    assert one(article.direct('h4'),'protocol heading').text()==variant['title'],'Protocol title changed'
    fields=one(article.direct('dl'),'protocol fields')
    expected_fields=[(label,variant[key]) for label,key in protocol_fields if variant.get(key)]
    assert [n.text() for n in fields.direct('dt')]==[label for label,value in expected_fields],'Protocol field names changed'
    assert [n.text() for n in fields.direct('dd')]==[value for label,value in expected_fields],'Protocol scientific field changed'
    assert [n.text() for n in article.direct('p')]==['仅适用于：'+', '.join(variant['paper_ids']),variant['locator']]+['版本边界对照 ↗ '+src['locator'] for src in support],'Protocol scope or locator changed'
    for paragraph,src in zip(article.direct('p')[2:],support):
        link=one(paragraph.direct('a'),'supporting protocol source')
        assert link.attrs=={'href':src['source_url']} and link.text()=='版本边界对照 ↗','Supporting protocol source changed'
    source_link=one(article.direct('a'),'protocol source')
    assert source_link.attrs=={'href':variant['source_url']} and source_link.text()=='固定版本协议来源 ↗','Protocol source link changed'
assert [n.attrs['id'] for n in old_articles]==[n.attrs['id'] for n in new_articles],'Original catalog article order changed'
for old,new in zip(old_articles,new_articles):
    assert catalog_signature(old,False)==catalog_signature(new,True),(old.attrs['id'],'original catalog body changed')

print(json.dumps({'missingDynamicLegacyLinks':sorted(set(missing_dynamic))}))
`;
function assertCurrentPreservation(overrides={}){
 assert.equal(sha(fs.readFileSync(path.join(root,'tests/entry-baseline.json'))),'d3edd07e8eff1fb0e85e3b24537e8b1f3000c1563c0ceaadf3a7667234208807','entry baseline stays immutable');
 for(const [name,hash] of Object.entries(baseline.files)){
  if(name==='data/literature.js')continue; // Exact baseline + reviewed field replay is checked below.
  const target=historicalNames.has(name)?path.join(historicalRoot,name):path.join(root,name);
  assert.equal(sha(fs.readFileSync(target)),hash,name+' original source bytes');
 }
 const run=spawnSync('python3',['-c',preservationPython],{input:JSON.stringify({root,overrides}),encoding:'utf8',maxBuffer:4*1024*1024});
 assert.equal(run.status,0,run.stdout+run.stderr);
 const report=JSON.parse(run.stdout);
 for(const oldUrl of report.missingDynamicLegacyLinks){
  const absolute=new URL(oldUrl,'https://example.test/local-only/index.html');
  const f=fixture({url:absolute.href});assert.deepEqual(f.errors,[]);
  const prefix=absolute.hash.startsWith('#state=')?'#state=':'#analysis=';
  const state=JSON.parse(decodeURIComponent(absolute.hash.slice(prefix.length)));
  if(prefix==='#state='){
   assert.equal(f.app.getState().paper,state.paper);assert.equal(f.app.getState().tab,state.tab);
   const button=f.$('[data-open-analysis="'+state.paper+'"]');assert(button);button.emit('click');
   assert.equal(f.c2.getState().paperId,state.paper);
  }else{
   assert.equal(f.c2.getState().paperId,state.paperId);
   if(state.selected)assert.equal(f.c2.getState().selected,state.selected);
  }
 }
}
// A targeted mode lets corruption controls call the identical positive invariant.
if(process.argv.includes('--check-preservation')){
 assertCurrentPreservation(JSON.parse(fs.readFileSync(0,'utf8')||'{}'));
 console.log('PASS exact historical/current preservation invariant');process.exit(0);
}

test('editorial goal groups only the two field trees; single-paper template stays independent',()=>{const f=start(),dual=f.$('.goal-tab-group'),single=f.$('.single-paper-tab-group');assert(dual);assert(single);assert.deepEqual(dual.querySelectorAll('[role="tab"]').map(x=>x.dataset.key),['l','c']);assert.deepEqual(single.querySelectorAll('[role="tab"]').map(x=>x.dataset.key),['a']);assert(dual.querySelector('#shared-goal-title'));assert(single.querySelector('#single-paper-context-title'));assert.match(dual.textContent,/导航领域范围 · 编者整理/);assert.match(f.$('.editorial-adaptation').textContent,/非彭思达原文/);assert.match(f.$('.editorial-adaptation').textContent,/问答属于关联任务，不等同于导航/);assert.equal(dual.querySelectorAll('.goal-siblings').length,1);assert.equal(dual.querySelector('.goal-siblings').querySelectorAll('li').length,2);for(const key of ['l','c'])assert.equal(f.$('#global-tab-'+key).getAttribute('aria-describedby'),'shared-goal-title shared-goal-scope');assert.equal(f.$('#global-tab-a').getAttribute('aria-describedby'),'single-paper-scope');assert(!f.$('.editorial-adaptation').closest('.pengsida-original-method'));});
test('editorial context survives every entry switch without adding scientific roots',()=>{const f=start(),before=['l','c'].map(key=>{const t=f.window.TreeModel.atlas.paths(f.app.model,key);return [t.nodes.length,t.pathCount,t.paperCount,t.by.get(t.root).children.length];});for(const key of ['c','a','l','a','c','l']){f.click('#global-tab-'+key);assert(f.$('#shared-goal-scope'));assert(f.$('#single-paper-scope'));assert.deepEqual(['l','c'].map(k=>{const t=f.window.TreeModel.atlas.paths(f.app.model,k);return [t.nodes.length,t.pathCount,t.paperCount,t.by.get(t.root).children.length];}),before);}assert.equal(f.app.getState().globalTree,'l');});
test('initial literature tab and three sibling ARIA tabs',()=>{const f=start();assert.equal(f.app.getState().globalTree,'l');const tabs=f.$('.global-tabs').querySelectorAll('[role="tab"]');assert.deepEqual(tabs.map(x=>x.dataset.key),['l','c','a']);for(const tab of tabs){const key=tab.dataset.key,panel=f.$('#global-panel-'+key);assert(panel);assert.equal(panel.getAttribute('aria-labelledby'),tab.id);assert.equal(tab.getAttribute('aria-controls'),panel.id);assert.equal(panel.hidden,key!=='l');assert.equal(tab.getAttribute('tabindex'),key==='l'?'0':'-1');}});
test('all three tabs support wrap arrows, Home, End and focus',()=>{const f=start();for(const [key,expected] of [['ArrowRight','c'],['ArrowRight','a'],['ArrowRight','l'],['ArrowLeft','a'],['Home','l'],['End','a'],['ArrowLeft','c'],['Home','l']]){f.$('#global-tab-'+f.app.getState().globalTree).emit('keydown',{key});assert.equal(f.app.getState().globalTree,expected);assert.equal(f.document.activeElement.id,'global-tab-'+expected);for(const k of ['l','c','a']){assert.equal(f.$('#global-panel-'+k).hidden,k!==expected);assert.equal(f.$('#global-tab-'+k).getAttribute('aria-selected'),String(k===expected));}}});
test('analysis global state survives roundtrip and invalid input remains sanitized',()=>{const f=start(),M=f.window.TreeModel;choose(f);assert.equal(M.deserialize(f.app.model,M.serialize(f.app.getState())).globalTree,'a');assert.equal(M.sanitizeState(f.app.model,{globalTree:'invalid'}).globalTree,'l');for(const key of ['l','c'])assert.equal(M.deserialize(f.app.model,M.serialize({...f.app.getState(),globalTree:key})).globalTree,key);});
test('all original roots and every literature/challenge path remain navigable',()=>{const f=start(),M=f.window.TreeModel,m=f.app.model;assert.equal(M.rootOverview(m,'l','pipeline').length,19);assert.equal(M.rootOverview(m,'c').length,12);assert.equal(atlasRoots(f).length,12);assert.equal(f.$('#global-panel-l').querySelectorAll('.task-family').length,3);assert.deepEqual(new Set(M.taskMap.groups.flatMap(g=>g.sections.flatMap(s=>s.ids))),new Set(M.rootOverview(m,'l').map(x=>x.node.id)));for(const key of ['l','c'])for(const p of m.trees[key].paths){let s=M.initialState();if(key==='l'&&p.viewKind!=='protocol')s=M.reduce(m,s,{type:'facet',facet:p.viewKind});for(const id of p.nodeIds)s=M.reduce(m,s,{type:'enter',key,id});assert.equal(s.paper,p.paperId,p.id);assert.deepEqual(json(s.origin.path),json(p.nodeIds));const before=json(s);s=M.reduce(m,s,{type:'globalTree',key:'a'});s=M.reduce(m,s,{type:'globalTree',key:before.globalTree});assert.deepEqual(json(s),before,p.id);}});
test('analysis selector exposes every catalog paper, exactly two independently mapped papers',()=>{const f=start(),panel=choose(f),select=selector(f);assert(select);const ids=select.querySelectorAll('option').map(x=>x.getAttribute('value')).filter(Boolean);assert.equal(ids.length,39);assert.equal(new Set(ids).size,39);assert.deepEqual([...ids].sort(),[...f.app.model.papers.keys()].sort());assert(panel.querySelector('[data-open-analysis="harnessvln"]'));const options=select.querySelectorAll('option').filter(x=>x.getAttribute('value'));assert.equal(options.filter(x=>/待建立|待解析|待填/.test(x.textContent)).length,37);});
test('direct mapped sample opens existing 72-node,47-answer analysis and restores global context',()=>{const f=start();choose(f);f.window.scrollY=217;const before=json(f.app.getState());f.$('#global-panel-a').querySelector('[data-open-analysis="harnessvln"]').emit('click');assert(f.c2.isOpen());assert.equal(f.c2.getState().paperId,'harnessvln');assert.equal(f.c2.getModel().nodes.size,72);assert.equal(f.c2.getModel().answers.size,47);f.c2.returnToTrees();assert(!f.c2.isOpen());assert.deepEqual(json(f.app.getState()),before);assert.equal(f.window.scrollY,217);assert.equal(f.$('#global-panel-a').hidden,false);});
test('return from analysis without a selected paper focuses a visible tree control',()=>{const f=start();choose(f);f.$('#global-panel-a').querySelector('[data-open-analysis="harnessvln"]').emit('click');f.c2.returnToTrees();assert(f.document.activeElement);let el=f.document.activeElement;while(el){assert(!el.hidden,'focus target has hidden ancestor '+el.id);el=el.parentElement;}});
test('each of 37 pending choices opens an honest empty-answer template and returns',()=>{const f=start();choose(f);for(const id of f.app.model.papers.keys()){if(['harnessvln','navharness'].includes(id))continue;openSelection(f,id);assert.equal(f.c2.getState().paperId,id);const m=f.c2.getModel();assert.equal(m.mapping,null);assert.equal(m.answers.size,0);assert.equal(m.nodes.size,59);assert.match(f.$('#c2-app').textContent,/待建立|尚未建立/);f.c2.returnToTrees();assert.equal(f.app.getState().globalTree,'a');}});
test('branch, selected paper and facet survive analysis-tab entry and return',()=>{const f=start();const p=f.window.TreeModel.pathsForPaper(f.app.model,'harnessvln').find(p=>p.key==='l');f.app.dispatch({type:'path',key:'l',id:p.id});choose(f);const before=json(f.app.getState());f.$('#global-panel-a').querySelector('[data-open-analysis="harnessvln"]').emit('click');f.c2.returnToTrees();assert.deepEqual(json(f.app.getState()),before);});
test('back and forward retain analysis global and existing C2 history',()=>{const f=start();choose(f);f.$('#global-panel-a').querySelector('[data-open-analysis="harnessvln"]').emit('click');f.back();assert(!f.c2.isOpen());assert.equal(f.app.getState().globalTree,'a');f.forward();assert(f.c2.isOpen());assert.equal(f.c2.getState().paperId,'harnessvln');});
test('original scientific hashes and current complete content remain exact',()=>{assertCurrentPreservation();});
test('all original source blocks and links remain inside a closed native disclosure',()=>{const f=start(),source=baseline.sourceBlocks;const ids=Object.keys(source);assert.equal(ids.length,14);for(const id of ids){const el=f.$('[data-source-block="'+id+'"]');assert(el,id);let p=el,closed=false;while(p){if(p.tagName==='DETAILS'&&p.getAttribute('open')===null)closed=true;p=p.parentElement;}assert(closed,id+' must be in closed disclosure');const original=source[id];assert.equal(el.innerHTML||el.textContent,original.replace(/<br\s*\/?\s*>/g,''));}assert(f.$('a[href="https://github.com/pengsida/learning_research"]'));assert(f.$('[data-c2-range="baseline-weekly"]'));assert(f.$('#coverage'));const disclosure=f.$('details.entry-help');assert(disclosure);assert.equal(disclosure.getAttribute('open'),null);assert(disclosure.querySelector('summary'));for(const q of ['.pengsida-original-method','[data-c2-range="baseline-weekly"]','#coverage'])assert(disclosure.querySelector(q),q+' must be inside auxiliary disclosure');});
test('reset and global return focus visible active tabs from analysis and catalog',()=>{for(const mode of ['analysis','catalog'])for(const action of ['overview','global']){const f=start();choose(f);if(mode==='catalog')f.app.dispatch({type:'view',view:'catalog'});f.app.dispatch({type:action});assert.equal(f.document.activeElement.id,'global-tab-'+f.app.getState().globalTree);assert(!f.document.activeElement.classList.contains('sr-only'));let el=f.document.activeElement;while(el){assert(!el.hidden,'hidden ancestor '+el.id);el=el.parentElement;}if(action==='overview'){assert.equal(f.app.getState().globalTree,'l');assert.equal(f.app.getState().paper,null);}}});
console.log(`${count} passed, ${failed} failed; in-memory DOM only, browser/geometry NOT_RUN.`);process.exitCode=failed?1:0;

// Guided operation contracts. These assert actual DOM/state/focus targets and CSS
// layout rules, but do not substitute for independent rendered-browser QA.
let guided=0;
function guideTest(name,fn){fn();guided++;console.log('PASS guided: '+name);}
function visible(el){for(let p=el;p;p=p.parentElement)if(p.hidden)return false;return !!el;}
guideTest('three purpose labels explain why and original names remain secondary',()=>{const f=start();for(const [key,label,term] of [['l','看领域脉络','文献脉络树'],['c','看难点与解法','Challenge–Insight 树'],['a','读懂一篇论文','单篇解析树']]){const tab=f.$('#global-tab-'+key);assert(tab.textContent.includes(label));assert(tab.querySelector('small').textContent.includes(term));assert(tab.querySelector('span').textContent.length>8);}assert.equal(f.$('#branch-rail').hidden,true);assert.equal(f.$('[data-root-jump]'),null);assert.equal(f.$('[data-action="overview"]'),null);});
guideTest('GOAT keeps the three-family context and immediately targets its protocol and methods',()=>{const f=start();rootButton(f,'l','task-goat-sequence').emit('click');assert(f.$('#tree-workspace').classList.contains('is-focused'));assert.equal(f.$('#global-map').parentElement,f.$('#navigation').parentElement);assert.equal(f.$('#tree-l').hidden,false);assert.equal(f.$('#tree-c').hidden,true);assert.equal(f.document.activeElement.id,'focus-title-l');assert(f.$('#tree-l').querySelector('.protocol-summary'));assert.equal(f.window.scrollY,0);assertCompleteAtlas(f,'l');assert(f.$('#tree-l').textContent.includes('GOAT'));assert(f.$('#focus-title-l').textContent.includes('先核对协议'));assert.equal(f.$('#global-panel-l').querySelectorAll('.task-family').length,3);assert.equal(rootButton(f,'l','task-goat-sequence').getAttribute('aria-pressed'),'true');});
guideTest('narrow layout retains three native family buttons and complete protocol selection',()=>{const f=fixture({mobile:true,width:390,height:844});assert.deepEqual(f.errors,[]);f.window.scrollY=137;rootButton(f,'l','task-goat-sequence').emit('click');assertCompleteAtlas(f,'l');const panel=f.$('#global-panel-l'),group=f.window.TreeModel.taskMap.group('goal');assert.equal(panel.querySelectorAll('.task-family').length,3);for(const id of group.sections.flatMap(s=>s.ids))assert(panel.querySelector('.protocol-card[data-id="'+id+'"]'));assert.equal(f.window.scrollY,137);assert(visible(f.document.activeElement));const css=fs.readFileSync(path.join(root,'style.css'),'utf8');assert(css.includes('.task-family-grid'));assert(css.includes('@media(max-width:1000px)'));assert(css.includes('overflow:auto'));});
guideTest('all 19 protocols and 12 challenges produce visible focus in only the chosen tree',()=>{const f=start(),M=f.window.TreeModel;for(const key of ['l','c'])for(const item of M.rootOverview(f.app.model,key,key==='l'?'pipeline':undefined)){rootButton(f,key,item.node.id).emit('click');assert(!f.$('#tree-'+key).hidden,item.node.id);assert(f.$('#tree-'+(key==='l'?'c':'l')).hidden);assert.equal(f.document.activeElement.id,key==='l'?'focus-title-l':'tree-node-'+key+'-'+item.node.id);assert(visible(f.document.activeElement));assert(f.$('#tree-'+key).textContent.includes(key==='l'?M.taskMap.label(item.node.id):item.node.label));}});
guideTest('HarnessVLN reaches evidence through its real protocol and method with the complete source route',()=>{const f=start(),M=f.window.TreeModel,p=M.pathsForPaper(f.app.model,'harnessvln').find(x=>x.key==='l'&&x.viewKind==='pipeline');rootButton(f,'l',p.nodeIds[0]).emit('click');const current=f.$('#tree-l');assert(current.querySelector('.protocol-summary'));const method=current.querySelector('[data-method-id="'+p.nodeIds[1]+'"]');assert(method);assert.equal(method.querySelector('h4').textContent,f.app.model.trees.l.nodes.get(p.nodeIds[1]).label);const button=method.querySelector('[data-action="path"][data-id="'+p.id+'"]');assert(button);button.emit('click');assert.equal(f.app.getState().paper,'harnessvln');assert.equal(f.document.activeElement.id,'paper-title');assert.deepEqual(json(f.app.getState().origin.path),json(p.nodeIds));const route=f.$('.selected-task-route');assert(route);for(const id of p.nodeIds.slice(1))assert(route.textContent.includes(f.app.model.trees.l.nodes.get(id).label));assertCompleteAtlas(f,'l');});
guideTest('Challenge Back restores parent page, child focus and per-branch scroll; browser history restores document position',()=>{const f=start(),M=f.window.TreeModel;rootButton(f,'c',M.rootOverview(f.app.model,'c').find(x=>x.childCount>1).node.id).emit('click');const next=f.$('#tree-c').querySelector('[data-action="enter"]');f.$('#body-c').scrollTop=135;f.window.scrollY=421;next.focus();const id=next.dataset.id;next.emit('click');f.window.scrollY=609;f.back();assert.equal(f.app.getState().c.length,1);assert.equal(f.window.scrollY,421);assert.equal(f.$('#body-c').scrollTop,135);assert.equal(f.document.activeElement.dataset.id,id);f.forward();assert.equal(f.app.getState().c.length,2);assert.equal(f.window.scrollY,609);f.click('[data-action="back"][data-key="c"]');assert.equal(f.document.activeElement.dataset.id,id);assert.equal(f.$('#body-c').scrollTop,135);});
guideTest('return to overview clears protocol and keeps three family buttons with attached visible focus',()=>{const f=start();rootButton(f,'l','task-goat-sequence').emit('click');const back=f.$('#tree-l').querySelector('[data-action="global"]');assert(back);back.emit('click');assert.equal(f.app.getState().l.length,0);assert.equal(f.app.getState().taskGroup,null);assert.equal(f.$('#tree-l').hidden,false);assert(f.$('#tree-l').querySelector('.focus-empty'));assert.equal(f.$('#global-panel-l').querySelectorAll('.task-family').length,3);assert.equal(f.$('#global-panel-l').querySelectorAll('.protocol-card').length,0);assertCompleteAtlas(f,'l');assert(visible(f.document.activeElement));assert(f.document.querySelectorAll('[id],[data-action]').includes(f.document.activeElement),'focus points to detached branch');});
guideTest('Escape closes one canonical evidence panel and restores its visible source-path button',()=>{const f=start(),M=f.window.TreeModel,p=M.pathsForPaper(f.app.model,'harnessvln').find(x=>x.key==='l');f.app.dispatch({type:'path',key:'l',id:p.id});const leaf=f.$('#tree-l').querySelector('[data-action="path"][data-id="'+p.id+'"]');assert(leaf);leaf.emit('click');assert.equal(f.$$('#paper-panel').length,1);f.$('#paper-title').emit('keydown',{key:'Escape'});assert.equal(f.app.getState().paper,null);assert.equal(f.document.activeElement.dataset.id,p.id);assert.equal(f.document.activeElement.dataset.action,'path');assert(visible(f.document.activeElement));});
guideTest('search results are revealed rather than stranded above the search control',()=>{const f=start();f.$('#search').value='HarnessVLN';f.$('#search-form').emit('submit');assert.equal(f.app.getState().view,'catalog');assert.equal(f.document.activeElement.id,'catalog-title');assert(f.$('#catalog-panel').scrolled);const back=f.$('#catalog-panel').querySelector('[data-action="view"]');back.emit('click');assert.equal(f.app.getState().view,'trees');assert(visible(f.document.activeElement));});
guideTest('reset API still clears selection/query and lands on a visible purpose tab',()=>{const f=start();f.app.dispatch({type:'path',key:'l',id:f.app.model.trees.l.paths[0].id});f.app.dispatch({type:'search',query:'HarnessVLN'});f.app.dispatch({type:'overview'});assert.equal(f.app.getState().paper,null);assert.equal(f.app.getState().query,'');assert.equal(f.app.getState().l.length,0);assert.equal(f.document.activeElement.id,'global-tab-l');assert(visible(f.document.activeElement));});
console.log(guided+' guided operation contracts passed; actual browser viewport visibility remains NOT_RUN.');
guideTest('Challenge expansion grows a nested connected subtree without removing ancestors or sibling branches',()=>{const f=start(),M=f.window.TreeModel;const task=M.rootOverview(f.app.model,'c').find(x=>x.childCount>1);rootButton(f,'c',task.node.id).emit('click');const before=f.$('#tree-c').querySelectorAll('.node').map(x=>x.dataset.id),node=f.$('#tree-c').querySelector('[data-action="enter"]'),id=node.dataset.id;node.emit('click');const panel=f.$('#tree-c');assert(panel.querySelector('.graph-root').textContent.includes(task.node.label));for(const sibling of before)assert(panel.querySelector('[data-id="'+sibling+'"]'),'visible sibling removed: '+sibling);const expanded=panel.querySelector('[data-id="'+id+'"]');assert.equal(expanded.dataset.action,'crumb');assert.equal(expanded.getAttribute('aria-expanded'),'true');assert(expanded.closest('.read-tree-canvas'));const current=M.branch(f.app.model,f.app.getState(),'c'),edges=panel.querySelector('.read-tree-links').querySelectorAll('path');assert(current.items.every(x=>panel.querySelector('.node[data-id="'+x.node.id+'"]')&&edges.some(edge=>edge.dataset.source===id&&edge.dataset.target===x.node.id)));assert.equal(expanded.querySelector('strong').textContent,f.app.model.trees.c.nodes.get(id).label);expanded.emit('click');assert.equal(f.app.getState().c.length,1);assert.equal(f.$('#tree-c').querySelectorAll('.node').length,before.length);});
guideTest('Challenge ancestor sibling changes only the lower branch and uses a valid original path',()=>{const f=start(),M=f.window.TreeModel;const task=M.rootOverview(f.app.model,'c').find(x=>x.childCount>1);rootButton(f,'c',task.node.id).emit('click');let first=f.$('#tree-c').querySelector('[data-action="enter"]');first.emit('click');const sibling=f.$('#tree-c').querySelectorAll('[data-action="enter"][data-depth="1"]').find(x=>x.dataset.id!==first.dataset.id);assert(sibling);sibling.emit('click');assert.equal(f.app.getState().c.length,2);assert.equal(f.app.getState().c[1],sibling.dataset.id);assert(M.matchingPaths(f.app.model.trees.c,f.app.getState().c).length>0);assert.equal(f.$('#tree-c').querySelector('.graph-root').textContent.includes(task.node.label),true);});
guideTest('every original literature route and connected challenge path retain every source ancestor',()=>{const f=start(),M=f.window.TreeModel;for(const key of ['l','c'])for(const p of f.app.model.trees[key].paths){f.app.dispatch({type:'path',key,id:p.id},'replace');const panel=f.$('#tree-'+key);if(key==='l'){const route=f.$('.selected-task-route');assert(route,p.id);const steps=route.querySelectorAll('.route-step');assert.deepEqual(steps.map(el=>el.textContent),json(p.nodeIds.map((id,i)=>i?f.app.model.trees.l.nodes.get(id).label:M.taskMap.label(id))));assert(panel.querySelector('[data-action="path"][data-id="'+p.id+'"]'),p.id+' missing paper route');if(p.viewKind!=='protocol'){assert(panel.querySelector('[data-method-id="'+p.nodeIds[1]+'"]'));for(const id of p.nodeIds.filter(id=>f.app.model.trees.l.nodes.get(id).type==='module'))assert(panel.textContent.includes(f.app.model.trees.l.nodes.get(id).label),id);}}else{assert(panel.querySelector('.graph-root').textContent.includes(f.app.model.trees[key].nodes.get(p.nodeIds[0]).label),p.id);for(let depth=1;depth<p.nodeIds.length;depth++){const node=panel.querySelector('[data-id="'+p.nodeIds[depth]+'"]');assert(node,p.id+' missing ancestor/leaf '+p.nodeIds[depth]);assert(node.closest('.read-tree-canvas'));assert.equal(node.querySelector('strong').textContent,f.app.model.trees[key].nodes.get(p.nodeIds[depth]).label);assert(panel.querySelector('.read-tree-links').querySelectorAll('path').some(edge=>edge.dataset.source===p.nodeIds[depth-1]&&edge.dataset.target===p.nodeIds[depth]));assert.equal(Number(node.dataset.depth),depth);}}assert.equal(f.$$('#paper-panel').length,1);assert.equal(f.app.getState().paper,p.paperId);assert.deepEqual(json(f.app.getState().origin.path),json(p.nodeIds));}});
guideTest('source atlases preserve every occurrence and real edge; Challenge retains its visible complete atlas',()=>{const f=start();for(const key of ['l','c']){f.app.dispatch({type:'globalTree',key});const t=assertCompleteAtlas(f,key),roots=t.by.get(t.root).children,panel=f.$('#global-panel-'+key);if(key==='c'){assert(panel.querySelectorAll('.atlas-vertex').length<t.nodes.length);f.click('[data-atlas-mode="'+key+'"]');assertCompleteAtlas(f,key);assert.equal(f.$('#global-panel-'+key).querySelectorAll('.atlas-vertex').length,t.nodes.length);f.click('[data-atlas-mode="'+key+'"]');assertCompleteAtlas(f,key);}else{assertCompleteAtlas(f,key,'full');assert.equal(panel.querySelectorAll('.task-family').length,3);assert.equal(panel.querySelectorAll('.atlas-svg').length,0);}assert.equal(roots.length,key==='l'?19:12);assert.equal(t.nodes.filter(n=>!n.sourceId).length,1);assert.equal(t.by.get(t.root).type,'ui_root');for(const n of t.nodes)if(n.sourceId)assert(f.app.model.trees[key].nodes.has(n.sourceId));assert.equal(t.paperCount,39);assert.equal(t.pathCount,f.app.model.trees[key].paths.length);}assert.equal(f.app.model.trees.l.nodes.size,new Set(f.window.LITERATURE_TREE.nodes.map(n=>n.node_id)).size);});
console.log(guided+' total guided operation contracts passed; visual legibility still requires real-browser QA.');

guideTest('the readable Challenge tree uses the shared geometry with complete labels and actual parent edges',()=>{const f=start(),M=f.window.TreeModel;for(const key of ['c']){const p=M.pathsForPaper(f.app.model,'harnessvln').find(x=>x.key===key);f.app.dispatch({type:'path',key,id:p.id});const panel=f.$('#tree-'+key),canvas=panel.querySelector('.read-tree-canvas'),buttons=canvas.querySelectorAll('.node'),edges=panel.querySelector('.read-tree-links').querySelectorAll('path'),position=(el,k)=>Number(el.getAttribute('style').match(new RegExp('(?:^|;)'+k+':([0-9.]+)px'))[1]),items=buttons.map(el=>({id:el.dataset.id,sourceId:el.dataset.id,label:el.querySelector('strong').textContent,contentTitle:el.querySelector('.read-node-copy').querySelector('span').textContent,depth:Number(el.dataset.depth),children:edges.filter(edge=>edge.dataset.source===el.dataset.id).map(edge=>edge.dataset.target)})),root=items.find(n=>n.depth===0),scene=M.atlas.readableLayout(items,root.id,{width:position(canvas,'width')});assert.equal(edges.length,items.length-1);for(const n of scene.nodes){const el=buttons.find(el=>el.dataset.id===n.id);assert.equal(position(el,'left'),n.x);assert.equal(position(el,'top'),n.y);assert.equal(position(el,'width'),n.w);assert.equal(position(el,'height'),n.h);assert.equal(n.labelLines.join(''),f.app.model.trees[key].nodes.get(n.id).label.replace(/\n/g,''));}for(const edge of edges)assert(f.app.model.trees[key].paths.some(path=>path.nodeIds.some((id,i)=>id===edge.dataset.source&&path.nodeIds[i+1]===edge.dataset.target)));}});

// Empty scientific task roots stay visible and state their actual lack of paths.
guideTest('zero-mapping protocols explain empty coverage without inventing methods or papers',()=>{const f=start();const empty=f.window.TreeModel.rootOverview(f.app.model,'l').filter(item=>!item.paths.length);assert(empty.length);for(const root of empty){f.app.dispatch({type:'root',key:'l',id:root.node.id});const panel=f.$('#tree-l');assert(panel.querySelector('.empty-coverage').textContent.includes('没有此协议的完整方法挂载'));assert(panel.querySelector('.protocol-summary'));assert.equal(panel.querySelectorAll('.method-comparison').length,0);assert.equal(panel.querySelectorAll('.paper-chip').length,0);assert.equal(f.app.getState().paper,null);}});

guideTest('choosing Representation then clicking a neutral global task keeps Representation in the visible controls',()=>{const f=start();rootButton(f,'l','task-vln-ce').emit('click');f.click('[data-action="facet"][data-facet="representation"]');assert.equal(f.app.getState().lFacet,'representation');rootButton(f,'l','task-object-category').emit('click');assert.equal(f.app.getState().lFacet,'representation');assert.equal(f.$('[data-action="facet"][data-facet="representation"]').getAttribute('aria-pressed'),'true');assert.equal(f.app.getState().l[0],'task-object-category');});

// Regression for cross-view Back: the default historical fixture permits focus
// on hidden nodes, so these contracts deliberately enable its visibility guard.
function historyFixture(){const f=fixture({visibilityAwareFocus:true});assert.deepEqual(f.errors,[]);return f;}
function assertVisibleFocus(f){assert(f.document.activeElement,'no focused element');assert(visible(f.document.activeElement),'focus retained in a hidden view');assert(f.document.querySelectorAll('[id],[data-atlas-id]').includes(f.document.activeElement),'focus retained on a detached element');assert.deepEqual(f.document.rejectedHiddenFocus||[],[],'attempted to focus before revealing its view');}
for(const key of ['l','c','a'])for(const paperId of ['harnessvln','navharness','arxiv:2609.39915'])guideTest('Back/Forward restores visible '+key+' context from '+paperId,()=>{
 const f=historyFixture();f.click('#global-tab-'+key);
 if(key==='a'){const select=selector(f);select.value=paperId;select.emit('change');}
 else{const path=f.window.TreeModel.pathsForPaper(f.app.model,paperId).find(p=>p.key===key);assert(path);f.app.dispatch({type:'path',key,id:path.id});f.click('#tab-analysis');}
 const entry=f.$(key==='a'?'#global-panel-a':'#paper-panel').querySelector('[data-open-analysis="'+paperId+'"]');assert(entry);entry.focus();f.window.scrollY=215;
 const before=json(f.app.getState());entry.emit('click');assert(f.c2.isOpen());assert.equal(f.c2.getState().paperId,paperId);
 if(paperId==='arxiv:2609.39915'){assert.equal(f.c2.getModel().answers.size,0);assert.equal(f.c2.getModel().mapping,null);}
 f.window.scrollY=432;
 for(let repeat=0;repeat<2;repeat++){f.back();assert(!f.c2.isOpen());assert.deepEqual(json(f.app.getState()),before);assert.equal(f.window.scrollY,215,'analysis scroll overwrote return position');assertVisibleFocus(f);assert.equal(f.$('main').hidden,false);f.forward();assert(f.c2.isOpen());assert.equal(f.c2.getState().paperId,paperId);assert.equal(f.window.scrollY,432,'base scroll overwrote analysis return position');assertVisibleFocus(f);}
 f.back();assertVisibleFocus(f);
});
for(const paperId of ['harnessvln','navharness'])guideTest('unknown drawer history remains paper-scoped and returns visibly: '+paperId,()=>{
 const f=historyFixture();choose(f);openSelection(f,paperId);f.c2.dispatch({type:'drawer',drawer:'unresolved'});assert(f.c2.getState().drawer);f.back();assert(f.c2.isOpen());assert.equal(f.c2.getState().paperId,paperId);assert.equal(f.c2.getState().drawer,null);assertVisibleFocus(f);f.back();assert(!f.c2.isOpen());assert.equal(f.app.getState().globalTree,'a');assertVisibleFocus(f);f.forward();assert(f.c2.isOpen());f.forward();assert.equal(f.c2.getState().drawer,'unresolved');assertVisibleFocus(f);
});
for(const key of ['l','c'])guideTest('ordinary '+key+' branch Back/Forward keeps visible focus and location',()=>{
 const f=historyFixture();f.click('#global-tab-'+key);const root=f.window.TreeModel.rootOverview(f.app.model,key).find(n=>n.paths.length);if(key==='l')f.click('.task-family[data-id="'+f.window.TreeModel.taskMap.groupFor(root.node.id)+'"]');f.$('#global-tab-'+key).focus();const before=json(f.app.getState());rootButton(f,key,root.node.id).emit('click');const branch=json(f.app.getState());f.back();assert.deepEqual(json(f.app.getState()),before);assertVisibleFocus(f);f.forward();assert.deepEqual(json(f.app.getState()),branch);assertVisibleFocus(f);
});
console.log('13 strict-visibility Back/Forward contracts passed; browser acceptance remains NOT_RUN.');
