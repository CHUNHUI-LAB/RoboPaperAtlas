#!/usr/bin/env python3
"""Opt-in clean build: existing public site plus one isolated comparison route."""
import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
ROUTE='library-topic-preview'
FILES={'index.html','preview.css','preview.js','topics.json'}
TOP={'schema_version','status','contract','records'}
RECORD={'id','title','authors','bibliographic_year','short_name','aliases','study_question','study_question_evidence_ids','methods','platforms','resources','contributions','problem_claims','task_relations','execution_domains','evaluation_contexts','unresolved_tasks','facet_coverage','evidence'}
CONTRACT={'same_facet_operator','between_facets_operator','weak_task_relations','main_task_relations','hierarchy'}
EVIDENCE={'id','urls','locator','finding'}
SOURCE_HOSTS={'arxiv.org','concept-graphs.github.io','crl.ethz.ch','horizonrobotics.github.io','ieeexplore.ieee.org','proceedings.mlr.press','raw.githubusercontent.com','sayplan.github.io','umi-gripper.github.io','weirdlabuw.github.io','www.markobjelonic.com','www.pi.website'}
SCHEMAS={
 'methods':({'label','role','evidence_ids'},set()),
 'platforms':({'configuration','role','filter_keys','evidence_ids'},{'morphology','name'}),
 'resources':({'kind','name','evidence_ids'},set()),
 'contributions':({'kind','description','evidence_ids'},set()),
 'problem_claims':({'problem_id','label','role','rationale','evidence_ids'},set()),
 'task_relations':({'task','relation','rationale','evidence_ids'},{'execution_domains','evaluation_strength'}),
 'execution_domains':({'domain','evidence_ids'},{'scope_note'}),
 'evaluation_contexts':({'kind','label','evidence_ids'},set()),
}

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
    require(data['schema_version']==2 and data['status']=='isolated_search_preview','Unexpected preview version or status')
    contract=data['contract']
    require(contract['same_facet_operator']=='OR' and contract['between_facets_operator']=='AND','Facet operators changed')
    require(contract['main_task_relations']==['research_object','downstream_execution_evaluation','qualitative_demonstration'],'Task strengths changed')
    require(contract['weak_task_relations']==['data_or_component_testing','training_data_context','adopted_component','resource_support','downstream_application'],'Weak task strengths changed')
    require(contract['hierarchy']=={'manipulation':['mobile-manipulation']},'Task hierarchy changed')
    task_ids={'navigation','mobile-manipulation','motion-control','manipulation','stylized-motion'}
    platform_ids={'legged','quadruped','humanoid','wheeled','mobile_manipulator','single_arm','dual_arm','fixed_base','dexterous_hand','simulated_character'}
    resource_ids={'benchmark','dataset','data-collection','data-generator','simulator','software','deployment-software','tokenizer'}
    catalog={r['id']:r for r in json.loads((root/'data/catalog.json').read_text())['papers']}
    require(len(data['records'])==95 and {r['id'] for r in data['records']}==set(catalog),'Preview must preserve all 95 unique catalog records')
    for r in data['records']:
        exact_fields(r,RECORD,'record')
        require(re.fullmatch(r'[a-z0-9-]+',r['id']) is not None,'Invalid local paper ID')
        for field in ['title','short_name','study_question']:require(isinstance(r[field],str),'Invalid text field')
        if isinstance(r['authors'],list):strings(r['authors'],'authors')
        else:require(isinstance(r['authors'],str),'Authors must be text or a string list')
        for field in ['title','authors','short_name','bibliographic_year']:require(r[field]==catalog[r['id']][field],'Preview must preserve catalog '+field)
        strings(r['aliases'],'aliases');strings(r['unresolved_tasks'],'unresolved_tasks');require(set(r['unresolved_tasks'])<=task_ids,'Invalid pending task')
        require(isinstance(r['evidence'],list) and bool(r['evidence']),'Evidence required')
        evidence_ids=set()
        for e in r['evidence']:
            exact_fields(e,EVIDENCE,'evidence')
            require(isinstance(e['id'],str) and re.fullmatch(r'e[1-9][0-9]*',e['id']) and e['id'] not in evidence_ids,'Invalid or repeated source ID')
            evidence_ids.add(e['id']);strings(e['urls'],'source URLs');require(bool(e['urls']),'Source URL required')
            for url in e['urls']:public_url(url)
            require(isinstance(e['locator'],str) and isinstance(e['finding'],str),'Invalid source description')
        strings(r['study_question_evidence_ids'],'study question refs');require(set(r['study_question_evidence_ids'])<=evidence_ids,'Dangling study question reference')
        for field,(required,optional) in SCHEMAS.items():
            require(isinstance(r[field],list),'Claims must be a list')
            for claim in r[field]:
                require(isinstance(claim,dict) and required<=set(claim)<=required|optional,'Invalid claim fields: '+field)
                strings(claim['evidence_ids'],'claim refs');require(bool(claim['evidence_ids']) and set(claim['evidence_ids'])<=evidence_ids,'Missing or dangling claim reference')
                for key,value in claim.items():
                    if key in {'evidence_ids','filter_keys','execution_domains'}:strings(value,key)
                    else:require(isinstance(value,str),'Claim values must be text')
                if field=='platforms':require(set(claim['filter_keys'])<=platform_ids,'Invalid platform filter')
                if field=='resources':require(claim['kind'] in resource_ids,'Invalid resource kind')
                if field=='task_relations':require(claim['task'] in task_ids and claim['relation'] in contract['main_task_relations']+contract['weak_task_relations'],'Invalid task relation')
        exact_fields(r['facet_coverage'],{'problem_claims','contributions','methods','platforms','execution_domains','task_relations','resources'},'coverage')
        for coverage in r['facet_coverage'].values():
            exact_fields(coverage,{'completeness','unresolved_claim_count'},'coverage field')
            require(coverage['completeness']=='partial' and type(coverage['unresolved_claim_count']) is int and coverage['unresolved_claim_count']>=0,'Coverage must retain partial/unknown states')
    for p in src.iterdir():
        text=p.read_text()
        for forbidden in ['/workspace/','/agent_notes/','dream_notes','task-first-audit','catalog_metadata_preserved','scientific_classification_preserved','prior section-level review','raw_record','prior_assessments','ten_case_reference','provenance','local_controlled_vocabulary_candidate','审计','优先阅读','concurrent full-paper review']:
            require(forbidden not in text,'Non-public input in route source')
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
    print('Added isolated library-topic-preview route; 95 searchable records with partial, source-backed facets')
if __name__=='__main__':main()
