"""Strict abstract-based daily research overview; 1.0 briefs stay unchanged."""
import html,json,re,hashlib
from pathlib import Path
from briefs import require,keys,string,strings,number,stamp,digest
OV={'headline','executive_summary','coverage','topic_distribution','themes','evidence_sources','revision_note','limitations','candidate_records','keyword_caveats'}
COVERAGE={'candidate_metadata_screened','complete_abstracts_checked','full_papers_read','revision_diffs_checked','comparison_window_available','topic_count_method','count_denominator'}
THEME={'id','title','summary','shared_problem','method_routes','open_question','evidence_ids','related_topics','attribution','comparison_scope'}
EVIDENCE={'versioned_id','version_url','source_url','title','level','source_type','checked_at','abstract_complete','full_paper_read','experiments_independently_verified','version_comparison_performed','abstract_chars','abstract_sha256'}
CANDIDATE={'versioned_id','title','first_submitted_at','updated_at','change_type','matched_topics'}
VERSION=re.compile(r'(\d{4}\.\d{4,5})v([1-9]\d*)$')
TOPICS={'vln_objectnav','navigation_agents','spatial_episodic_memory','mobile_manipulation','whole_body_control','end_effector_trajectories','robot_vla','robot_moe','robot_world_models'}
def unique_list(value,label):
 strings(value);require(len(set(value))==len(value),'Duplicate '+label);return set(value)
