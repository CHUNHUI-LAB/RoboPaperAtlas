"""Authenticated preview transport with derived current reading-state output."""
import hashlib,json,re
from pathlib import Path
from preview_reading import hydrate_reading_stages
ROUTE='atlas-global-preview/index.html'
def digest(b):return hashlib.sha256(b).hexdigest()
def pairs(items):
 out={}
 for k,v in items:
  if k in out:raise ValueError('Duplicate preview manifest field')
  out[k]=v
 return out
def read_preview(root):
 directory=Path(root)/'data/atlas-global-preview-parts';index=directory/'manifest.json'
 if directory.is_symlink() or index.is_symlink():raise ValueError('Symlinked preview input')
 m=json.loads(index.read_text(),object_pairs_hook=pairs)
 if set(m)!={'schema_version','format','route','bytes','sha256','parts'} or (type(m['schema_version'])is not int or m['schema_version']!=1) or m['format']!='raw_utf8_html_parts' or m['route']!=ROUTE:raise ValueError('Unsupported preview manifest')
 if type(m['bytes']) is not int or not 0<m['bytes']<=1000000 or not re.fullmatch('[0-9a-f]{64}',m['sha256']):raise ValueError('Invalid preview payload metadata')
 if not isinstance(m['parts'],list) or not 1<=len(m['parts'])<=24:raise ValueError('Invalid preview parts')
 data=[]
 for i,item in enumerate(m['parts'],1):
  if set(item)!={'path','bytes','sha256'} or item['path']!=f'part-{i:03d}.txt' or type(item['bytes'])is not int or not 0<item['bytes']<=60000 or not re.fullmatch('[0-9a-f]{64}',item['sha256']):raise ValueError('Invalid preview part')
  p=directory/item['path']
  if p.is_symlink() or not p.is_file() or p.resolve().parent!=directory.resolve():raise ValueError('Unsafe preview part')
  b=p.read_bytes();b.decode('utf8')
  if len(b)!=item['bytes'] or digest(b)!=item['sha256']:raise ValueError('Preview part integrity mismatch')
  data.append(b)
 payload=b''.join(data)
 if len(payload)!=m['bytes'] or digest(payload)!=m['sha256']:raise ValueError('Preview integrity mismatch')
 if not payload.startswith(b'<!doctype html>') or b'id="atlas-data"'not in payload:raise ValueError('Expected standalone design preview')
 return payload
def write_preview(root,output):
 output=Path(output).resolve();directory=output/'atlas-global-preview'
 if directory.is_symlink():raise ValueError('Symlinked preview destination')
 directory.mkdir(parents=True,exist_ok=True);target=directory/'index.html'
 if target.is_symlink() or output not in target.resolve().parents:raise ValueError('Unsafe preview destination')
 payload=hydrate_reading_stages(read_preview(root),root,'atlas-data');target.write_bytes(payload);return digest(payload)
