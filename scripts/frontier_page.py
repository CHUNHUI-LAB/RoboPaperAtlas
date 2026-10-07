"""Render the separate, explicitly unreviewed preprint discovery feed."""
import html,re
from urllib.parse import urlsplit

def render(data,catalog,shell,link,brief_html='',overview=False):
    e=lambda v:html.escape(str(v) if v is not None else '',quote=True)
    status=data.get('status','not_fetched'); papers=data.get('papers',[]); coverage=data.get('coverage',{})
    status_labels={'success':'抓取成功','ok':'抓取成功','limited':'部分抓取','stale':'上次成功快照（本次失败）','partial':'部分抓取','failed':'抓取失败','error':'抓取失败','not_fetched':'尚未发布抓取结果'}
    dates=[('当前快照抓取',data.get('fetched_at')),('最近成功',data.get('last_successful_fetch_at')),('最近失败',data.get('last_failed_fetch_at'))]
    date_html=''.join(f'<div><dt>{label}</dt><dd>{e(value or "尚无记录")}</dd></div>' for label,value in dates)
    canonical={}
    for p in catalog['papers']:
        match=re.search(r'arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]+)',p.get('preprint_url') or '')
        if match: canonical[match[1]]=p['id']
    cards=[]
    core={'vln_objectnav','navigation_agents','spatial_episodic_memory','mobile_manipulation','whole_body_control','end_effector_trajectories'}
    labels_zh={'vln_objectnav':'VLN / ObjectNav','navigation_agents':'导航智能体与 Harness','spatial_episodic_memory':'空间记忆与反馈','mobile_manipulation':'四足机械臂与移动操作','whole_body_control':'WBC · Whole-body Control','end_effector_trajectories':'末端轨迹','robot_vla':'VLA · Vision-Language-Action（延伸相关）','robot_moe':'MoE（延伸相关）','robot_world_models':'世界模型（延伸相关）'}
    papers=sorted(papers,key=lambda p:(not bool(core.intersection(p.get('matched_topics',[]))), -(int(p.get('updated_at','0')[:4]) if p.get('updated_at') else 0)))
    for p in papers:
        rid=p.get('canonical_id') or p.get('id'); overlap=canonical.get(rid); authors=p.get('authors',[])
        reasons=p.get('relevance_reasons',[])
        reason_html=''
        for r in reasons:
            if isinstance(r,dict):
                evidence='；'.join(('标题' if v.get('field')=='title' else '摘要')+'：'+', '.join(v.get('matched_phrases',[])) for v in r.get('evidence',[]))
                reason_html+='<li><strong>'+e(labels_zh.get(r.get('topic'),r.get('label')) )+'</strong><br>'+e(evidence)+'</li>'
            else: reason_html+='<li>'+e(r)+'</li>'
        topics=p.get('matched_topics',[]); labels=labels_zh; tags=''.join(f'<span>{e(labels.get(t,t))}</span>' for t in topics)
        change='新版修订' if p.get('change_type')=='revision' else '首次提交'
        known=f'<a class="frontier-overlap" href="../papers/{e(overlap)}/index.html">已在论文目录中 ↗</a>' if overlap else '<span class="frontier-unreviewed">发现候选 · 尚未人工审核</span>'
        cards.append(f'''<article class="frontier-card" data-topics="{e(" ".join(topics))}" data-focus="{str(bool(core.intersection(topics))).lower()}"><div class="frontier-card-top"><span>{e(rid)} · v{e(p.get('arxiv_version'))}</span><span>{change}</span></div><h2>{link(p.get('version_url') or p.get('source_url'),p['title'])}</h2><p class="frontier-authors">{e(', '.join(authors))}</p><div class="tags">{tags}</div><div class="frontier-dates"><span>首次提交 {e(p.get('first_submitted_at'))}</span><span>最近修订 {e(p.get('updated_at'))}</span></div><details><summary>查看摘要摘录</summary><p class="abstract">{e(p.get('abstract_excerpt',''))}{"…" if p.get("abstract_truncated") else ""}</p><p class="fine-print">摘录可能截断；完整摘要请查看 arXiv 原始记录。</p></details><details><summary>为什么匹配这个方向？</summary><ul>{reason_html}</ul><p class="fine-print">基于公开标题 / 摘要关键词的启发式匹配，不代表质量排序、专家推荐或已完成精读。</p></details><div class="frontier-card-bottom">{known}{link(p.get('source_url'),'arXiv 原始记录','text-link')}</div></article>''')
    limitations=coverage.get('limitations',[])
    if isinstance(limitations,str): limitations=[limitations]
    coverage_html='<li>仅覆盖记录的查询与分类；索引延迟和术语差异可能遗漏相关工作。</li><li>关键词匹配未经过人工审核；首次提交/修订不代表论文创新性或录用状态。</li>'
    if data.get('fetch_error'): coverage_html+='<li>'+e(data['fetch_error'])+'</li>'
    filter_options=''.join(f'<option value="{key}">{e(label)}</option>' for key,label in labels_zh.items())
    period=' → '.join(str(coverage[k]) for k in ('window_start','window_end') if coverage.get(k)) or '尚无已核验抓取窗口'
    results=''.join(cards) or '<div class="empty-state"><h3>暂时没有已发布的发现结果</h3><p>抓取结果就绪后会显示真实候选；这里不会用示例论文填充。</p></div>'
    body=f'''<main id="main" class="frontier-main"><p class="eyebrow">AT THE RESEARCH FRONTIER</p><div class="frontier-heading"><div><h1>Radar<span class="frontier-accent"> / 前沿动态</span></h1><p>先读本期重点，再探索新论文与版本更新。<br>所有判断都保留来源，也保留证据边界。</p></div><span class="frontier-status">{e(status_labels.get(status,status))} · {len(papers)} 条候选</span></div>{brief_html}<div class="frontier-boundary"><strong>发现队列与精读目录分开维护</strong><p>这些条目是未经人工审核的预印本候选，可能存在关键词误匹配；不代表同行评审通过，也不代表已完成 Stage 1 / 2 / 3。正式纳入阅读时，仍优先核验会议或期刊出版版本。</p></div><section class="feed-metadata" aria-label="抓取透明度"><div><h2>抓取记录</h2><dl>{date_html}</dl></div><div><h2>覆盖范围</h2><p>{e(period)}</p><p>结果覆盖：{'完整（相对于所记录查询和窗口）' if coverage.get('complete') else '未证明完整 / 可能仅部分结果'}</p><p>达到候选上限而截断：{'是' if coverage.get('truncated') else '否'}</p><p><a class="text-link" href="../data/frontier.json">查看公开快照与完整查询 ↗</a></p><p>已安排每日更新（约 08:00 UTC）；本页显示最后发布快照，实际抓取状态见记录。</p><ul>{coverage_html}</ul></div></section><div class="frontier-results-label"><h2>继续探索</h2><p>自动匹配候选 · 下方为采集查询标签，与 Library 中的研究问题分类分开 · 不代表推荐或精读完成</p></div><div class="frontier-controls"><label>候选查询标签 <select id="frontier-topic"><option value="focused">核心方向优先</option><option value="all">全部候选（含延伸相关）</option>{filter_options}</select></label><span id="frontier-count" role="status" aria-live="polite"></span></div><div class="frontier-grid" id="frontier-grid">{results}</div><button type="button" class="load-more" id="frontier-more" hidden>显示更多候选 ↓</button><div id="frontier-empty" class="empty-state" hidden>当前方向没有匹配候选</div><p class="fine-print">摘要与元数据来自 arXiv 原始记录。各论文权益归原作者与相应权利人；本页不重新分发 PDF。显示的英文时间为 UTC 原始时间戳。</p></main>'''
    if overview:
        start=body.index(brief_html)
        body='<main id="main" class="frontier-main radar-production">'+brief_html+'<details class="radar-discovery" id="radar-discovery"><summary>七日发现队列与抓取记录（'+str(len(papers))+' 条）</summary>'+body[start+len(brief_html):].replace('</main>','</details></main>')
    return shell('前沿动态',body,prefix='../',page='frontier')
