'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),ui=require('../assets/presentation.js');
const papers=JSON.parse(fs.readFileSync(path.join(root,'data/catalog.json'),'utf8')).papers;
const byid=Object.fromEntries(papers.map(p=>[p.id,p]));
test('DeepWBC current readers route to reviewed stages while original artifacts stay intact',()=>{
 assert.deepEqual(ui.currentReports(byid['rpa-0012']).map(x=>x.path),['papers/rpa-0012/reading/stage1.html','papers/rpa-0012/reading/stage2.html','papers/rpa-0012/reading/stage3.html']);
 assert.deepEqual(['stage1','stage2','stage3'].map(stage=>byid['rpa-0012'].stages[stage].artifacts[0].path),['artifacts/rpa-0012/v2/first-pass.html','artifacts/rpa-0012/v1/writing-close-reading.html','artifacts/rpa-0012/v1/method-code-reading.html']);
});
test('UMI current readers use mixed-stage versions without mutating frozen paths',()=>{
 assert.deepEqual(ui.currentReports(byid['rpa-0062']).map(x=>x.path),['papers/rpa-0062/reading/stage1.html','papers/rpa-0062/reading/stage2.html','papers/rpa-0062/reading/stage3.html']);
});
test('RoboDuet current readers include all three reviewed author-manuscript stages',()=>{
 assert.deepEqual(ui.currentReports(byid['rpa-0052']).map(x=>x.path),['papers/rpa-0052/reading/stage1.html','papers/rpa-0052/reading/stage2.html','papers/rpa-0052/reading/stage3.html']);
 assert.equal(byid['rpa-0052'].stages.stage3.status,'imported');
 assert.equal(byid['rpa-0052'].stages.stage1.artifacts[0].path,'artifacts/rpa-0052/v1/first-pass.html');
 assert.equal(byid['rpa-0052'].stages.stage2.artifacts[0].path,'artifacts/rpa-0052/v1/writing-close-reading.html');
});
test('historical UMI and DeepWBC artifact identities are not redirected to current views',()=>{
 for(const [id,stage,version,file] of [['rpa-0062','stage2','v3','writing-close-reading.html'],['rpa-0062','stage1','v2','first-pass.html'],['rpa-0012','stage1','v1','first-pass.html']]){
  const path=`artifacts/${id}/${version}/${file}`;assert.equal(ui.reportEntryPath(id,stage,path,version),path);
 }
});
test('malformed, external, traversal, other-paper and stage/file mismatch paths fail closed',()=>{
 const bad=['https://evil.example/report.html','//evil.example/report.html','artifacts/rpa-0012/v2/../../secret.html','artifacts/rpa-0062/v2/first-pass.html','artifacts/rpa-0012/v2/method-code-reading.html','artifacts/rpa-0012/v2/any.html','artifacts/rpa-0012/v2/first-pass.html?x=1','artifacts/rpa-0012/v2/first-pass.html#x','artifacts/rpa-0012/v2/%66irst-pass.html'];
 for(const value of bad){const p=structuredClone(byid['rpa-0012']);p.stages.stage1.artifacts[0].path=value;assert(!ui.currentReports(p).some(x=>x.stage==='stage1'),value)}
});
test('unknown stages, unsafe versions and unapproved artifacts are not linked',()=>{
 const p=structuredClone(byid['rpa-0012']);p.stages.stage4=p.stages.stage1;assert.equal(ui.currentReports(p).length,3);
 for(const change of [{version:'../v2'},{review_status:'pending'},{kind:'pdf'}]){const q=structuredClone(p);Object.assign(q.stages.stage1.artifacts[0],change);assert(!ui.currentReports(q).some(x=>x.stage==='stage1'))}
 const q=structuredClone(p);q.id='../rpa-0012';assert.deepEqual(ui.currentReports(q),[]);
});
test('paper and report records are never mutated',()=>{const before=JSON.stringify(papers);for(const p of papers){ui.currentReports(p);ui.metadataLabel(p);ui.pdfNoteHeading(p)}assert.equal(JSON.stringify(papers),before)});
test('formal overlay, raw state and old PDF check remain explicitly scoped',()=>{
 const p=byid['rpa-0012'];assert.equal(p.citation_verified,false);assert.equal(ui.metadataLabel(p),'正式书目已核验（独立补充）');assert.equal(ui.metadataLabel(byid['rpa-0002']),'原始书目待核验');const pre=structuredClone(byid['rpa-0002']);pre.verified_overlay.title=pre.title;assert.match(ui.metadataLabel(pre),/正式出版未确认/);assert.match(ui.pdfNoteHeading(p),/2026-09-30.*后续阅读范围见各阶段报告/);
});
test('helper loads before interface; live drawer uses tested path function',()=>{
 const build=fs.readFileSync(path.join(root,'scripts/build.py'),'utf8');assert(build.indexOf("asset_url(prefix,'presentation.js')")<build.indexOf("asset_url(prefix,'interface.js')"));
 const uiSource=fs.readFileSync(path.join(root,'assets/interface.js'),'utf8');assert.match(uiSource,/presentation\.currentReports\(p\)/);assert.match(uiSource,/已导入报告所用版本/);assert(!uiSource.includes('artifacts\\/rpa-0062'));
});
