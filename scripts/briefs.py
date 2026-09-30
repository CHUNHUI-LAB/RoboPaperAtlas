"""Validate and render the dated, evidence-scoped public research briefs."""
import json,re,hashlib,html
from pathlib import Path
from datetime import datetime
from validate import check_url
TOP={'schema_version','id','date','title','status','generated_at','language','window','source_snapshot','counts','coverage_note','overview','new_papers','revised_papers','reading_priority','evidence_note','limitations','candidate_ids'}
ITEM={'arxiv_id','arxiv_version','versioned_id','title','authors','first_submitted_at','updated_at','change_type','source_url','version_url','short_title','problem','author_proposal','relevance','evidence_limit','focus_tags','evidence_level','author_proposal_attribution','relevance_attribution','evidence','curated_catalog_overlap','revision_comparison'}
def require(value,message):
 if not value:raise ValueError(message)
def date_ok(value):
 require(isinstance(value,str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',value)),'Invalid brief date');datetime.strptime(value,'%Y-%m-%d');return value
def keys(value,required,optional=()):
 require(isinstance(value,dict) and set(required)<=set(value) and set(value)<=set(required)|set(optional),'Unexpected or missing nested fields')
def string(value,limit=12000):
 require(isinstance(value,str) and bool(value.strip()) and len(value)<=limit,'Invalid text value')
def strings(value,limit=1000):
 require(isinstance(value,list) and len(value)<=limit,'Invalid text list')
 for text in value:string(text)
def number(value):require(type(value) is int and value>=0,'Counts must be nonnegative integers')
def stamp(value,nullable=False):
 if nullable and value is None:return None
 require(isinstance(value,str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z',value)),'UTC timestamp required')
 return datetime.fromisoformat(value.replace('Z','+00:00'))
def digest(value):require(isinstance(value,str) and bool(re.fullmatch(r'[0-9a-f]{64}',value)),'Invalid SHA-256')
def validate_brief(data):
 keys(data,TOP);require(data['schema_version']=='1.0','Unsupported brief schema');date_ok(data['date']);require(data['id']=='arxiv-daily-'+data['date'],'Mismatched brief ID');require(data['status'] in {'ready','no_material_update','stale','error'},'Invalid brief status');require(data['language']=='zh-CN','Unexpected language');stamp(data['generated_at'])
 for field in ['title','coverage_note','overview','evidence_note']:string(data[field])
 strings(data['limitations'])
 win=data['window'];keys(win,{'start','end','timezone','date_field','inclusive','duration_hours'});a,b=stamp(win['start']),stamp(win['end']);require(a<b,'Invalid observation window');require(win['timezone']=='UTC' and win['date_field']=='updated_at' and win['inclusive'] is True,'Brief window must use inclusive UTC updated_at');number(win['duration_hours']);require((b-a).total_seconds()==win['duration_hours']*3600 and 0<win['duration_hours']<=744,'Window duration mismatch')
 snap=data['source_snapshot'];keys(snap,{'name','sha256','generated_at','fetched_at','last_successful_fetch_at','status','coverage','query','rule_version'});digest(snap['sha256']);require(snap['name']=='frontier.json','Unexpected snapshot name');stamp(snap['generated_at']);stamp(snap['fetched_at'],True);stamp(snap['last_successful_fetch_at'],True);require(snap['status'] in {'ok','limited','stale','error'},'Invalid snapshot state');string(snap['query']);string(snap['rule_version'])
 coverage=snap['coverage'];keys(coverage,{'window_start','window_end','window_inclusive','date_field','complete','truncated','api_total_results','fetched_entries','pages_fetched','window_entries','matched_entries','displayed_entries','stopped_at','source','limitations'});ca,cb=stamp(coverage['window_start']),stamp(coverage['window_end']);require(ca<=a and b<=cb,'Brief window exceeds recorded snapshot coverage');require(coverage['window_inclusive'] is True and coverage['date_field']=='updated_at','Unsupported coverage window');require(type(coverage['complete']) is bool and type(coverage['truncated']) is bool,'Coverage flags must be boolean');strings(coverage['limitations']);string(coverage['stopped_at']);require(coverage['source']=='arxiv_api','Unexpected snapshot source')
 for key in ['api_total_results','fetched_entries','pages_fetched','window_entries','matched_entries','displayed_entries']:number(coverage[key])
 counts=data['counts'];keys(counts,{'source_seven_day_candidates','window_candidates','new','revisions','selected_new','selected_revisions','complete_abstracts_checked_for_selection'})
 for value in counts.values():number(value)
 require(counts['source_seven_day_candidates']==coverage['displayed_entries'] and counts['window_candidates']<=counts['source_seven_day_candidates'],'Snapshot/window count mismatch');require(counts['new']+counts['revisions']==counts['window_candidates'],'Candidate counts mismatch')
 for key in ['new_papers','revised_papers','reading_priority']:require(isinstance(data[key],list),'List required')
 all_items=data['new_papers']+data['revised_papers'];require(data['status'] not in {'no_material_update','error'} or not all_items,'No-material/error states cannot retain selected cards');require(len(all_items)<=5,'Brief must have at most five selected papers');require(counts['selected_new']==len(data['new_papers']) and counts['selected_revisions']==len(data['revised_papers']),'Selection counts mismatch');require(counts['selected_new']<=counts['new'] and counts['selected_revisions']<=counts['revisions'],'Selections exceed candidates')
 ids=set();selected_versions=set()
 for group,change in [('new_papers','new'),('revised_papers','revision')]:
  for item in data[group]:
   keys(item,ITEM-{'revision_comparison'}, {'revision_comparison'} if change=='revision' else set());rid=item['arxiv_id'];require(isinstance(rid,str) and bool(re.fullmatch(r'\d{4}\.\d{4,5}',rid)),'Invalid arXiv ID');require(rid not in ids,'Duplicate brief selection');ids.add(rid)
   require(type(item['arxiv_version']) is int and item['arxiv_version']>=1,'Invalid arXiv version');vid=rid+'v'+str(item['arxiv_version']);require(item['versioned_id']==vid,'Version ID mismatch');selected_versions.add(vid)
   require(item['change_type']==change,'New/revision grouping mismatch');require((change=='new' and item['arxiv_version']==1) or (change=='revision' and item['arxiv_version']>=2),'Version conflicts with new/revision label');require(item['source_url']=='https://arxiv.org/abs/'+rid and item['version_url']=='https://arxiv.org/abs/'+vid,'Canonical source URLs required');check_url(item['source_url']);check_url(item['version_url'])
   first,updated=stamp(item['first_submitted_at']),stamp(item['updated_at']);require(first<=updated and a<=updated<=b,'Selected update outside stated brief window')
   for field in ['title','short_title','problem','author_proposal','relevance','evidence_limit']:string(item[field])
   strings(item['authors']);require(item['authors'],'Authors required');strings(item['focus_tags']);require(item['author_proposal_attribution']=='author_claim' and item['relevance_attribution']=='curator_inference','Claim attribution required')
   require(item['evidence_level'] in {'abstract_only','full_text_checked','version_comparison'},'Invalid evidence scope');ev=item['evidence'];keys(ev,{'level','label','source_type','source_url','retrieved_at','abstract_complete','full_paper_read','experiments_independently_verified','abstract_chars','abstract_sha256'},{'supporting_sources','sections_checked','version_sources'});string(ev['label']);string(ev['source_type']);require(ev['source_url']==item['version_url'],'Evidence must identify selected version');stamp(ev['retrieved_at']);number(ev['abstract_chars']);digest(ev['abstract_sha256'])
   for flag in ['abstract_complete','full_paper_read','experiments_independently_verified']:require(type(ev[flag]) is bool,'Evidence flags must be boolean')
   for field in ['supporting_sources','version_sources']:
    if field in ev:
     strings(ev[field])
     for url in ev[field]:check_url(url)
   if 'sections_checked' in ev:strings(ev['sections_checked'])
   if item['evidence_level']=='abstract_only':require(ev['level']=='primary_complete_abstract' and ev['abstract_complete'] is True and ev['full_paper_read'] is False and ev['experiments_independently_verified'] is False,'Abstract-only must not imply full reading or independent verification')
   elif item['evidence_level']=='full_text_checked':require(ev['level']=='primary_full_text' and ev['full_paper_read'] is True and ev.get('sections_checked') and ev.get('supporting_sources'),'Full-text scope needs supporting sections and sources')
   else:
    require(change=='revision' and ev['level']=='primary_version_comparison' and len(ev.get('version_sources',[]))>=2,'Version comparison needs multiple revision sources')
    versions=ev['version_sources'];require(len(set(versions))>=2 and item['version_url'] in versions,'Comparison needs distinct versions including selected edition')
    require(all(re.fullmatch(r'https://arxiv\.org/abs/'+re.escape(rid)+r'v[1-9]\d*',url) for url in versions),'Comparison sources must be pinned versions of this paper')
   overlap=item['curated_catalog_overlap'];keys(overlap,{'already_present','catalog_id'});require(type(overlap['already_present']) is bool,'Overlap flag must be boolean')
   if overlap['already_present']:require(isinstance(overlap['catalog_id'],str) and bool(re.fullmatch(r'[a-z0-9][a-z0-9-]*',overlap['catalog_id'])),'Unsafe catalog ID')
   else:require(overlap['catalog_id'] is None,'Unexpected overlap target')
   if change=='revision':
    require('revision_comparison' in item,'Revision comparison scope required');comparison=item['revision_comparison'];keys(comparison,{'performed','changes_verified'},{'compared_versions'});require(type(comparison['performed']) is bool,'Comparison flag must be boolean');strings(comparison['changes_verified'])
    if not comparison['performed']:require(comparison['changes_verified']==[] and not comparison.get('compared_versions') and item['evidence_level']!='version_comparison','Uncompared revisions cannot claim comparison evidence or changes')
    else:
     require(item['evidence_level']=='version_comparison' and len(comparison.get('compared_versions',[]))>=2,'Compared revision needs explicit version evidence')
     strings(comparison['compared_versions']);require(set(comparison['compared_versions'])==set(ev['version_sources']) and len(set(comparison['compared_versions']))>=2,'Compared versions must match pinned evidence sources')
 for entry in data['reading_priority']:
  keys(entry,{'audience','arxiv_ids','text'});string(entry['audience']);string(entry['text']);strings(entry['arxiv_ids']);require(set(entry['arxiv_ids'])<=ids,'Priority references unselected papers')
 strings(data['candidate_ids']);require(all(re.fullmatch(r'\d{4}\.\d{4,5}v[1-9]\d*',vid) for vid in data['candidate_ids']),'Invalid candidate version ID');require(len(set(data['candidate_ids']))==len(data['candidate_ids'])==counts['window_candidates'],'Candidate list/count mismatch');require(selected_versions<=set(data['candidate_ids']),'Selection absent from candidate snapshot')
 return data

def load_archive(root):
 directory=Path(root)/'data/briefs';require(not directory.is_symlink() and not (directory/'index.json').is_symlink(),'Symlinked archive is not allowed');index=json.loads((directory/'index.json').read_text());require(set(index)=={'schema_version','latest','summary_automation_enabled','briefs'},'Unknown brief index fields');require(index['schema_version']==1 and type(index['summary_automation_enabled']) is bool,'Invalid brief index');date_ok(index['latest']);seen=set();records={}
 for entry in index['briefs']:
  require(set(entry)=={'date','path','title','status','sha256'},'Unknown archive index entry field');date_ok(entry['date']);require(entry['date'] not in seen,'Duplicate archive date');seen.add(entry['date']);require(entry['path']==entry['date']+'.json','Archive path must be bounded to its date')
  path=directory/entry['path'];require(not path.is_symlink() and path.resolve().parent==directory.resolve(),'Unsafe archive path');payload=path.read_bytes();require(hashlib.sha256(payload).hexdigest()==entry['sha256'],'Brief SHA-256 mismatch');record=validate_brief(json.loads(payload));require(record['date']==entry['date'] and record['title']==entry['title'] and record['status']==entry['status'],'Brief/index metadata mismatch');records[entry['date']]=record
 require(index['latest'] in records,'Latest brief missing');expected={'index.json'}|{entry['path'] for entry in index['briefs']}
 require(all(p.name in expected and p.is_file() and not p.is_symlink() for p in directory.iterdir()),'Unindexed or unsafe archive file')
 return index,records

def section(data,index,prefix='',archive=False):
 e=lambda v:html.escape(str(v),quote=True);items=data['new_papers']+data['revised_papers'];count=data['counts'];cards=[]
 for n,item in enumerate(items,1):
  change='新提交' if item['change_type']=='new' else '版本修订';scope={'abstract_only':'基于完整摘要','full_text_checked':'已检查相关全文','version_comparison':'已比较指定版本'}[item['evidence_level']]
  overlap=item['curated_catalog_overlap'];existing=f'<a href="{prefix}papers/{e(overlap["catalog_id"])}/index.html">查看已有目录 ↗</a>' if overlap['already_present'] else ''
  cards.append(f'''<article class="brief-paper"><div class="brief-paper-index">{n:02d}</div><div class="brief-paper-content"><p class="brief-paper-type">{change} · v{item['arxiv_version']}</p><h3><a href="{e(item['version_url'])}" target="_blank" rel="noopener noreferrer">{e(item['short_title'])} <span aria-hidden="true">↗</span></a></h3><p class="brief-full-title">{e(item['title'])}</p><p class="brief-problem">{e(item['problem'])}</p><p class="brief-method"><span>作者提出</span>{e(item['author_proposal'])}</p><p class="brief-relevance"><span>相关性判断 · 推断</span>{e(item['relevance'])}</p><details><summary>{scope} · 查看证据边界</summary><p>{e(item['evidence_limit'])}</p><p>首发 {e(item['first_submitted_at'])} · 更新 {e(item['updated_at'])}</p>{existing}</details></div></article>''')
 archives=''.join(f'<a href="{prefix}frontier/briefs/{e(entry["date"])}/index.html"'+(' aria-current="page"' if archive and entry['date']==data['date'] else '')+f'>{e(entry["date"])}</a>' for entry in sorted(index['briefs'],key=lambda x:x['date'],reverse=True))
 state_note={'ready':'','no_material_update':'本窗口没有值得新增的重点摘要，不重复推荐未变内容。','stale':'本次更新未完成；以下保留此前内容，请以原始观察窗口为准。','error':'本期摘要暂未生成，请查看抓取记录与已有归档。'}[data['status']]
 state_html=f'<p class="brief-state">{e(state_note)}</p>' if state_note else ''
 automation='每日摘要更新已安排；以下为最后一次发布内容。' if index['summary_automation_enabled'] else '本期为已发布摘要速览；后续自动摘要更新尚未启用。'
 empty='<p class="brief-none">本窗口没有需要新增的重点摘要；不为凑数重复推荐。</p>' if not items else ''
 return f'''<section class="daily-brief" id="daily-brief" aria-labelledby="brief-heading"><div class="brief-heading"><div><p class="brief-date">{e(data['date'])} · DAILY RESEARCH BRIEF</p><h2 id="brief-heading">本期摘要速览</h2></div><a class="text-link" href="{prefix}frontier/briefs/{e(data['date'])}/index.html">独立阅读本期 ↗</a></div>{state_html}<p class="brief-window">观察窗口：{e(data['window']['start'])} → {e(data['window']['end'])}（UTC）</p><p class="brief-counts">{e(count['window_candidates'])} 条窗口候选 · {e(count['new'])} 篇首版 · {e(count['revisions'])} 篇修订 · {len(items)} 篇摘要速览</p><div class="brief-overview"><span>本期观察 · 编辑判断</span><p>{e(data['overview'])}</p></div><div class="brief-papers">{''.join(cards)}{empty}</div><div class="brief-priority"><h3>按研究问题继续看</h3>{''.join(f'<p><strong>{e(row["audience"])}</strong>{e(row["text"])}</p>' for row in data['reading_priority'])}</div><details class="brief-evidence"><summary>来源、范围与限制</summary><p>{e(data['evidence_note'])}</p><p>{e(data['coverage_note'])}</p><p>来源抓取完成：{e(data['source_snapshot']['fetched_at'])}；简报生成：{e(data['generated_at'])}</p><ul>{''.join(f'<li>{e(note)}</li>' for note in data['limitations'])}</ul></details><div class="brief-archive"><span>简报归档</span>{archives}</div><p class="brief-automation">{automation} 本期摘要不改变论文目录的阅读状态。</p></section>'''
