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

def compact_text(text):
 """Use an existing complete sentence/clause; never generate a new conclusion."""
 return re.split(r'(?<=[。！？；])',text,maxsplit=1)[0]

def render(data,index,prefix='',archive=False,preview=False):
 o=validate_overview(data);e=lambda x:html.escape(str(x),quote=True);count=data['counts'];weekly=data['schema_version']=='weekly-1.0'
 sources={s['versioned_id']:s for s in o['evidence_sources']};selections={s['versioned_id']:s for s in data.get('new_papers',[])+data.get('revised_papers',[])}
 period='weekly' if weekly else 'daily';entries=index['weeks' if weekly else 'briefs'];route='weekly' if weekly else 'briefs'
 def theme_link(t,label=None):return '<a href="#theme-'+e(t['id'])+'" data-radar-action="theme" data-theme="'+e(t['id'])+'">'+e(label or t['title'].split('：')[0])+'</a>'
 def paper_link(vid,theme='',origin='theme'):
  s=sources.get(vid) or next(r for r in o['candidate_records'] if r['versioned_id']==vid)
  return '<a href="#paper-'+e(vid)+'" data-radar-action="paper" data-paper="'+e(vid)+'" data-theme="'+e(theme)+'" data-origin="'+origin+'">'+e(s['title'])+'</a>'
 choices=[];themes=[]
 for i,t in enumerate(o['themes'],1):
  short=t['title'].split('：')[0];tid=e(t['id'])
  choices.append(f'<a class="radar-theme-choice" id="choose-{tid}" href="#theme-{tid}" data-radar-action="theme" data-theme="{tid}"><span class="radar-choice-title"><b>{i:02d} · {e(short)}</b><small>{len(set(t["evidence_ids"]))} 篇来源</small></span><span class="radar-choice-summary">{e(compact_text(t["summary"]))}</span></a>')
  routes=''.join('<li><p>'+e(r['text'])+'</p><div class="radar-source-links">'+''.join(paper_link(v,t['id']) for v in r['evidence_ids'])+'</div></li>' for r in t['method_routes'])
  themes.append(f'<details class="radar-theme" id="theme-{tid}" data-radar-theme="{tid}"><summary><span>{i:02d}</span><span class="radar-theme-copy"><span class="radar-theme-title" role="heading" aria-level="3">{e(t["title"])}</span></span><i aria-hidden="true">＋</i></summary><div class="radar-theme-body"><a href="#radar-overview" data-radar-action="overview">← 返回窗口总览</a><h2 id="heading-{tid}" tabindex="-1">{e(t["title"])}</h2><p>{e(t["summary"])}</p><h3>共同问题</h3><p>{e(t["shared_problem"])}</p><h3>不同的方法路线</h3><ul>{routes}</ul><div class="radar-question"><h3>接下来需要核查</h3><p>{e(t["open_question"])}</p></div><p class="radar-scope">窗口内编辑归纳 · 基于完整摘要 · 未作跨期趋势判断，不代表领域共识</p></div></details>')
 papers=[]
 for r in o['candidate_records']:
  vid=r['versioned_id'];source=sources.get(vid);item=selections.get(vid);members=[t for t in o['themes'] if vid in t['evidence_ids']]
  membership=''.join(theme_link(t) for t in members) or '未用于本窗口主线归纳'
  content=''
  if item:
   content='<div data-radar-selection><h3>'+e(item['short_title'])+'</h3><p>'+e(item['problem'])+'</p><p><b>作者提出</b> '+e(item['author_proposal'])+'</p><p><b>相关性判断 · 编辑推断</b> '+e(item['relevance'])+'</p><p>'+e(item['evidence_limit'])+'</p></div>'
   overlap=item['curated_catalog_overlap']
   if overlap['already_present']:content+='<a href="'+prefix+'papers/'+e(overlap['catalog_id'])+'/index.html">查看已有目录与阅读档案 ↗</a>'
  else:content='<p class="radar-scope">未保存独立摘要速览；以下仅展示已有主线路线与来源记录，不补写单篇结论。</p>'
  routes=''.join('<li><b>'+e(t['title'].split('：')[0])+'</b><p>'+e(x['text'])+'</p></li>' for t in members for x in t['method_routes'] if vid in x['evidence_ids'])
  if routes:content+='<details class="radar-paper-routes"><summary>已有主线路线 · 可能同时涉及其他论文</summary><ul>'+routes+'</ul></details>'
  if source:content+='<p>证据：完整一手摘要 · '+e(source['source_type'])+' · 核查 '+e(source['checked_at'])+'</p><p>阅读全文 / 逐版比较：0 / 0；作者结果未独立复现。此处未核查代码。</p><details><summary>摘要证据校验记录</summary><p>'+str(source['abstract_chars'])+' 字符 · SHA-256 '+e(source['abstract_sha256'])+'</p></details>'
  else:content+='<p>仅保留候选元数据；本窗口没有完整摘要核查记录，未完成全文精读、代码核查或版本比较。</p>'
  papers.append('<details class="radar-paper" id="paper-'+e(vid)+'" data-radar-paper="'+e(vid)+'" data-paper-themes="'+e(' '.join(t['id'] for t in members))+'"><summary>'+e(r['title'])+'</summary><div><a href="#radar-overview" data-radar-action="return">← 返回上一层</a><h2 id="paper-heading-'+e(vid)+'" tabindex="-1">'+e(r['title'])+'</h2><p>'+e(vid)+' · '+('首版' if r['change_type']=='new' else '修订')+'</p><nav class="radar-memberships" aria-label="论文所属主线">'+membership+'</nav>'+content+'<p>首次提交 '+e(r['first_submitted_at'])+' · 最近更新 '+e(r['updated_at'])+'</p><p>'+source_link({'version_url':'https://arxiv.org/abs/'+vid},'打开固定版本 arXiv 原始记录')+'</p></div></details>')
 records=''.join('<li data-radar-candidate data-search="'+e((r['title']+' '+r['versioned_id']).casefold())+'"><span>'+('首版' if r['change_type']=='new' else '修订')+' · '+e(r['versioned_id'])+'</span>'+paper_link(r['versioned_id'],origin='candidates')+'<small>'+e(r['updated_at'])+'</small></li>' for r in o['candidate_records'])
 distribution=''.join(f'<div class="radar-distribution-row"><span>{e(row["label"])}</span><meter min="0" max="{max(1,count["window_candidates"])}" value="{row["count"]}">{row["count"]}</meter><b>{row["count"]}</b><small>{row["new"]} 首版 / {row["revisions"]} 修订</small></div>' for row in o['topic_distribution'])
 caveats=''.join('<p>'+paper_link(c['versioned_id'],origin='evidence')+'：'+e(c['explanation'])+'</p>' for c in o['keyword_caveats'])
 used={vid for t in o['themes'] for vid in t['evidence_ids']};scope=''.join('<li>'+e(x)+'</li>' for x in o['limitations'])
 state={'ready':'','stale':'更新未完成，保留原始成功观察窗口与旧内容。' if weekly else '此页保留此前观察窗口；本次更新未完成。','no_material_update':'本周没有新增研究主线；不拼接或重复旧日报。' if weekly else '本窗口没有需要新增的研究主题，不重复上期总结。','error':'本期研究概览暂未完成；此状态不代表没有新论文。'}[data['status']]
 state_html='<p class="radar-state">'+e(state)+'</p>' if state else ''
 root=Path(__file__).resolve().parents[1];assets=''.join('<'+('link rel="stylesheet" href="' if kind=='css' else 'script defer src="')+prefix+'assets/radar-overview.'+kind+'?v='+hashlib.sha256((root/('assets/radar-overview.'+kind)).read_bytes()).hexdigest()[:12]+('">' if kind=='css' else '"></script>') for kind in ['css','js'])
 archives=''.join('<a href="'+prefix+'frontier/'+route+'/'+e(row['date'])+'/index.html"'+(' aria-current="page"' if archive and row['date']==data['date'] else '')+'>'+e(row['date'])+'</a>' for row in sorted(entries,key=lambda x:x['date'],reverse=True))
 data_href=prefix+('data/radar-preview/' if preview else 'data/weekly/' if weekly else 'data/briefs/')+data['date']+'.json'
 history='<a href="'+prefix+'frontier/briefs/2026-09-30/v1/index.html">最初摘要快照 ↗</a>' if data['date']=='2026-09-30' and not preview else ''
 manifest='<a href="'+prefix+'data/weekly/'+data['date']+'/manifest.json">冻结候选来源清单 ↗</a>' if weekly else ''
 automation=(('每周摘要更新已安排。' if index['summary_automation_enabled'] else '周报自动更新尚未启用。') if weekly else ('每日摘要更新已安排；本页显示最后发布的观察窗口。' if index['summary_automation_enabled'] else '后续自动摘要更新尚未启用。')) if not preview else ''
 boundary=(('完整（相对于所记录查询和窗口）' if data['source_snapshot']['coverage_complete'] else '部分覆盖；候选数不是本周全部相关论文') if weekly else data['coverage_note'])
 date_window=e(data['window']['start'])+' → '+e(data['window']['end'])+'（UTC，按更新时间）'
 compact_window=data['window']['start'][5:16].replace('T',' ')+' → '+data['window']['end'][5:16].replace('T',' ')+' UTC'
 preview_note='<p class="radar-preview-label">Radar 设计预览 · 此样式现已用于正式 Radar</p>' if preview else ''
 return f'''{assets}<section class="research-overview" id="{'weekly-brief' if weekly else 'daily-brief'}" data-radar-period="{period}" data-radar-date="{e(data['date'])}">{preview_note}{state_html}<header class="radar-lead"><p class="radar-date">{e(data['date'])} / {'WEEKLY RESEARCH RADAR' if weekly else 'Research Radar'} · {'周报' if weekly else '日报'} <span>{e(compact_window)}</span></p><h1>{e(o['headline'])}</h1><p class="radar-editorial">{e(compact_text(o['executive_summary']))}</p><p class="radar-window-counts">{count['window_candidates']} 条窗口候选 · {count['new']} 篇首版 · {count['revisions']} 篇修订 <span>完整摘要 {len(sources)} · 全文 / 逐版比较 0 / 0</span></p></header><div class="radar-reading-layout"><nav class="radar-theme-nav" id="radar-overview" aria-label="全部研究主线"><h2 tabindex="-1" id="radar-overview-heading">{'七天研究主线' if weekly else '本期研究主线'} <small>{len(choices)} 条</small></h2>{''.join(choices)}<p class="radar-scope">窗口内对照，来源可重叠；不代表全领域共识或跨期趋势</p><nav class="radar-view-links" aria-label="其他窗口视图"><a href="#radar-candidates" data-radar-action="candidates">全部候选（{count['window_candidates']}）</a><a href="#radar-evidence" data-radar-action="evidence">证据与范围</a><a href="#radar-archives">历史窗口</a></nav></nav><div class="radar-focus">{''.join(themes)}{''.join(papers)}<details class="radar-window-list" id="radar-candidates" data-radar-view="candidates"><summary>完整观察窗口 · {count['window_candidates']} 条候选</summary><div><a href="#radar-overview" data-radar-action="overview">← 返回窗口总览</a><h2 tabindex="-1" id="radar-candidates-heading">全部窗口候选</h2><p>保留全部 {count['window_candidates']} 条元数据；点论文查看本站已有证据。</p><label>搜索本窗口<input type="search" id="radar-candidate-search" placeholder="标题或 arXiv 编号"></label><p id="radar-candidate-count" role="status" aria-live="polite">{count['window_candidates']} 条候选</p><ul>{records}</ul><p id="radar-candidate-empty" hidden>没有匹配的窗口候选</p></div></details><details class="radar-evidence" id="radar-evidence" data-radar-view="evidence"><summary>证据、背景与查询范围</summary><div><a href="#radar-overview" data-radar-action="overview">← 返回窗口总览</a><h2 tabindex="-1" id="radar-evidence-heading">这份概览读到了哪里</h2><p>{e(o['executive_summary'])}</p><p class="radar-window">{date_window}</p><p>{e(boundary)}</p><p>{count['window_candidates']} 条元数据 / 摘要片段筛查；{len(sources)} 篇完整一手摘要；阅读全文 / 逐版比较：0 / 0</p><p>{len(used)} 篇摘要用于主题归纳；其余 {len(sources)-len(used)} 篇属于背景核查。作者结果未独立复现；完整摘要核查不等于全文精读。</p><h3>可进一步展开的摘要</h3><p>仅 {len(selections)} 篇保存独立摘要速览，内容已合入对应论文；其他候选只展示实际已有记录。</p><h3>修订的解释边界</h3><p>{e(o['revision_note'])}</p><ul>{scope}</ul><details class="radar-distribution"><summary>关键词分布与查询局限</summary><p>现有多标签关键词规则，计数重叠，不能相加成总数；不是人工分类、研究热度或人工推荐。</p>{distribution}</details><div class="radar-keyword-caveat"><strong>关键词标签存在误分与漏分，不能视为人工分类。</strong>{caveats}</div><p>来源抓取：{e(data['source_snapshot']['fetched_at'])}；生成：{e(data['generated_at'])}</p><p>源快照 SHA-256：{e(data['source_snapshot']['sha256'])}</p><p>来源快照包含 {count['source_seven_day_candidates']} 条七日候选；本页只讨论所列观察窗口，不改变目录、Stage 或复现状态。</p><a href="{e(data_href)}">查看公开概览数据 ↗</a>{manifest}</div></details></div></div><noscript><p>当前为无脚本阅读：全部主线均在上方，点标题定位后展开正文；单篇来源位于对应论文内。搜索与自动聚焦需要 JavaScript。</p></noscript><footer class="radar-footer" id="radar-archives"><nav class="radar-archive" aria-label="{'周报' if weekly else '简报'}归档"><span>历史窗口</span>{archives}{history}</nav><a href="{prefix}frontier/index.html#frontier-grid">七日发现队列与抓取记录 ↗</a><p>{automation}</p></footer></section>'''
