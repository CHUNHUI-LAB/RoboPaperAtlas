'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
// Include bytes and inode/timestamp metadata: same-byte writes and replacements
// must fail too. Reject links and special files rather than following them.
function snapshot(root){
 const rows=[];
 function walk(name){
  const file=path.join(root,name),s=fs.lstatSync(file,{bigint:true});
  assert.ok(s.isFile()||s.isDirectory(),'fixture contains a link or special file: '+name);
  rows.push([name,s.isDirectory()?'d':'f',String(s.mode),String(s.ino),String(s.size),String(s.mtimeNs),String(s.ctimeNs),s.isFile()?crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'):null]);
  if(s.isDirectory())for(const child of fs.readdirSync(file).sort())walk(path.join(name,child));
 }
 walk('');return JSON.stringify(rows);
}
function unchanged(root,expected){assert.equal(snapshot(root),expected,'production preview fixture was modified by a scenario');}
module.exports={snapshot,unchanged};