def validate_overview(brief):
 o=brief['research_overview'];keys(o,OV)
 for field,limit in [('headline',160),('executive_summary',1600),('revision_note',1600)]:string(o[field],limit)
 strings(o['limitations'],30)
 cov=o['coverage'];keys(cov,COVERAGE)
 for k in ['candidate_metadata_screened','complete_abstracts_checked','full_papers_read','revision_diffs_checked','count_denominator']:number(cov[k])
 require(cov['candidate_metadata_screened']==cov['count_denominator']==brief['counts']['window_candidates'],'Overview coverage denominator mismatch')
 require(cov['full_papers_read']==0 and cov['revision_diffs_checked']==0 and cov['comparison_window_available'] is False,'Overview1.1 supports abstract evidence without temporal or version comparison')
 require(cov['topic_count_method']=='existing_title_abstract_keyword_heuristic_multilabel','Unknown topic count method')
 records=o['candidate_records'];require(isinstance(records,list)and len(records)==cov['count_denominator'],'Candidate metadata count mismatch');byid={}
 start,end=stamp(brief['window']['start']),stamp(brief['window']['end'])
 for row in records:
  keys(row,CANDIDATE);m=VERSION.fullmatch(row['versioned_id']);require(m and row['versioned_id'] not in byid,'Invalid or duplicate candidate ID');byid[row['versioned_id']]=row
  string(row['title'],2000);first,updated=stamp(row['first_submitted_at']),stamp(row['updated_at']);require(first<=updated and start<=updated<=end,'Candidate outside overview window')
  require(row['change_type']==('new'if int(m[2])==1 else'revision'),'Candidate version/change mismatch');require(unique_list(row['matched_topics'],'candidate tags')<=TOPICS,'Unknown candidate topic')
 require(set(byid)==set(brief['candidate_ids']),'Retained metadata differs from candidate list')
 require(sum(r['change_type']=='new'for r in records)==brief['counts']['new'],'New candidate count mismatch')
 dist=o['topic_distribution'];require(isinstance(dist,list)and len(dist)==len(TOPICS),'Complete topic distribution required');seen=set()
 for row in dist:
  keys(row,{'topic','label','count','new','revisions','candidate_ids'});topic=row['topic'];require(topic in TOPICS and topic not in seen,'Invalid or duplicate topic');seen.add(topic);string(row['label'],160)
  for field in ['count','new','revisions']:number(row[field])
  ids=unique_list(row['candidate_ids'],'distribution candidate');expected={vid for vid,p in byid.items()if topic in p['matched_topics']}
  require(ids==expected and len(ids)==row['count']==row['new']+row['revisions'],'Keyword distribution mismatch');require(row['new']==sum(byid[v]['change_type']=='new'for v in ids),'Topic new/revision mismatch')
 sources=o['evidence_sources'];require(isinstance(sources,list)and len(sources)<=len(records),'Invalid evidence list');evidence={}
 for source in sources:
  keys(source,EVIDENCE);vid=source['versioned_id'];m=VERSION.fullmatch(vid);require(m and vid in byid and vid not in evidence,'Evidence ID missing, duplicated or outside window');evidence[vid]=source
  require(source['version_url']=='https://arxiv.org/abs/'+vid and source['source_url']in {'https://arxiv.org/abs/'+vid,'https://arxiv.org/abs/'+m[1]},'Evidence URL/version mismatch');require(source['title']==byid[vid]['title'],'Evidence title mismatch');require(stamp(source['checked_at'])<=stamp(brief['generated_at']),'Evidence checked after brief generation');number(source['abstract_chars']);require(source['abstract_chars']>0,'Full abstract character count required');digest(source['abstract_sha256'])
  require(source['level']=='primary_complete_abstract'and source['source_type']in {'arxiv_api_atom','arxiv_abstract_page'},'Unsupported overview evidence')
  require(source['abstract_complete']is True and source['full_paper_read']is False and source['experiments_independently_verified']is False and source['version_comparison_performed']is False,'Abstract-only flags required')
 require(len(evidence)==cov['complete_abstracts_checked'],'Full abstract coverage count mismatch')
 caveats=o['keyword_caveats'];require(isinstance(caveats,list)and len(caveats)<=10,'Invalid keyword caveats')
 for c in caveats:
  keys(c,{'versioned_id','topic','issue','explanation','evidence_basis'});vid=c['versioned_id'];require(vid in byid and c['topic']in TOPICS,'Caveat outside window/topic set');string(c['explanation'],1000)
  require(c['issue']in {'false_positive','missed_match'}and c['evidence_basis']in {'snapshot_excerpt','complete_abstract'},'Unknown caveat evidence')
  require((c['topic']in byid[vid]['matched_topics'])==(c['issue']=='false_positive'),'Caveat contradicts actual keyword assignment')
  require(c['evidence_basis']!='complete_abstract'or vid in evidence,'Full-abstract caveat lacks evidence')
 themes=o['themes'];require(isinstance(themes,list)and len(themes)<=5,'At most five themes');require(brief['status']!='ready'or themes,'Ready overview requires themes');require(brief['status']not in {'error','no_material_update'}or not themes,'Error/no-material overview must not repeat themes');themeids=set()
 for t in themes:
  keys(t,THEME);require(re.fullmatch('[a-z][a-z0-9-]*',t['id']) and t['id']not in themeids,'Invalid theme ID');themeids.add(t['id'])
  for field,limit in [('title',100),('summary',500),('shared_problem',500),('open_question',1000)]:string(t[field],limit)
  require(t['attribution']=='curator_synthesis'and t['comparison_scope']=='within_window_no_temporal_trend','Theme attribution/comparison scope mismatch');strings(t['related_topics'],12)
  declared=unique_list(t['evidence_ids'],'theme evidence');require(declared and declared<=set(evidence),'Theme evidence is missing or unresolved');routes=t['method_routes'];require(isinstance(routes,list)and 1<=len(routes)<=6,'Invalid method routes');used=set()
  for route in routes:
   keys(route,{'text','evidence_ids'});string(route['text'],1000);ids=unique_list(route['evidence_ids'],'route evidence');require(ids and ids<=declared,'Route lacks valid evidence');used|=ids
  require(used==declared,'Theme evidence must equal method-route evidence union')
 return o

def validate_snapshot(brief,frontier,raw_sha256):
 """Cross-check the actual matching snapshot; archives retain their own bounded metadata."""
 require(brief['source_snapshot']['sha256']==raw_sha256,'Preview must match preserved source snapshot')
 o=validate_overview(brief);start,end=stamp(brief['window']['start']),stamp(brief['window']['end'])
 records=[{k:p[k]for k in CANDIDATE}for p in frontier['papers']if start<=stamp(p['updated_at'])<=end]
 require({p['versioned_id']:p for p in records}=={p['versioned_id']:p for p in o['candidate_records']},'Retained candidate metadata differs from actual source snapshot')
 return True

