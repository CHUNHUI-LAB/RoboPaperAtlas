/* Display adapters only: raw catalog flags and report records stay unchanged. */
(function(root){
 'use strict';
 const stages=[['stage1','初读','first-pass.html'],['stage2','写作精读','writing-close-reading.html'],['stage3','方法精读','method-code-reading.html']];
 function overlayStatus(p){
  const o=p.verified_overlay||{};if(!o.title||!o.authors)return null;
  if(['verified_primary_metadata','official_publication_metadata_verified','published'].includes(p.publication_status)&&o.publication_year)return '正式书目已核验（独立补充）';
  return p.publication_status==='preprint_metadata_verified_publication_unresolved'?'预印本书目已核验（正式出版未确认）':null;
 }
 function metadataLabel(p){return overlayStatus(p)||(p.citation_verified?'来源已核验':'原始书目待核验')}
 function currentReports(p){
  if(!/^[a-z0-9][a-z0-9-]*$/.test(p.id||''))return [];
  return stages.flatMap(([stage,label,file],index)=>{
   const state=p.stages?.[stage],a=state?.status==='imported'?state.artifacts?.[0]:null;
   if(!a||a.kind!=='html'||!/^v[1-9][0-9]*$/.test(a.version||'')||!['approved','content_approved'].includes(a.review_status))return [];
   const expected='artifacts/'+p.id+'/'+a.version+'/'+file;
   if(a.path!==expected)return [];
   return [{stage,label,index:index+1,artifact:a,path:expected}];
  });
 }
 function pdfNoteHeading(p){return '以下是 '+(p.verified_at||'未注明日期')+' 的书目／链接核验记录；后续阅读范围见各阶段报告。'}
 const api=Object.freeze({overlayStatus,metadataLabel,currentReports,pdfNoteHeading});
 if(typeof module==='object'&&module.exports)module.exports=api;else root.RoboPaperPresentation=api;
})(typeof globalThis==='object'?globalThis:this);
