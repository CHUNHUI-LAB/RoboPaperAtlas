'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const api=require('../assets/presentation.js');
const catalog=require('../data/catalog.json');
for(const id of ['harnessvln','navharness','holoagent-0']){
 test(id+' maps only exact v2 Stage1 to current route',()=>{
  assert.equal(api.reportEntryPath(id,'stage1',`artifacts/${id}/v2/first-pass.html`,'v2'),`papers/${id}/reading/stage1.html`);
  assert.equal(api.reportEntryPath(id,'stage1',`artifacts/${id}/v1/first-pass.html`,'v1'),`artifacts/${id}/v1/first-pass.html`);
  assert.equal(api.reportEntryPath(id,'stage1',`artifacts/${id}/v3/first-pass.html`,'v3'),`artifacts/${id}/v3/first-pass.html`);
  assert.equal(api.reportEntryPath(id,'stage2',`artifacts/${id}/v2/writing-close-reading.html`,'v2'),`artifacts/${id}/v2/writing-close-reading.html`);
  assert.equal(api.reportEntryPath(id,'stage1',`artifacts/${id}/v1/first-pass.html`,'v2'),null);
  const actual=catalog.papers.find(p=>p.id===id);
  assert.deepEqual(api.currentReports(actual),[]);
  const synthetic=structuredClone(actual);
  synthetic.stages.stage1={status:'imported',artifacts:[{kind:'html',version:'v2',path:`artifacts/${id}/v2/first-pass.html`,review_status:'content_approved'}]};
  assert.equal(api.currentReports(synthetic)[0].path,`papers/${id}/reading/stage1.html`);
  synthetic.stages.stage1.artifacts[0].review_status='pending_candidate';
  assert.deepEqual(api.currentReports(synthetic),[]);
  synthetic.stages.stage1.artifacts[0].review_status='preview_pending';
  assert.deepEqual(api.currentReports(synthetic),[]);
 });
}
