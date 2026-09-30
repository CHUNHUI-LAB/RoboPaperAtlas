"""Strict lossless transport for separately reviewed standalone reader previews."""
import hashlib,json,re
from pathlib import Path
ROUTE='reader-theme-preview/umi-on-legs/first-pass.html'
PREVIEWS={
 ROUTE:'reader-theme-preview-parts',
 'reader-theme-preview/umi-on-legs/writing-close-reading.html':'reader-theme-preview-stage2-parts',
 'reader-theme-preview/umi-on-legs/method-code-reading.html':'reader-theme-preview-stage3-parts',
}
def digest(b):return hashlib.sha256(b).hexdigest()
def valid_hash(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
def pairs(items):
 out={}
 for k,v in items:
  if k in out:raise ValueError('Duplicate preview manifest field')
  out[k]=v
 return out
def read_preview(root,route=ROUTE):
 if route not in PREVIEWS:raise ValueError('Unlisted preview route')
 directory=Path(root)/'data'/PREVIEWS[route];index=directory/'manifest.json'
 if directory.parent.is_symlink() or directory.is_symlink() or index.is_symlink():raise ValueError('Symlinked preview input')
 m=json.loads(index.read_text(encoding='utf8'),object_pairs_hook=pairs)
 if not isinstance(m,dict) or set(m)!={'schema_version','format','route','bytes','sha256','parts'} or (type(m['schema_version'])is not int or m['schema_version']!=1) or m['format']!='raw_utf8_html_parts' or m['route']!=route:raise ValueError('Unsupported preview manifest')
 if type(m['bytes']) is not int or not 0<m['bytes']<=2000000 or not valid_hash(m['sha256']):raise ValueError('Invalid preview payload metadata')
 if not isinstance(m['parts'],list) or not 1<=len(m['parts'])<=48:raise ValueError('Invalid preview parts')
 data=[]
 for i,item in enumerate(m['parts'],1):
  if not isinstance(item,dict) or set(item)!={'path','bytes','sha256'} or item['path']!=f'part-{i:03d}.txt' or type(item['bytes'])is not int or not 0<item['bytes']<=60000 or not valid_hash(item['sha256']):raise ValueError('Invalid preview part')
  p=directory/item['path']
  if p.is_symlink() or not p.is_file() or p.resolve().parent!=directory.resolve():raise ValueError('Unsafe preview part')
  b=p.read_bytes();b.decode('utf8')
  if len(b)!=item['bytes'] or digest(b)!=item['sha256']:raise ValueError('Preview part integrity mismatch')
  data.append(b)
 payload=b''.join(data)
 if len(payload)!=m['bytes'] or digest(payload)!=m['sha256']:raise ValueError('Preview integrity mismatch')
 if not payload.startswith(b'<!doctype html>') or b'<article class="reader-article">'not in payload or b'name="robots" content="noindex,nofollow"'not in payload:raise ValueError('Expected standalone design preview')
 return payload
def _write_payload(output,route,payload):
 output=Path(output)
 if output.is_symlink():raise ValueError('Symlinked preview output root')
 output=output.resolve();directory=output
 for part in Path(route).parts[:-1]:
  directory=directory/part
  if directory.is_symlink():raise ValueError('Symlinked preview destination')
  directory.mkdir(exist_ok=True)
 target=output/route
 if target.is_symlink() or output not in target.resolve().parents:raise ValueError('Unsafe preview destination')
 target.write_bytes(payload);return digest(payload)
def write_preview(root,output,route=ROUTE):
 return _write_payload(output,route,read_preview(root,route))
def write_previews(root,output):
 # Validate every input before writing any page, so a broken collection is rejected.
 payloads={route:read_preview(root,route) for route in PREVIEWS}
 return {route:_write_payload(output,route,payload) for route,payload in payloads.items()}
