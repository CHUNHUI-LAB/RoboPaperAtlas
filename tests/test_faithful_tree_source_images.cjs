'use strict';
// Mandatory acceptance gate. Defensive unavailable UI is never a substitute.
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {SOURCE_IMAGES}=require('../previews/radar-c2-analysis/analysis/c2.js').FaithfulTree;
const expected={dual:{sha256:'c69e3c4cbd47a74b7a98b7b26c02e0b4ff8df49584fffafb26c0c2f6a8791e64',bytes:718155,width:2048,height:1421},analysis:{sha256:'60b1b2e8e38d912de02c18873e1c9b261fb6625564330d454c28326ef4b4aee6',bytes:502548,width:1225,height:2048}};
for(const [id,e]of Object.entries(expected)){
 const im=SOURCE_IMAGES[id];assert(im&&typeof im.data==='string'&&im.data.startsWith('data:image/png;base64,'),'BLOCKED: original '+id+' image bytes missing');
 const b=Buffer.from(im.data.split(',')[1],'base64');assert.equal(b.length,e.bytes);assert.equal(crypto.createHash('sha256').update(b).digest('hex'),e.sha256);assert.equal(im.sha256,e.sha256);assert.equal(im.width,e.width);assert.equal(im.height,e.height);assert.equal(im.status,'exact_bytes_verified');assert.equal(b.readUInt32BE(16),e.width);assert.equal(b.readUInt32BE(20),e.height);
}
console.log('PASS mandatory source-image gate: two exact PNG byte streams, hashes and full dimensions verified; browser NOT_RUN');
