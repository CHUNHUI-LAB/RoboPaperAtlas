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
 return '<nav class="radar-archive" aria-label="Radar 周期"><a href="'+prefix+'frontier/daily/index.html"'+(' aria-current="page"' if current=='daily' else '')+'>日报 · 最近24小时</a><a href="'+prefix+'frontier/weekly/index.html"'+(' aria-current="page"' if current=='weekly' else '')+'>周报 · 七天研究主线</a></nav>'

def render(data,index,prefix):
 e=lambda s:html.escape(str(s),quote=True);o=data['research_overview'];sources={s['versioned_id']:s for s in o['evidence_sources']};themes=[]
 for ordinal,t in enumerate(o['themes'],1):
  routes=''.join('<li><p>'+e(r['text'])+'</p>'+''.join('<a href="'+e(sources[v]['version_url'])+'">'+e(sources[v]['title'])+' ↗</a><br>' for v in r['evidence_ids'])+'</li>' for r in t['method_routes'])
  themes.append('<details class="radar-theme" open><summary><span>'+f'{ordinal:02d}'+'</span><span class="radar-theme-copy"><span class="radar-theme-title" role="heading" aria-level="3">'+e(t['title'])+'</span><span class="radar-theme-summary">'+e(t['summary'])+'</span></span><i aria-hidden="true">＋</i></summary><div class="radar-theme-body"><h4>共同问题</h4><p>'+e(t['shared_problem'])+'</p><h4>方法路线 · 作者摘要陈述</h4><ul>'+routes+'</ul><h4>仍需核查</h4><p>'+e(t['open_question'])+'</p><p class="radar-scope">编辑归纳；窗口内对照，不代表跨周趋势或领域共识</p></div></details>')
 distribution=''.join('<li>'+e(x['label'])+'：'+str(x['count'])+'（'+str(x['new'])+' 首版 / '+str(x['revisions'])+' 修订）</li>' for x in o['topic_distribution']);caveats=''.join('<p>'+e(x['explanation'])+'</p>' for x in o['keyword_caveats']);attempt=index.get('last_attempt');attempt_note=('<p class="radar-state">最近周报更新失败（'+e(attempt['attempted_at'])+'）：'+e(attempt['message'])+'。以下保留上次成功观察窗口。</p>') if attempt else '';state={'ready':'','stale':'更新未完成，保留原始成功观察窗口与旧内容。','error':'本期取数或摘要核查失败；此状态不代表没有新论文。','no_material_update':'本周没有新增研究主线；不拼接或重复旧日报。'}[data['status']]
 partial='完整' if data['source_snapshot']['coverage_complete'] and not data['source_snapshot']['coverage_truncated'] else '部分覆盖；候选数不是本周全部相关论文'
 count=data['counts'];archive=''.join('<a href="'+prefix+'frontier/weekly/'+e(x['date'])+'/index.html">'+e(x['date'])+'</a>' for x in reversed(index['weeks']));candidates=''.join('<li><span>'+('首版' if r['change_type']=='new' else '修订')+' · '+e(r['versioned_id'])+'</span><a href="https://arxiv.org/abs/'+e(r['versioned_id'])+'">'+e(r['title'])+'</a><small>'+e(r['updated_at'])+'</small></li>' for r in o['candidate_records'])
 return '<link rel="stylesheet" href="'+prefix+'assets/radar-overview.css?v='+sha((Path(__file__).resolve().parents[1]/'assets/radar-overview.css').read_bytes())[:12]+'">'+navigation(prefix,'weekly')+attempt_note+'<section class="research-overview" id="weekly-brief"><header class="radar-lead"><p class="radar-date">'+e(data['date'])+' / WEEKLY RESEARCH RADAR</p><h1>'+e(o['headline'])+'</h1><p class="radar-editorial">'+e(o['executive_summary'])+'</p><p class="radar-window">'+e(data['window']['start'])+' → '+e(data['window']['end'])+'（UTC，按更新时间）</p><p>'+e(state)+'</p><p>'+str(count['window_candidates'])+' 条候选 · '+str(count['new'])+' 首版 / '+str(count['revisions'])+' 修订 · 查询覆盖：'+partial+'</p></header><div class="radar-editorial-layout"><div class="radar-main"><h2>七天研究主线</h2>'+''.join(themes)+'<h2>修订的解释边界</h2><p>'+e(o['revision_note'])+'</p></div><aside class="radar-evidence"><h2>证据覆盖</h2><p>'+str(count['window_candidates'])+' 条标题与摘要片段筛查；'+str(len(sources))+' 篇完整官方摘要；全文 / 代码 / 版本差分：0 / 0 / 0</p><ul>'+''.join('<li>'+e(s)+'</li>' for s in o['limitations'])+'</ul><details class="radar-distribution"><summary>关键词分布与局限</summary><p>现有多标签关键词规则，计数重叠；不是人工分类或热度排名。</p><ul>'+distribution+'</ul>'+caveats+'</details><p>本周摘要归纳不改变目录、Stage 或复现状态。</p></aside></div><details class="radar-window-list"><summary>完整七天候选清单（'+str(count['window_candidates'])+'）</summary><ul>'+candidates+'</ul></details><footer class="radar-footer"><a href="'+prefix+'data/weekly/'+data['date']+'.json">公开周报数据 ↗</a><a href="'+prefix+'data/weekly/'+data['date']+'/manifest.json">冻结候选来源清单 ↗</a><p>源快照 SHA-256：'+e(data['source_snapshot']['sha256'])+'</p><nav class="radar-archive" aria-label="周报归档">'+archive+'</nav><p>'+('每周摘要更新已安排。' if index['summary_automation_enabled'] else '周报自动更新尚未启用。')+'</p></footer></section>'

