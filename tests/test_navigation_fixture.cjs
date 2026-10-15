'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {snapshot,unchanged}=require('./helpers/navigation_fixture.cjs');
for(const mode of ['read','content','same-bytes','add','remove','replace','symlink'])test('shared navigation fixture integrity: '+mode,t=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'navigation-fixture-'));t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
 const file=path.join(root,'page.html');fs.writeFileSync(file,'exact preview');const before=snapshot(root);
 if(mode==='read'){assert.equal(fs.readFileSync(file,'utf8'),'exact preview');unchanged(root,before);return;}
 if(mode==='content')fs.writeFileSync(file,'other preview');
 if(mode==='same-bytes')fs.writeFileSync(file,'exact preview');
 if(mode==='add')fs.writeFileSync(path.join(root,'extra'),'extra');
 if(mode==='remove')fs.unlinkSync(file);
 if(mode==='replace'){fs.writeFileSync(path.join(root,'replacement'),'exact preview');fs.renameSync(path.join(root,'replacement'),file);}
 if(mode==='symlink'){fs.unlinkSync(file);fs.symlinkSync('missing',file);}
 assert.throws(()=>unchanged(root,before));
});
