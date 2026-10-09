/* Exact, lazy scientific content. Tree identity and navigation never depend on a request. */
(function(root){
'use strict';
function own(o,k){return !!o&&Object.prototype.hasOwnProperty.call(o,k);}
function need(value,message){if(!value)throw new Error(message);}
function equal(a,b){if(a===b)return true;if(!a||!b||typeof a!=='object'||typeof b!=='object')return false;var x=Object.keys(a).sort(),y=Object.keys(b).sort();return x.length===y.length&&x.every(function(k,i){return k===y[i]&&equal(a[k],b[k]);});}
function hash(bytes){need(root.crypto&&root.crypto.subtle,'浏览器不支持完整性校验');return root.crypto.subtle.digest('SHA-256',bytes).then(function(v){return Array.from(new Uint8Array(v)).map(function(n){return n.toString(16).padStart(2,'0');}).join('');});}
function restoreScopeCoverage(bundle){
 var d=bundle.delivery||{},encoding=d.scopeCoverageEncoding,refs=d.scopeCoverageIds,directoryRefs=d.directoryCoverageIds,scopes=Object.create(null),coverage=bundle.coverage||{},directory=Object.create(null);
 bundle.scopes.forEach(function(s){need(!own(scopes,s.id),'阅读范围身份重复');scopes[s.id]=s;});
 bundle.directory.forEach(function(row){need(!own(directory,row.id),'目录身份重复');directory[row.id]=row;});
 if(encoding===undefined){need(refs===undefined&&directoryRefs===undefined,'覆盖引用缺少编码');Object.keys(coverage).forEach(function(id){need(own(scopes,id)&&own(scopes[id],'coverage')&&own(scopes[id],'coveragePolicy'),'未编码的阅读覆盖缺失');});Object.keys(directory).forEach(function(id){need(own(directory[id],'coverage'),'未编码的目录覆盖缺失');});return;}
 need(encoding==='coverage-and-policy-by-scope-id-v1','未知阅读覆盖编码');
 need(Array.isArray(refs)&&refs.every(function(id){return typeof id==='string';})&&new Set(refs).size===refs.length&&equal(refs.slice().sort(),Object.keys(coverage).sort()),'阅读覆盖引用清单不符');
 Object.keys(scopes).forEach(function(id){if(refs.indexOf(id)<0)need(own(scopes[id],'coverage')&&(scopes[id].isVirtual||own(scopes[id],'coveragePolicy')),'阅读范围同时缺少内联与引用覆盖');});
 var prepared=[];refs.forEach(function(id){need(own(scopes,id)&&!own(scopes[id],'coverage')&&!own(scopes[id],'coveragePolicy'),'阅读覆盖引用未知或冲突');var c=coverage[id];need(c&&c.scopeId===id&&c.coveragePolicy&&typeof c.coveragePolicy==='object'&&!Array.isArray(c.coveragePolicy),'阅读覆盖身份不符');prepared.push({scope:scopes[id],coverage:JSON.parse(JSON.stringify(c)),policy:JSON.parse(JSON.stringify(c.coveragePolicy))});});
 var directoryPrepared=[];if(directoryRefs===undefined){Object.keys(directory).forEach(function(id){need(own(directory[id],'coverage'),'未编码的目录覆盖缺失');});}else{need(Array.isArray(directoryRefs)&&directoryRefs.every(function(id){return typeof id==='string';})&&new Set(directoryRefs).size===directoryRefs.length&&equal(directoryRefs.slice().sort(),Object.keys(directory).sort()),'目录覆盖引用清单不符');directoryRefs.forEach(function(id){need(own(coverage,id)&&!own(directory[id],'coverage'),'目录覆盖引用未知或冲突');directoryPrepared.push({entry:directory[id],coverage:JSON.parse(JSON.stringify(coverage[id]))});});}
 prepared.forEach(function(row){row.scope.coverage=row.coverage;row.scope.coveragePolicy=row.policy;});directoryPrepared.forEach(function(row){row.entry.coverage=row.coverage;});delete d.scopeCoverageEncoding;delete d.scopeCoverageIds;delete d.directoryCoverageIds;
}
function create(bundle){
 var delivery=bundle.delivery;if(!delivery)return null;
 need(delivery.schemaVersion==='navigation-delivery/1'&&/^[a-f0-9]{64}$/.test(delivery.sourceModelSha256),'分片清单版本不符');
 restoreScopeCoverage(bundle);
 var cache=Object.create(null),jobs=Object.create(null),attempts=Object.create(null),errors=Object.create(null),progress=Object.create(null),listeners=[],timeout=20000;
 // Preserve the validated index metadata, even after a full record is installed.
 var metadata={entities:JSON.parse(JSON.stringify(bundle.entities)),claims:JSON.parse(JSON.stringify(bundle.claims))};
 function notify(id){listeners.forEach(function(fn){fn(id);});}
 function projection(table,row){var result={},omit=delivery.recordOmissions[table]||[];Object.keys(row).forEach(function(k){if(omit.indexOf(k)<0)result[k]=row[k];});return result;}
 function validate(id,packet){
  need(own(delivery.packets,id),'未知正文分片');var expected=delivery.packets[id];
  need(packet&&packet.schemaVersion==='navigation-content-packet/1'&&packet.sourceModelSha256===delivery.sourceModelSha256&&packet.ownerId===id,'正文来源版本或所属节点不符');
  need(equal(Object.keys(packet).sort(),['claims','entities','ownerId','relations','schemaVersion','sourceModelSha256'].sort()),'正文分片出现未知字段');
  ['entities','claims'].forEach(function(table){var ids=expected[table==='entities'?'entityIds':'claimIds'];need(packet[table]&&equal(Object.keys(packet[table]).sort(),ids.slice().sort()),'正文记录范围不符');Object.keys(packet[table]).forEach(function(key){var row=packet[table][key];need(own(metadata[table],key)&&row.id===key&&equal(projection(table,row),metadata[table][key]),'正文论文、版本或记录身份不符');});});
  need(Array.isArray(packet.relations),'正文关系缺失');packet.relations.forEach(function(rel){var start=rel.from||rel.fromId,end=rel.to||rel.toId;need(own(bundle.entities,start)&&own(bundle.entities,end),'正文关系端点不存在');var d=rel.detail||{},refs=rel.claimIds||rel.evidence_refs||d.claimIds||d.evidence_refs||[];refs.forEach(function(cid){if(own(bundle.claims,cid))need(own(packet.claims,cid),'正文关系证据闭包缺失');});});
  Object.keys(packet.entities).forEach(function(eid){(packet.entities[eid].claimIds||[]).forEach(function(cid){need(own(packet.claims,cid),'正文实体证据闭包缺失');});});
  return packet;
 }
 function install(id,packet){validate(id,packet);['entities','claims'].forEach(function(table){Object.keys(packet[table]).forEach(function(key){bundle[table][key]=packet[table][key];});});cache[id]=packet;delete errors[id];return packet;}
 Object.keys(delivery.initialPackets||{}).forEach(function(id){install(id,delivery.initialPackets[id]);});
 function status(id){return cache[id]?'ready':jobs[id]?'loading':errors[id]?'failed':'idle';}
 function request(id,retry){
  if(cache[id])return Promise.resolve(cache[id]);if(jobs[id])return jobs[id];
  if(!own(delivery.packets,id))return Promise.reject(new Error('未知正文节点'));
  if(errors[id]&&!retry)return Promise.reject(errors[id]);
  var count=attempts[id]||0;if(count>=3)return Promise.reject(errors[id]||new Error('正文重试次数已用完'));
  attempts[id]=count+1;delete errors[id];var spec=delivery.packets[id],controller=root.AbortController?new root.AbortController():null,active=true,started=Date.now(),timer;
  var info=progress[id]={phase:'fetch',elapsedMs:0,receivedBytes:0,expectedBytes:spec.bytes,attempt:count+1,sourceModelSha256:delivery.sourceModelSha256,packetSha256:spec.sha256};
  function phase(value){if(active){info.phase=value;info.elapsedMs=Date.now()-started;}}
  function check(){need(active,'旧正文请求已结束');}
  var work=Promise.resolve().then(function(){check();need(/^[a-f0-9]{64}$/.test(spec.sha256)&&Number.isInteger(spec.bytes)&&spec.bytes>0,'正文配置无效');return root.fetch('content/'+spec.sha256+'.json',{credentials:'same-origin',signal:controller&&controller.signal});}).then(function(response){check();need(response.ok,'正文HTTP '+response.status);phase('body');
   if(response.body&&response.body.getReader){var reader=response.body.getReader(),chunks=[];return (function read(){return reader.read().then(function(part){check();if(part.done){var bytes=new Uint8Array(info.receivedBytes),offset=0;chunks.forEach(function(chunk){bytes.set(chunk,offset);offset+=chunk.byteLength;});return bytes.buffer;}info.receivedBytes+=part.value.byteLength;need(info.receivedBytes<=spec.bytes,'正文超过已核字节长度');chunks.push(part.value);return read();});}());}
   return response.arrayBuffer().then(function(bytes){check();info.receivedBytes=bytes.byteLength;return bytes;});
  }).then(function(bytes){check();need(bytes.byteLength===spec.bytes,'正文字节长度不符');phase('hash');return hash(bytes).then(function(actual){check();need(actual===spec.sha256,'正文字节与已核分片不一致');phase('parse');var packet=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));phase('identity');validate(id,packet);check();return packet;});});
  var deadline=new Promise(function(_,reject){timer=setTimeout(function(){if(!active)return;active=false;if(controller)controller.abort();info.elapsedMs=Date.now()-started;reject(new Error('正文加载超时，阶段：'+info.phase));},timeout);});
  jobs[id]=Promise.race([work,deadline]).then(function(packet){check();install(id,packet);phase('ready');return packet;},function(error){errors[id]=error;info.elapsedMs=Date.now()-started;throw error;}).finally(function(){active=false;clearTimeout(timer);delete jobs[id];notify(id);});
  return jobs[id];
 }
 return {ready:function(id){return !!cache[id];},status:status,request:request,relations:function(id){return cache[id]?cache[id].relations:[];},attempts:function(id){return attempts[id]||0;},error:function(id){return errors[id]&&errors[id].message;},diagnostics:function(id){return progress[id]?JSON.parse(JSON.stringify(progress[id])):null;},subscribe:function(fn){listeners.push(fn);},validate:validate};
}
root.NavigationContent={create:create,hash:hash};
}(window));
