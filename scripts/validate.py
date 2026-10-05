#!/usr/bin/env python3
"""Validate the public data boundary and static output before publication."""
import argparse, json, re, ipaddress
from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
FIELDS={'id','title','short_name','authors','original_metadata','verified_overlay','bibliographic_year','publication_year','preprint_year','year_basis','venue','category','tags','summary','citation_verified','metadata_status','verified_at','verification_scope','publication_status','paper_url','preprint_url','pdf_url','pdf_kind','pdf_edition','pdf_note','project_url','code_urls','code_note','doi','sources','notes','stages'}
URL_FIELDS={'paper_url','preprint_url','pdf_url','project_url'}
CATEGORIES={'navigation','wbc','vla','foundations'}
def ensure(condition,message):
    if not condition: raise ValueError(message)
def check_url(value):
    ensure(isinstance(value,str) and value and not re.search(r'[\x00-\x20\x7f\\]',value),'Invalid URL characters')
    u=urlsplit(value)
    ensure(u.scheme=='https' and u.hostname and not u.username and not u.password,'Only public HTTPS URLs without userinfo are allowed')
    ensure(u.hostname.rstrip('.') not in {'localhost','localhost.localdomain'} and not u.hostname.endswith(('.local','.internal')),'Private hostname not permitted')
    ensure(not re.fullmatch(r'[0-9.]+',u.hostname) or bool(re.fullmatch(r'(?:\d{1,3}\.){3}\d{1,3}',u.hostname)), 'Ambiguous numeric hostname')
    try: ensure(ipaddress.ip_address(u.hostname).is_global,'Nonpublic IP not permitted')
    except ValueError as ex:
        if 'Nonpublic IP' in str(ex) or re.fullmatch(r'[0-9.]+',u.hostname) or re.match(r'^0x[0-9a-f]+',u.hostname,re.I): raise ValueError('Nonpublic or ambiguous IP hostname')
    ensure(not re.search(r'(?:token|password|secret|api_key)=',u.query,re.I),'Credential-shaped query parameter not permitted')
def expected_stage(paper_id,stage,report_records=()):
    from reports import report_path
    matches=[x for x in report_records if x['paper_id']==paper_id and x['stage']==stage]
    if not matches:return {'status':'not_imported','artifacts':[]}
    ensure(len({x['version'] for x in matches})==len(matches),'Duplicate report stage version')
    matches=sorted(matches,key=lambda x:int(x['version'][1:]),reverse=True)
    return {'status':'imported','artifacts':[{'kind':'html','version':x['version'],'path':report_path(x),'sha256':x['sha256'],'source_edition':x['source_edition'],'created_at':x['created_at'],'review_status':x['review_status']} for x in matches]}