def home_overview(weekly_index,weekly_records,daily_index,daily_records,prefix='../'):
 from briefs import section as daily_section
 e=lambda value:html.escape(str(value),quote=True)
 daily=daily_records[daily_index['latest']]
 day_state={'ready':'当天摘要已更新','no_material_update':'最近24小时没有新增候选或研究主线','stale':'当天更新未完成，日报保留原窗口','error':'当天更新失败；这不代表没有新论文'}[daily['status']]
 day='<aside class="radar-state"><p>'+e(day_state)+' · '+e(daily['window']['start'])+' → '+e(daily['window']['end'])+'（UTC）</p><a href="'+prefix+'frontier/briefs/'+e(daily['date'])+'/index.html">阅读 '+e(daily['date'])+' 日报与证据范围 ↗</a></aside>'
 usable=[r for r in weekly_records.values() if r['status'] in {'ready','stale'} and r['research_overview']['themes']]
 if usable:
  recent=max(usable,key=lambda r:r['window']['end']);index=dict(weekly_index)
  if recent['date']!=weekly_index['latest'] and 'last_attempt' not in index:
   reason='最近一周没有新的研究主线' if weekly_records.get(weekly_index['latest'],{}).get('status')=='no_material_update' else '最近周报更新未完成'
   note='<p class="radar-state">'+reason+'，以下保留 '+e(recent['date'])+' 的成功观察窗口。</p>'
  else:note=''
  return day+note+render(recent,index,prefix)
 historical=[r for r in daily_records.values() if r['status']=='ready']
 if historical:
  recent=max(historical,key=lambda r:r['window']['end'])
  note='<p class="radar-state">周报尚无可用研究总览；以下为 '+e(recent['date'])+' 历史日报，观察窗口以原记录为准，不是当天新发现。</p>'
  return navigation(prefix)+note+daily_section(recent,daily_index,prefix,archive=True)+day
 return navigation(prefix)+day+'<p class="radar-state">近期研究总览暂不可用；下方保留有明确抓取范围的候选队列。</p>'

def build(root,target,shell):
 index,records=load_archive(root)
 for date,data in records.items():
  folder=target/'frontier/weekly'/date;folder.mkdir(parents=True,exist_ok=True);body='<main id="main" class="brief-archive-page">'+render(data,index,'../../../')+'</main>';(folder/'index.html').write_text(shell(data['title'],body,prefix='../../../',page='frontier'))
 folder=target/'frontier/weekly';body='<main id="main" class="brief-archive-page">'+render(records[index['latest']],index,'../../')+'</main>';(folder/'index.html').write_text(shell('Radar 周报',body,prefix='../../',page='frontier'));shutil.copytree(Path(root)/'data/weekly',target/'data/weekly')
 return index,records
