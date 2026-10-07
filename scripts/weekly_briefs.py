"""Independent weekly 1.0 archive; no changes to daily public allowlists."""
import hashlib,html,json,re,shutil
from pathlib import Path
from briefs import require,keys,string,strings,number,stamp,digest,date_ok
from radar_overview import validate_overview,CANDIDATE,OV
TOP={'schema_version','id','date','title','status','generated_at','language','window','source_snapshot','counts','research_overview','candidate_manifest'}
SNAP={'name','sha256','generated_at','fetched_at','status','query','rule_version','coverage_complete','coverage_truncated','coverage_start','coverage_end'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def validate_weekly(data,records):
 keys(data,TOP);require(data['schema_version']=='weekly-1.0','Unknown weekly schema');date_ok(data['date']);require(data['id']=='arxiv-weekly-'+data['date'],'Weekly ID mismatch');require(data['language']=='zh-CN','Unexpected language');require(data['status'] in {'ready','no_material_update','stale','error'},'Invalid weekly state');string(data['title'],200);generated=stamp(data['generated_at'])
 w=data['window'];keys(w,{'start','end','timezone','date_field','inclusive','duration_hours'});a,b=stamp(w['start']),stamp(w['end']);require((b-a).total_seconds()==168*3600 and type(w['duration_hours']) is int and w['duration_hours']==168,'Weekly window must be seven days');require(w['timezone']=='UTC' and w['date_field']=='updated_at' and w['inclusive'] is True,'Invalid weekly window');require(b<=generated and data['date']==w['end'][:10],'Week date/window mismatch')
 s=data['source_snapshot'];keys(s,SNAP);digest(s['sha256']);require(s['name']=='frontier.json','Unexpected snapshot');require(s['status'] in {'ok','limited','stale','error'},'Invalid source state');sg=stamp(s['generated_at']);sf=stamp(s['fetched_at'],True);require(sg<=generated and (sf is None or sf<=sg),'Source chronology exceeds generation');string(s['query']);string(s['rule_version']);require(type(s['coverage_complete']) is bool and type(s['coverage_truncated']) is bool,'Coverage flags must be boolean');require(stamp(s['coverage_start'])<=a and b<=stamp(s['coverage_end']),'Weekly range exceeds source coverage');require(not(s['coverage_complete'] and s['coverage_truncated']),'Contradictory coverage');require(data['status'] not in {'ready','no_material_update'} or s['status'] in {'ok','limited'},'Failed source cannot claim ready or no material');require(data['status'] not in {'ready','no_material_update'} or sf is not None,'Successful issue requires fetched time')
 c=data['counts'];keys(c,{'window_candidates','new','revisions','source_seven_day_candidates'})
 for v in c.values():number(v)
 require(c['new']+c['revisions']==c['window_candidates']==c['source_seven_day_candidates']==len(records),'Weekly counts mismatch')
 require(len({r['versioned_id'].split('v')[0] for r in records})==len(records),'Duplicate canonical candidate ID');keys(data['research_overview'],OV-{'candidate_records'});require(data['candidate_manifest']==data['date']+'/manifest.json','Unsafe candidate manifest');require(data['status']!='no_material_update' or not data['research_overview']['themes'],'No material state cannot have themes')
 adapter={**data,'candidate_ids':[r['versioned_id'] for r in records],'research_overview':{**data['research_overview'],'candidate_records':records}}
 validate_overview(adapter)
 byid={r['versioned_id']:r for r in records}
 for source in data['research_overview']['evidence_sources']:
  require(stamp(source['checked_at'])>=stamp(byid[source['versioned_id']]['updated_at']),'Abstract checked before selected version existed')
 return adapter

def validate_snapshot(data,records,frontier,raw_sha256):
 require(data['source_snapshot']['sha256']==raw_sha256,'Weekly source snapshot hash mismatch')
 a,b=stamp(data['window']['start']),stamp(data['window']['end'])
 source=data['source_snapshot'];coverage=frontier['coverage'];collection=frontier['collection']
 expected_source={'name':'frontier.json','sha256':raw_sha256,'generated_at':frontier['generated_at'],'fetched_at':frontier['fetched_at'],'status':frontier['status'],'query':collection['search_query'],'rule_version':collection['rule_version'],'coverage_complete':coverage['complete'],'coverage_truncated':coverage['truncated'],'coverage_start':coverage['window_start'],'coverage_end':coverage['window_end']}
 require(source==expected_source,'Weekly source provenance differs from snapshot')
 expected=[{k:p[k] for k in CANDIDATE} for p in frontier['papers'] if a<=stamp(p['updated_at'])<=b]
 require({r['versioned_id']:r for r in expected}=={r['versioned_id']:r for r in records},'Frozen weekly candidates differ from source snapshot')
 return validate_weekly(data,records)

def bounded_file(directory,name):
 p=directory/name;require(not p.is_symlink() and p.is_file() and p.resolve().parent==directory.resolve(),'Unsafe archive file');return p.read_bytes()
def load_candidates(directory):
 require(not directory.is_symlink(),'Symlinked candidate directory');raw=bounded_file(directory,'manifest.json');m=json.loads(raw);keys(m,{'schema_version','sha256','count','parts'});require(m['schema_version']=='weekly-candidates-1.0','Candidate schema mismatch');digest(m['sha256']);number(m['count']);require(isinstance(m['parts'],list),'Missing parts');records=[];seen=set()
 for i,part in enumerate(m['parts']):
  keys(part,{'path','sha256','bytes','count'});require(part['path']==f'{i:03d}.json','Candidate part path/order mismatch');digest(part['sha256']);number(part['bytes']);number(part['count']);blob=bounded_file(directory,part['path']);require(len(blob)==part['bytes']<=60000 and sha(blob)==part['sha256'],'Candidate part integrity failure');rows=json.loads(blob);require(isinstance(rows,list) and len(rows)==part['count'],'Candidate part count mismatch');records.extend(rows);seen.add(part['path'])
 require({p.name for p in directory.iterdir()}==seen|{'manifest.json'},'Unindexed candidate file');canonical=json.dumps(records,ensure_ascii=False,separators=(',',':')).encode();require(len(records)==m['count'] and sha(canonical)==m['sha256'],'Frozen candidate list integrity failure');return records,raw

def validate_attempt(attempt):
 if attempt is None:return
 keys(attempt,{'status','attempted_at','window_start','window_end','message'})
 require(attempt['status']=='error','Attempt must describe failure');a,b,t=stamp(attempt['window_start']),stamp(attempt['window_end']),stamp(attempt['attempted_at']);require((b-a).total_seconds()==168*3600 and b<=t,'Invalid failed attempt window');string(attempt['message'],500)

def record_failed_attempt(root,attempt):
 """Preserve successful issue and candidate bytes; only annotate the index."""
 validate_attempt(attempt);load_archive(root);p=Path(root)/'data/weekly/index.json';index=json.loads(p.read_text());index['last_attempt']=attempt;temp=p.with_suffix('.pending');require(not temp.exists() and not temp.is_symlink(),'Pending index already exists');temp.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');temp.replace(p);load_archive(root)

def load_archive(root):
 directory=Path(root)/'data/weekly';require(not directory.is_symlink(),'Symlinked weekly archive');index=json.loads(bounded_file(directory,'index.json'));keys(index,{'schema_version','latest','summary_automation_enabled','weeks'},{'last_attempt'});require(index['schema_version']=='weekly-index-1.0' and type(index['summary_automation_enabled']) is bool,'Invalid weekly index');date_ok(index['latest']);validate_attempt(index.get('last_attempt'));require(isinstance(index['weeks'],list),'Invalid weeks');records={};expected={'index.json'}
 for entry in index['weeks']:
  keys(entry,{'date','path','title','status','sha256','candidate_manifest_sha256'});date_ok(entry['date']);require(entry['date'] not in records and entry['path']==entry['date']+'.json','Duplicate/unsafe week');raw=bounded_file(directory,entry['path']);digest(entry['sha256']);require(sha(raw)==entry['sha256'],'Weekly SHA mismatch');data=json.loads(raw);rows,manifest=load_candidates(directory/entry['date']);digest(entry['candidate_manifest_sha256']);require(sha(manifest)==entry['candidate_manifest_sha256'],'Manifest SHA mismatch');record=validate_weekly(data,rows);require(all(record[k]==entry[k] for k in ['date','title','status']),'Weekly index mismatch');records[entry['date']]=record;expected|={entry['path'],entry['date']}
 require(index['latest'] in records and index['latest']==max(records),'Latest week missing or incorrect');require({p.name for p in directory.iterdir()}==expected,'Unindexed weekly archive file')
 snapshot=Path(root)/'data/frontier.json'
 if snapshot.exists():
  raw=snapshot.read_bytes();current_sha=sha(raw)
  for record in records.values():
   if record['source_snapshot']['sha256']==current_sha:
    data={k:v for k,v in record.items() if k!='candidate_ids'};data['research_overview']={k:v for k,v in record['research_overview'].items() if k!='candidate_records'}
    validate_snapshot(data,record['research_overview']['candidate_records'],json.loads(raw),current_sha)
 return index,records

def navigation(prefix='',current='daily'):
 return '<nav class="radar-archive" aria-label="Radar 周期"><a href="'+prefix+'frontier/index.html"'+(' aria-current="page"' if current=='overview' else '')+'>近期研究概览</a><a href="'+prefix+'frontier/daily/index.html"'+(' aria-current="page"' if current=='daily' else '')+'>日报 · 最近24小时</a><a href="'+prefix+'frontier/weekly/index.html"'+(' aria-current="page"' if current=='weekly' else '')+'>周报 · 七天研究主线</a></nav>'

def render(data,index,prefix,current='weekly'):
 from radar_overview import render as overview_render
 e=lambda s:html.escape(str(s),quote=True);attempt=index.get('last_attempt')
 note=('<p class="radar-state">最近周报更新失败（'+e(attempt['attempted_at'])+'）：'+e(attempt['message'])+'。以下保留上次成功观察窗口。</p>') if attempt else ''
 return navigation(prefix,current)+note+overview_render(data,index,prefix)

def home_overview(weekly_index,weekly_records,daily_index,daily_records,prefix='../',current='overview'):
 from briefs import section as daily_section
 e=lambda value:html.escape(str(value),quote=True)
 daily=daily_records[daily_index['latest']]
 day_state={'ready':'当天摘要已更新','no_material_update':('最近24小时没有新增候选或研究主线' if daily['counts']['window_candidates']==0 else '最近24小时未新增研究主线；窗口候选保留在完整日报'),'stale':'当天更新未完成，日报保留原窗口','error':'当天更新失败；这不代表没有新论文'}[daily['status']]
 day='<aside class="radar-state"><p>'+e(day_state)+' · '+e(daily['window']['start'])+' → '+e(daily['window']['end'])+'（UTC）</p><a href="'+prefix+'frontier/briefs/'+e(daily['date'])+'/index.html">阅读 '+e(daily['date'])+' 日报与证据范围 ↗</a></aside>'
 # A landing page never silently substitutes another reporting period.
 usable=[r for r in daily_records.values() if r['date']<=daily_index['latest'] and r['status'] in {'ready','stale'} and r.get('research_overview',{}).get('themes')]
 if daily['status'] in {'ready','stale'} and daily.get('research_overview',{}).get('themes'):
  return navigation(prefix,current)+daily_section(daily,daily_index,prefix)
 if usable:
  recent=max(usable,key=lambda r:r['window']['end'])
  note='<p class="radar-state">以下为 '+e(recent['date'])+' 历史日报，保留原始观察窗口，不是当天新发现或本期新增。周报可从独立周期入口阅读。</p>'
  return navigation(prefix,current)+day+note+daily_section(recent,daily_index,prefix)
 return navigation(prefix,current)+day+'<p class="radar-state">近期研究总览暂不可用；可查看完整日报记录或独立周报。</p>'

def daily_landing(weekly_index,weekly_records,daily_index,daily_records,prefix='../../'):
 """Keep empty daily records intact, but make the rolling reading entry useful."""
 from briefs import section as daily_section
 daily=daily_records[daily_index['latest']]
 if daily['status']=='no_material_update':
  note='<p class="radar-state">本期日报没有新增研究主线。先阅读下方近期研究概览；内容保留原始日期与观察窗口，不是本期新增。完整日报及候选记录可通过下方日期链接查看。</p>'
  return note+home_overview(weekly_index,weekly_records,daily_index,daily_records,prefix,current='daily')
 return home_overview(weekly_index,weekly_records,daily_index,daily_records,prefix,current='daily')

def build(root,target,shell):
 index,records=load_archive(root)
 for date,data in records.items():
  folder=target/'frontier/weekly'/date;folder.mkdir(parents=True,exist_ok=True);body='<main id="main" class="brief-archive-page">'+render(data,index,'../../../')+'</main>';(folder/'index.html').write_text(shell(data['title'],body,prefix='../../../',page='frontier'))
 folder=target/'frontier/weekly';body='<main id="main" class="brief-archive-page">'+render(records[index['latest']],index,'../../')+'</main>';(folder/'index.html').write_text(shell('Radar 周报',body,prefix='../../',page='frontier'));shutil.copytree(Path(root)/'data/weekly',target/'data/weekly')
 return index,records
