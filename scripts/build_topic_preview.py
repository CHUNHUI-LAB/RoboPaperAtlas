#!/usr/bin/env python3
"""Opt-in clean build: existing public site plus one isolated comparison route."""
import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
ROUTE='library-topic-preview'
FILES={'index.html','preview.css','preview.js','topics.json'}
TOP={'schema_version','status','topics','contract','records'}
RECORD={'id','title','short_name','aliases','authors','research_topics','related_topics','artifact_roles','morphology','curation','note','evidence','methods','tags'}
CONTRACT={'default','membership','related','unknown','facets','limits'}
TOPIC={'id','label','english','boundary'}
EVIDENCE={'url','scope','locator'}
SOURCE_HOSTS={'arxiv.org','proceedings.mlr.press','umi-gripper.github.io'}

def require(value,message):
    if not value:raise ValueError(message)
def exact_fields(obj,fields,label):require(isinstance(obj,dict) and set(obj)==fields,'Invalid public field allowlist: '+label)
def strings(value,label):require(isinstance(value,list) and all(isinstance(v,str) for v in value),'Invalid string list: '+label)
def public_url(url):
    require(isinstance(url,str),'URL must be text')
    u=urlsplit(url)
    require(u.scheme=='https' and u.hostname in SOURCE_HOSTS and not u.username and not u.password and u.port in (None,443),'Unapproved public source URL')
    return url

def safe_path(root,path):
    root=Path(root).absolute();path=Path(path).absolute()
    require(root==root.resolve() and not root.is_symlink(),'Repository root must not traverse symlinks')
    require(path==root or root in path.parents,'Path must remain inside repository')
    require(path==path.resolve(),'Path must be normalized and must not traverse symlinks')
    current=root
    for part in path.relative_to(root).parts:
        current=current/part
        require(not current.is_symlink(),'Symlink path is not allowed')
    return path

def safe_target(root,target):
    target=safe_path(root,target)
    require(target!=Path(root).absolute(),'Output cannot be repository root')
    if target.exists():
        require(target.is_dir(),'Output must be a directory')
        for path in target.rglob('*'):require(not path.is_symlink(),'Output tree must not contain symlinks')
    return target

def validate_source(root=ROOT):
    root=Path(root).absolute()
    src=safe_path(root,root/'previews'/ROUTE)
    safe_path(root,root/'data/catalog.json')
    require(src.is_dir(),'Route source must be a directory')
    require({p.name for p in src.iterdir()}==FILES,'Route source must contain exactly four public files')
    for name in FILES:
        path=safe_path(root,src/name)
        require(path.is_file(),'Public source must be a regular file')
    data=json.loads((src/'topics.json').read_text())
    exact_fields(data,TOP,'root');exact_fields(data['contract'],CONTRACT,'contract')
    require(data['schema_version']==1 and data['status']=='isolated_topic_name_proposal','Unexpected preview version or status')
    for topic in data['topics']:exact_fields(topic,TOPIC,'topic');require(all(isinstance(v,str) for v in topic.values()),'Topic fields must be text')
    topic_ids={t['id'] for t in data['topics']}
    require(topic_ids=={'navigation','legged','manipulation'} and len(data['topics'])==3,'Unexpected topic IDs')
    catalog={r['id']:r for r in json.loads((root/'data/catalog.json').read_text())['papers']}
    require(len(data['records'])==95 and {r['id'] for r in data['records']}==set(catalog),'Preview must preserve all 95 unique catalog records')
    require(sum(r['curation']=='sample_reviewed' for r in data['records'])==13,'Exactly 13 reviewed examples required')
    for r in data['records']:
        exact_fields(r,RECORD,'record')
        require(re.fullmatch(r'[a-z0-9-]+',r['id']) is not None,'Invalid local paper ID')
        for field in ['title','short_name','authors','note']:require(isinstance(r[field],str),'Invalid text field')
        require(r['title']==catalog[r['id']]['title'],'Preview must preserve catalog title')
        for field in ['aliases','research_topics','related_topics','artifact_roles','morphology','methods','tags']:strings(r[field],field)
        require(set(r['research_topics']+r['related_topics'])<=topic_ids,'Unknown topic')
        require(set(r['artifact_roles'])<={'policy','resource'} and set(r['morphology'])<={'legged','mobile'},'Unknown facet')
        require(r['curation'] in {'sample_reviewed','not_curated'},'Unknown example status')
        require(isinstance(r['evidence'],list),'Evidence must be a list')
        if r['curation']=='not_curated':require(not (r['research_topics'] or r['related_topics'] or r['artifact_roles'] or r['morphology'] or r['evidence']),'Unreviewed record must not imply assignment')
        else:require(bool(r['evidence']),'Examples require evidence')
        for e in r['evidence']:
            exact_fields(e,EVIDENCE,'evidence');public_url(e['url'])
            require(isinstance(e['scope'],str) and (e['locator'] is None or isinstance(e['locator'],str)),'Invalid evidence scope')
    for p in src.iterdir():
        text=p.read_text()
        for forbidden in ['/workspace/','/agent_notes/','dream_notes','task-first-audit','catalog_metadata_preserved','scientific_classification_preserved','策展','本体','现有 Atlas','尚尚未','主题整理主题归属','prior section-level review']:
            require(forbidden not in text,'Non-public or obsolete text in route source')
    return data

def write_preview(root,target):
    root=Path(root).absolute()
    validate_source(root)
    target=safe_target(root,target)
    dest=safe_path(root,target/ROUTE)
    if dest.exists():
        require(dest.is_dir() and {p.name for p in dest.iterdir()}==FILES,'Existing route must contain exactly four public files')
        for p in dest.iterdir():require(p.is_file() and not p.is_symlink(),'Existing route files must be regular files')
    else:dest.mkdir(parents=True)
    # Copy only the explicit allowlist, never a recursive source tree. O_NOFOLLOW
    # also rejects a final-file symlink introduced after validation.
    for name in sorted(FILES):
        source=safe_path(root,root/'previews'/ROUTE/name)
        output=safe_path(root,dest/name)
        with os.fdopen(os.open(source,os.O_RDONLY|os.O_NOFOLLOW),'rb') as inp:
            with os.fdopen(os.open(output,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o644),'wb') as out:
                shutil.copyfileobj(inp,out)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='dist');args=parser.parse_args()
    target=safe_target(ROOT,ROOT/args.output)
    require(ROOT in target.resolve().parents,'Output must be a repository subdirectory')
    validate_source()
    subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),'--output',args.output],check=True)
    write_preview(ROOT,target)
    for r in json.loads((target/ROUTE/'topics.json').read_text())['records']:
        require((target/'papers'/r['id']/'index.html').is_file(),'Missing paper detail destination')
    require((target/'atlas-global-preview/index.html').is_file(),'Missing star-map destination')
    print('Added isolated library-topic-preview route; 13 examples, 82 not topic-reviewed, all 95 searchable')
if __name__=='__main__':main()