def validate_catalog(data,report_records=()):
    ensure(set(data)=={'schema_version','updated_at','papers'},'Catalog envelope fields not allowlisted')
    ensure(data['schema_version']==1,'Unsupported schema'); ensure(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',data['updated_at'])), 'Invalid catalog date'); ids=set(); titles=set()
    for p in data['papers']:
        ensure(set(p)==FIELDS,f'Unexpected or missing fields in {p.get("id")}')
        ensure(isinstance(p['id'],str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*',p['id']),'Unsafe paper id')
        ensure(p['id'] not in ids,'Duplicate paper ID');ids.add(p['id'])
        ensure(p['category'] in CATEGORIES,'Invalid category')
        for key in ['bibliographic_year','publication_year','preprint_year']:
            ensure(p[key] is None or (type(p[key]) is int and 1900<=p[key]<=2100),'Invalid year')
        ensure(type(p['citation_verified']) is bool,'citation_verified must be boolean')
        ensure(isinstance(p['title'],str) and p['title'].strip(),'Missing title')
        title=re.sub(r'\W+','',p['title']).casefold(); ensure(title not in titles,'Duplicate canonical title');titles.add(title)
        for k in URL_FIELDS:
            if p[k]:check_url(p[k])
        for k in ['code_urls','sources']:
            ensure(isinstance(p[k],list),'URL list required')
            for u in p[k]:check_url(u)
        if p['original_metadata']:
            ensure(set(p['original_metadata'])=={'title','authors','year'},'Unexpected original metadata fields')
            ensure(p['metadata_status']=='user_provided_unverified' and not p['citation_verified'],'Original record verification must remain distinct')
        if p['verified_overlay']:
            ensure(set(p['verified_overlay'])<= {'title','authors','publication_year','preprint_year','venue','doi','verification_scope'},'Unexpected verified overlay fields')
        ensure(set(p['stages'])=={'stage1','stage2','stage3'},'Three stages required')
        for key,stage in p['stages'].items():ensure(stage==expected_stage(p['id'],key,report_records),'Stage must match an actual reviewed report or remain not_imported')
    ensure(all(x['paper_id'] in ids for x in report_records),'Report paper is absent from catalog')
    return len(ids)
def validate_frontier(data):
    ensure(data.get('schema_version') in {1,'1.0'},'Unsupported frontier schema')
    ensure(set(data)<= {'schema_version','generated_at','fetched_at','last_successful_fetch_at','last_failed_fetch_at','fetch_error','status','coverage','collection','topic_labels','papers','reprocessed_at','attempted_coverage','attempted_collection'}, 'Unknown frontier envelope field')
    ids=set()
    for p in data.get('papers',[]):
        ensure(set(p)<= {'id','canonical_id','arxiv_version','versioned_id','title','authors','first_submitted_at','updated_at','change_type','source_url','version_url','categories','primary_category','doi','journal_reference','matched_topics','relevance_reasons','review_status','deep_read','fetched_at','first_seen_at','observation','abstract_excerpt','abstract_truncated','abstract_original_chars','abstract_excerpt_method'}, 'Unknown frontier paper field')
        ensure(p.get('deep_read') is False, 'Frontier cannot imply completed reading')
        ensure(len(p.get('abstract_excerpt',''))<=600, 'Abstract excerpt too long')
        cid=p.get('canonical_id') or p.get('id');ensure(re.fullmatch(r'\d{4}\.\d{4,5}',cid or ''),'Invalid arXiv ID');ensure(cid not in ids,'Duplicate frontier ID');ids.add(cid)
        for key in ['source_url','version_url']:
            if p.get(key):
                check_url(p[key]); ensure(p[key]=='https://arxiv.org/abs/'+p['canonical_id']+(('v'+str(p['arxiv_version'])) if key=='version_url' else ''), 'Wrong arXiv canonical URL')
        ensure(p.get('review_status')=='candidate_not_reviewed','Frontier candidates must remain unreviewed')
        ensure(p.get('change_type') in {'new','revision'},'Unknown change type')
    return len(ids)
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.references=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in {'href','src'} and v:self.links.append(v);self.references.append((tag,k,v))
def validate_output(root,report_records=()):
    from reports import report_path
    report_paths={report_path(x) for x in report_records}
    from current_reader import validate_current_readers
    current_paths=validate_current_readers(ROOT,root,json.loads((ROOT/'data/catalog.json').read_text())['papers'],report_records)
    from navigation_stage1_preview import validate_preview as validate_navigation_preview
    navigation_preview_paths=validate_navigation_preview(ROOT,root)
    preview_path='reader-preview/umi-on-legs/index.html'
    from reader_theme_preview import PREVIEWS, read_preview as read_theme_preview
    theme_preview_paths=set(PREVIEWS)
    theme_root=root/'reader-theme-preview'
    if theme_root.exists() or theme_root.is_symlink():
        ensure(not theme_root.is_symlink(),'Unsafe reader theme preview directory')
        ensure({str(p.relative_to(root)) for p in theme_root.rglob('*') if p.is_file()}==theme_preview_paths,'Unexpected or missing reader theme preview')
        for route in theme_preview_paths:
            theme_preview=root/route
            ensure(not theme_preview.parent.is_symlink() and not theme_preview.is_symlink() and theme_preview.is_file(),'Unsafe reader theme preview output')
            ensure(theme_preview.read_bytes()==read_theme_preview(ROOT,route),'Reader theme preview hash mismatch')
    report_images=set()
    import hashlib
    for report in report_records:
        artifact=root/report_path(report)
        ensure(artifact.is_file() and not artifact.is_symlink(),'Missing report artifact')
        ensure(hashlib.sha256(artifact.read_bytes()).hexdigest()==report['sha256'],'Built report hash mismatch')
        image_parser=Links();image_parser.feed(artifact.read_text());report_images.update(v for t,k,v in image_parser.references if t=='img' and k=='src' and v.startswith('data:image/'))
    if (root/'artifacts').exists():
        ensure({str(x.relative_to(root)) for x in (root/'artifacts').rglob('*') if x.is_file()}==report_paths,'Unlisted built report artifact')
        ensure(not any(x.is_symlink() for x in (root/'artifacts').rglob('*')),'Symlink in report output')
    pages=list(root.rglob('*.html'))
    ensure(pages,'No built HTML')
    for p in pages:
        parser=Links();parser.feed(p.read_text())
        for tag,attribute,link in parser.references:
            if link.startswith('data:'):
                ensure((str(p.relative_to(root)) in (report_paths|current_paths|navigation_preview_paths) or str(p.relative_to(root)) in ({preview_path}|theme_preview_paths) and link in report_images) and tag=='img' and attribute=='src' and link.startswith(('data:image/png;base64,','data:image/jpeg;base64,')),'Unexpected embedded resource')
                continue
            u=urlsplit(link)
            if u.scheme:check_url(link);continue
            if not u.path:continue
            path=unquote(u.path)
            if path.startswith('/RoboPaperAtlas/'):target=root/path.removeprefix('/RoboPaperAtlas/')
            elif path.startswith('/'):raise ValueError('Unexpected root URL: '+link)
            else:target=(p.parent/path).resolve()
            ensure(root.resolve() in [target,*target.parents],'Link escapes output tree')
            ensure(target.exists(),'Broken local link: '+str(p)+' '+link)
    return len(pages)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='dist');args=ap.parse_args()
    from briefs import load_archive
    load_archive(ROOT)
    from reports import load_reports
    reports=load_reports(ROOT)
    n=validate_catalog(json.loads((ROOT/'data/catalog.json').read_text()),reports);f=validate_frontier(json.loads((ROOT/'data/frontier.json').read_text()));pages=validate_output(ROOT/args.output,reports)
    print(f'PASS: {n} catalog records, {f} frontier candidates, {pages} HTML pages; schemas, public URLs, IDs, stage boundaries, local links')
if __name__=='__main__': main()
