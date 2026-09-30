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
def validate_catalog(data):
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
        for stage in p['stages'].values():ensure(stage=={'status':'not_imported','artifacts':[]},'This catalog release has no imported reports; artifact import requires reviewed implementation')
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
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in {'href','src'} and v:self.links.append(v)
def validate_output(root):
    pages=list(root.rglob('*.html'))
    ensure(pages,'No built HTML')
    for p in pages:
        parser=Links();parser.feed(p.read_text())
        for link in parser.links:
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
    n=validate_catalog(json.loads((ROOT/'data/catalog.json').read_text()));f=validate_frontier(json.loads((ROOT/'data/frontier.json').read_text()));pages=validate_output(ROOT/args.output)
    print(f'PASS: {n} catalog records, {f} frontier candidates, {pages} HTML pages; schemas, public URLs, IDs, stage boundaries, local links')
if __name__=='__main__': main()