def source_link(source,label=None):
 e=html.escape;return '<a href="'+e(source['version_url'],quote=True)+'" target="_blank" rel="noopener noreferrer">'+e(label or source['title'])+' ↗</a>'

def render(data,index,prefix='',archive=False,preview=False):
 o=validate_overview(data);e=lambda x:html.escape(str(x),quote=True);count=data['counts'];sources={s['versioned_id']:s for s in o['evidence_sources']};themes=[]
 for i,t in enumerate(o['themes'],1):
  routes=''.join('<li><p>'+e(r['text'])+'</p><div class="radar-source-links">'+''.join(source_link(sources[v])for v in r['evidence_ids'])+'</div></li>'for r in t['method_routes'])
  themes.append(f'<details class="radar-theme"'+(' open'if i==1 else'')+f'><summary><span>{i:02d}</span><span class="radar-theme-copy"><span class="radar-theme-title" role="heading" aria-level="3">{e(t["title"])}</span><span class="radar-theme-summary">{e(t["summary"])}</span></span><i aria-hidden="true">＋</i></summary><div class="radar-theme-body"><h4>共同问题</h4><p>{e(t["shared_problem"])}</p><h4>不同的方法路线</h4><ul>{routes}</ul><div class="radar-question"><h4>接下来需要核查</h4><p>{e(t["open_question"])}</p></div><p class="radar-scope">窗口内编辑归纳 · 基于完整摘要 · 未作跨期趋势判断</p></div></details>')
 distribution=''.join(f'<div class="radar-distribution-row"><span>{e(row["label"])}</span><meter min="0" max="{max(1,count["window_candidates"])}" value="{row["count"]}">{row["count"]}</meter><b>{row["count"]}</b><small>{row["new"]} 首版 / {row["revisions"]} 修订</small></div>'for row in o['topic_distribution'])
 scope=''.join('<li>'+e(x)+'</li>'for x in o['limitations']);used={vid for t in o['themes']for vid in t['evidence_ids']}
 state={'ready':'','stale':'此页保留此前观察窗口；本次更新未完成。','no_material_update':'本窗口没有需要新增的研究主题，不重复上期总结。','error':'本期研究概览暂未完成。'}[data['status']]
 picks=[]
 for item in data['new_papers']+data['revised_papers']:
  picks.append(f'<details class="radar-pick"><summary><span>{"首版"if item["change_type"]=="new"else"修订"} · v{item["arxiv_version"]}</span><strong>{e(item["short_title"])}</strong></summary><div><p>{e(item["problem"])}</p><p><b>作者提出</b> {e(item["author_proposal"])}</p><p><b>相关性判断</b> {e(item["relevance"])}</p><p class="radar-scope">{e(item["evidence_limit"])}</p>{source_link(item)}</div></details>')
 records=''.join(f'<li data-radar-candidate data-search="{e((r["title"]+" "+r["versioned_id"]).casefold())}"><span>{"首版"if r["change_type"]=="new"else"修订"} · {e(r["versioned_id"])}</span><a href="https://arxiv.org/abs/{e(r["versioned_id"])}" target="_blank" rel="noopener noreferrer">{e(r["title"])}</a><small>{e(r["updated_at"])}</small></li>'for r in o['candidate_records'])
 caveat_html=''.join('<p><a href="https://arxiv.org/abs/'+e(c['versioned_id'])+'">'+e(next(r['title'] for r in o['candidate_records'] if r['versioned_id']==c['versioned_id']).split(':')[0])+'</a>：'+e(c['explanation'])+'</p>'for c in o['keyword_caveats'])
 data_href=prefix+('data/radar-preview/'if preview else'data/briefs/')+data['date']+'.json'
 root=Path(__file__).resolve().parents[1];assets=''.join('<'+('link rel="stylesheet" href="'if kind=='css'else'script defer src="')+prefix+'assets/radar-overview.'+kind+'?v='+hashlib.sha256((root/('assets/radar-overview.'+kind)).read_bytes()).hexdigest()[:12]+('">'if kind=='css'else'"></script>')for kind in ['css','js'])
 preview_note='<p class="radar-preview-label">Radar 设计预览 · 此样式现已用于正式 Radar</p>'if preview else''
 archives=''.join(f'<a href="{prefix}frontier/briefs/{e(entry["date"])}/index.html"'+(' aria-current="page"'if archive and entry['date']==data['date']else'')+f'>{e(entry["date"])}</a>'for entry in sorted(index['briefs'],key=lambda x:x['date'],reverse=True))
 archive_html='<nav class="radar-archive" aria-label="简报归档"><span>简报归档</span>'+archives+'</nav>'if not preview else''
 history_link=f'<a href="{prefix}frontier/briefs/2026-09-30/v1/index.html">最初摘要快照 ↗</a>'if data['date']=='2026-09-30'and not preview else''
 automation=('每日摘要更新已安排；本页显示最后发布的观察窗口。'if index['summary_automation_enabled']else'后续自动摘要更新尚未启用。')if not preview else''
 date_window=f'{e(data["window"]["start"])} → {e(data["window"]["end"])}（UTC）'
 state_html='<p class="radar-state">'+e(state)+'</p>'if state else''
 return f'''{assets}<section class="research-overview" id="daily-brief">{preview_note}{state_html}<header class="radar-lead"><p class="radar-date">{e(data['date'])} / Research Radar</p><h1>{e(o['headline'])}</h1><p class="radar-editorial">{e(o['executive_summary'])}</p><p class="radar-window">{date_window}</p><p class="radar-window-counts">{count['window_candidates']} 条窗口候选 <span>·</span> {count['new']} 篇首版 <span>·</span> {count['revisions']} 篇修订</p></header><div class="radar-editorial-layout"><div class="radar-main"><h2>本期研究主线</h2><p class="radar-section-note">先把问题与方法串起来，再按需要打开原始摘要。</p>{''.join(themes)}<section class="radar-revisions"><h2>怎样看待这些修订</h2><p>{e(o['revision_note'])}</p></section><section class="radar-picks"><h2>可进一步展开的摘要</h2><p>本期 {len(picks)} 篇摘要速览，作为研究概览之后的补充。</p>{''.join(picks)}</section></div><aside class="radar-evidence"><h2>这份概览读到了哪里</h2><p>观察对象是 arXiv 预印本候选；正式发表情况须另行核验，完整摘要核查不等于全文精读。</p><dl><div><dt>元数据 / 摘要片段筛查</dt><dd>{o['coverage']['candidate_metadata_screened']}</dd></div><div><dt>完整一手摘要</dt><dd>{len(sources)}</dd></div><div><dt>阅读全文 / 逐版比较</dt><dd>0 / 0</dd></div></dl><p>{len(used)} 篇摘要用于主题归纳；其余 {len(sources)-len(used)} 篇属于背景核查。作者报告的结果未独立复现。</p><ul>{scope}</ul><details class="radar-distribution"><summary>关键词分布与查询局限</summary><p>现有规则自动匹配，多标签计数重叠，不能相加成总数，也不代表研究热度或人工分类。</p>{distribution}</details><div class="radar-keyword-caveat"><strong>关键词标签存在误分与漏分，不能视为人工分类。</strong>{caveat_html}</div></aside></div><section class="radar-window-list"><div><h2>完整观察窗口</h2><p>浏览全部 {count['window_candidates']} 条元数据，避免只看到被展开的摘要。</p></div><label>搜索本窗口<input type="search" id="radar-candidate-search" placeholder="标题或 arXiv 编号"></label><p id="radar-candidate-count" role="status" aria-live="polite">{count['window_candidates']} 条候选</p><ul>{records}</ul><noscript><p>当前显示全部窗口候选；搜索需要 JavaScript，论文来源与原生展开控件仍可使用。</p></noscript><p id="radar-candidate-empty" hidden>没有匹配的窗口候选</p></section><footer class="radar-footer"><p>来源快照包含 {count['source_seven_day_candidates']} 条七日候选；本页只讨论上方所列观察窗口。</p><a href="{prefix}frontier/index.html#frontier-grid">查看现有 Radar 与七日候选 ↗</a><a href="{e(data_href)}">查看公开概览数据 ↗</a>{history_link}{archive_html}<p>{automation}</p></footer></section>'''
