#!/usr/bin/env python3
"""Losslessly assemble/split the public frontier snapshot for small-file transport."""
import argparse, hashlib, json, os, re, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PARTS=ROOT/'data/frontier-parts'
OUTPUT=ROOT/'data/frontier.json'
CHUNK_BYTES=48000
MAX_PART_BYTES=60000

def sha(data):return hashlib.sha256(data).hexdigest()
def read_parts(directory=PARTS):
    directory=Path(directory).resolve()
    index=directory/'manifest.json'
    if index.is_symlink():raise ValueError('Symlinked manifest is not allowed')
    manifest=json.loads(index.read_text(encoding='utf-8'))
    if set(manifest)!={'schema_version','format','encoding','bytes','sha256','parts'} or manifest['schema_version']!=1 or manifest['format']!='raw_text_parts' or manifest['encoding']!='utf-8':raise ValueError('Unsupported part manifest')
    if not isinstance(manifest['parts'],list) or not manifest['parts'] or len(manifest['parts'])>1000:raise ValueError('Invalid part count')
    chunks=[];seen=set()
    for i,part in enumerate(manifest['parts'],1):
        if set(part)!={'path','bytes','sha256'} or part['path']!=f'part-{i:03d}.txt':raise ValueError('Parts must use ordered, safe names')
        if part['path'] in seen:raise ValueError('Duplicate part')
        seen.add(part['path']);path=directory/part['path']
        if path.is_symlink() or path.resolve().parent!=directory or not path.is_file():raise ValueError('Unsafe part path')
        data=path.read_bytes()
        if len(data)>MAX_PART_BYTES or len(data)!=part['bytes'] or sha(data)!=part['sha256']:raise ValueError('Part byte count or SHA-256 mismatch')
        data.decode('utf-8');chunks.append(data)
    payload=b''.join(chunks)
    if len(payload)!=manifest['bytes'] or sha(payload)!=manifest['sha256']:raise ValueError('Full snapshot byte count or SHA-256 mismatch')
    obj=json.loads(payload.decode('utf-8'))
    if obj.get('schema_version')!='1.0' or not isinstance(obj.get('papers'),list):raise ValueError('Invalid frontier JSON')
    return payload

def atomic_write(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.frontier-',delete=False) as handle:
        tmp=Path(handle.name);handle.write(payload)
    try:os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()

def assemble():
    payload=read_parts();atomic_write(OUTPUT,payload)
    return {'bytes':len(payload),'sha256':sha(payload)}

def split():
    payload=OUTPUT.read_bytes();payload.decode('utf-8');obj=json.loads(payload)
    if obj.get('schema_version')!='1.0' or not isinstance(obj.get('papers'),list):raise ValueError('Invalid frontier JSON')
    PARTS.mkdir(parents=True,exist_ok=True)
    entries=[];start=0
    while start<len(payload):
        end=min(start+CHUNK_BYTES,len(payload))
        while True:
            try:payload[start:end].decode('utf-8');break
            except UnicodeDecodeError:end-=1
        chunk=payload[start:end];name=f'part-{len(entries)+1:03d}.txt'
        atomic_write(PARTS/name,chunk);entries.append({'path':name,'bytes':len(chunk),'sha256':sha(chunk)});start=end
    manifest={'schema_version':1,'format':'raw_text_parts','encoding':'utf-8','bytes':len(payload),'sha256':sha(payload),'parts':entries}
    atomic_write(PARTS/'manifest.json',(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
    # Remove only obsolete generated pieces with the exact public naming convention.
    wanted={p['path'] for p in entries}
    for p in PARTS.iterdir():
        if re.fullmatch(r'part-\d{3}\.txt',p.name) and p.name not in wanted and p.is_file() and not p.is_symlink():p.unlink()
    if read_parts()!=payload:raise ValueError('Round-trip mismatch')
    return {'parts':len(entries),'bytes':len(payload),'sha256':sha(payload)}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--split',action='store_true',help='Export the current full snapshot to lossless small text parts');args=parser.parse_args()
    print(json.dumps(split() if args.split else assemble(),sort_keys=True))
if __name__=='__main__':main()
