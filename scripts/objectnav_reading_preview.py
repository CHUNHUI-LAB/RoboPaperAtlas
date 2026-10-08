"""Build one isolated, versioned ObjectNav reading example; never mutate trees."""
import hashlib
import html
import json
import os
import stat
from pathlib import Path
import tempfile
from radar_c2_preview import read_regular, validate_tree, SOURCE_DIRS
from build_topic_preview import require, safe_path, safe_target

ROUTE = 'review/objectnav-reading-v1'
SOURCE = 'previews/objectnav-reading-v1'
FILES = frozenset(('content.json', 'style.css', 'reader.js'))
MANIFEST = 'scripts/objectnav_reading_manifest.json'
CONTENT_SHA256 = 'dd7ec946ff10658cc7bca5cdd04bdf514d6301691c7d66ad12dcd4bb7b6edb9e'

def esc(value):
    return html.escape(str(value), quote=True)

def external(url, label):
    require(url.startswith('https://'), 'Evidence URL must use HTTPS')
    return '<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' <span class="sr-only">（新标签页）</span>↗</a>'

def payloads(root):
    root = Path(root).absolute()
    validate_tree(root, root / SOURCE, FILES)
    manifest = json.loads(read_regular(root, root / MANIFEST))
    require(manifest['version']=='objectnav-reading/1', 'Unknown exemplar version')
    require(manifest['status']=='isolated_candidate_pending_browser_review', 'Invalid review status')
    require(set(manifest['files'])==FILES, 'Unexpected exemplar files')
    payload = {name:read_regular(root,root / SOURCE / name) for name in FILES}
    for name, content in payload.items():
        require(hashlib.sha256(content).hexdigest()==manifest['files'][name], 'Unreviewed exemplar bytes: '+name)
    require(hashlib.sha256(payload['content.json']).hexdigest()==CONTENT_SHA256,'Science projection changed')
    data=json.loads(payload['content.json'])
    require(data['version']=='objectnav-reading/1','Unknown content version')
    require(len(data['template'])==59 and len(data['poni']['answers'])==22,'PONI scope changed')
    require(len({n['source_id'] for n in data['template']})==59,'Duplicate template identity')
    require(len({a['template_node_id'] for a in data['poni']['answers']})==22,'Duplicate answer')
    require(all(a['template_node_id'] in {n['source_id'] for n in data['template']} for a in data['poni']['answers']), 'Unbound answer')
    return payload, data

def render(data, payload):
    sources=data['sources']; poni=sources['poni2022']['url']; sem=sources['semexp2020']['url']
    def cite(key, label): return external(sources[key]['url'],label)
    def psource(label): return external(poni,label)
    answers={a['template_node_id']:a for a in data['poni']['answers']}
    nodes=data['template']; byid={n['id']:n for n in nodes}
    def answer_node(n, level=0):
        answer=answers.get(n['source_id']); children=[x for x in nodes if x.get('parent')==n['id']]
        aid='analysis-'+n['source_id']
        content='<article class="answer" id="'+esc(aid)+'" tabindex="-1" data-template-id="'+esc(n['source_id'])+'"><h4>'+esc(n['label']).replace('\n','<br>')+'</h4>'
        if n.get('structural_note'):
            content+='<p class="note">原结构注记：'+esc(n['structural_note'])+'</p>'
        if n.get('note'):
            content+='<details class="original-note"><summary>查看原图注记（保留原意，并非本页建议）</summary><p>'+esc(n['note']).replace('\n','<br>')+'</p><p class="boundary">这里保留原图文字供核对，不是隐瞒真实限制的指令。应如实报告方法缺陷、任务边界与未验证之处。</p><p class="note">'+esc(n.get('interpretation_note',''))+'</p></details>'
        if answer:
            content+='<p class="answer-status">已核部分 · '+esc(answer['attribution'])+'</p><p>'+esc(answer['text'])+'</p>'
            if answer.get('slot_binding'):content+='<p class="note">本篇对应：'+esc(answer['slot_binding'])+'</p>'
            content+='<p class="source">'+ ' · '.join(external(e['source_url'],e['locator']) for e in answer['evidence_refs'])+'</p>'
            if answer.get('scope_note'):content+='<p class="note">'+esc(answer['scope_note'])+'</p>'
        else:content+='<p class="note">未填写。保留原模板位置，不据此推断论文缺少该内容。</p>'
        content+='</article>'
        if children:content+='<div class="answer-children">'+''.join(answer_node(x,level+1) for x in children)+'</div>'
        return content
    analysis=''
    for chapter in [x for x in nodes if x.get('parent')=='paper-analysis-tree']:
        analysis+='<details id="chapter-'+esc(chapter['id'])+'"><summary>'+esc(chapter['label'])+'</summary>'+answer_node(chapter)+'</details>'
    ci=''
    ci_names={'insight':'Insight：为什么换一种学法？','technical_approach':'具体怎么实现？','why':'为什么两种潜力互补？','evidence':'什么证据支持这个解释？','boundary':'结论到哪里为止？'}
    for claim in data['claims']:
        kind=claim['id'].split(':')[-1]
        if kind not in ci_names:continue
        ci+='<article class="evidence-item"><h3>'+ci_names[kind]+'</h3><p>'+esc(claim['statement'])+'</p><p class="source">'+external(claim['source_url'],claim['locator'])+'</p></article>'
    css=hashlib.sha256(payload['style.css']).hexdigest()[:16];js=hashlib.sha256(payload['reader.js']).hexdigest()[:16]
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>ObjectNav：从任务到 PONI 证据 · RoboPaperAtlas 试读</title><link rel="icon" href="../../assets/favicon.svg"><link rel="stylesheet" href="style.css?v={css}"><script src="reader.js?v={js}" defer></script></head>
<body><a class="skip" href="#overview">跳到正文</a><header class="site-header"><a class="brand" href="../../index.html">RoboPaperAtlas</a><a href="../radar-c2-analysis/index.html">原三树入口 →</a></header>
<main><header class="hero"><p class="eyebrow">隔离试读 · ObjectNav · v1</p><h1>找一把椅子，<br>机器人该先往哪走？</h1><p class="lead">先理解任务，再把方法放在同一张研究地图上。最后看清 PONI 保留了什么、替换了什么，以及证据在哪里。</p><p class="boundary">这是一个选择性阅读示范，不是整个 ObjectNav 领域的完整分类；不改变论文阅读完成状态。</p><nav class="jump-links" aria-label="本页快速阅读"><a href="#overview">01 任务与条件</a><a href="#comparison">02 方法比较</a><a href="#poni-evidence">03 PONI 证据</a><a href="#analysis">直达部分论文解析</a></nav></header>
<section id="overview" tabindex="-1"><p class="eyebrow">01 / 总览</p><h2>ObjectNav 要解决什么？</h2><p class="section-lead">{esc(data['task']['definition_zh'])}。</p><div class="example"><span class="label">一个具体例子 · 编辑示意</span><p>机器人刚进入一个陌生室内环境，收到类别目标“chair”。它没有椅子的坐标，需要边观察边寻找，走到符合评测条件的一把椅子附近并主动 STOP。</p><p>目标是任一合格的椅子，不是照片中指定的那一把；“没有预先地图”也不表示没有位姿或里程计输入。</p></div><div class="definition-grid"><div><h3>给了什么</h3><p>目标类别；每个方法/协议规定的传感观测和动作。目标位置不提供。</p></div><div><h3>怎样算完成</h3><p>找到合格实例并主动停止。具体距离、可见性、预算与评测器要按对应协议核对。</p></div></div><p class="source">任务与评测入口：{cite('obj20','ObjectNav Revisited · arXiv v2 · §2–3')}。该文讨论任务标准化与 Habitat 2020 Challenge；它不意味着下列方法共享完全相同的评测器。</p>
<details id="protocol"><summary>展开 benchmark / 方法条件：哪些能比，哪些不能直接比？</summary><p>这里比较的是条件和接口，没有跨论文分数排行榜。Success 看是否完成目标，SPL 同时考虑路径效率；数值只有在数据集、场景划分、传感与评测协议一致时才有可比意义。</p><div class="protocol-grid"><article><h3>SemExp · NeurIPS 2020</h3><p>类别目标；RGB-D 与 sensor pose。论文 §3 描述主动 stop、目标附近 1 m、500 步预算。</p><p>类别语义地图；交互 RL 学习长程探索目标；解析局部执行。</p><p class="source">{cite('semexp2020','正式论文 §3 / Fig.2')}</p></article><article><h3>PONI · CVPR 2022</h3><p>类别目标；RGB-D 与里程计汇聚的相对位姿。论文 §3.1 描述主动 stop、1 m、500 步。</p><p>离线完整语义地图产生训练标签；推理时仍逐步观测、建图和移动。</p><p class="source">{psource('正式论文 §3.1、§3.4–3.6')}</p></article><article><h3>VLFM · arXiv v1 选段核读</h3><p>RGB-D、odom 与目标文本；occupancy/frontier map 加目标特定的视觉语言 value/confidence map。</p><p>仿真执行器是训练过的 PointNav；真实 Spot 使用 BD API（§VI-C，作者限定路径相对无障碍）。不能把“zero-shot”写成全系统从未训练。</p><p class="source">{external(data['vlfm']['pipeline_contract'] and 'https://arxiv.org/html/2312.03275v1','固定 v1 · §IV、§VI-C、§VII')}</p><p class="note">本页新增核对 arXiv:2312.03275v1（2023-12-06）的相关选段；不称为 ICRA 正式终稿。此处不补推 VLFM 的数值成功判据。</p></article></div><p class="boundary">SemExp 与 PONI 的“1 m / 500 步”只是各文任务说明，不能据此宣称完整 evaluator 等价；VLFM 的感知表示、训练来源与执行器也须分别比较。</p></details></section>
<section id="comparison" tabindex="-1"><p class="eyebrow">02 / 研究地图</p><h2>同一个目标，三种搜索决策</h2><p class="section-lead">先看表示、选点与执行。SemExp 和 PONI 共享语义地图式接口；VLFM 以目标相关的图文评分构建另一种 value map。</p><div class="method-grid"><article class="method"><p class="label">语义地图式路线</p><h3>SemExp</h3><ol class="pipeline"><li>RGB-D ＋位姿 → 类别语义地图</li><li>目标条件探索策略 → 长程目标点</li><li>解析局部执行 → 新观测与地图更新</li></ol><dl><dt>搜索决策怎么学</dt><dd>与环境交互的强化学习。</dd><dt>在本页的角色</dt><dd>用于理解 PONI 所承接的接口与替换位置；不授予整个 ObjectNav 的全球首作地位。</dd></dl><p class="source">{cite('semexp2020','§3 / Fig.2')}</p></article><article class="method featured"><p class="label">同一接口，改变长程搜索学习</p><h3>PONI</h3><ol class="pipeline"><li>RGB-D ＋位姿 → 部分类别语义地图</li><li>面积潜力 ＋ 目标潜力 → 长程目标点</li><li>解析局部执行 → 新观测与地图更新</li></ol><dl><dt>搜索决策怎么学</dt><dd>完整标注地图生成潜力标签，部分地图作输入，离线监督训练。</dd><dt>它改了哪里</dt><dd>“下一处去哪找”的预测与训练方式；不是替换整个导航闭环。</dd></dl><a href="#poni-evidence">看保留 / 替换 / 依据 ↓</a><p class="source">{psource('§3.2–3.6')}</p></article><article class="method"><p class="label">视觉语言 value-map 路线</p><h3>VLFM</h3><ol class="pipeline"><li>RGB ＋ 目标文本 → BLIP-2 相关性评分</li><li>空间 value/confidence map ＋ frontier → 搜索方向</li><li>仿真 PointNav / 真实机器人 API → 更新地图与检测</li></ol><dl><dt>表示差异</dt><dd>主要搜索评分来自整幅画面与目标文本的相关性，不是先把场景压成类别标签语义图。</dd><dt>必须保留的边界</dt><dd>根据 §IV-B 的相关性定义，不能把评分当作校准目标存在概率（定义边界判断）；§VII 明确地图针对当前目标，不能默认跨目标复用。</dd></dl><p class="source">{external('https://arxiv.org/html/2312.03275v1','固定 v1 · §IV-B–D、§VI-C、§VII')}</p></article></div><p class="boundary">“根据部分语义图决定去哪找”是本页地图式路线中的局部问题，不是所有 ObjectNav 方法必须使用的全领域分解。这里也没有把 VLFM 画成 PONI 的直接后继。</p><details><summary>辅助关系图：只概括本页关系</summary><div class="relation"><p>ObjectNav 类别目标任务</p><ul><li>语义地图式接口 → SemExp → PONI 的长程搜索替换</li><li>视觉语言 value-map 接口 → VLFM</li></ul><p class="note">第一条箭头表示本页已核的接口承接与局部替换；第二条不宣称历史继承。文字比较和证据可独立阅读。</p></div></details></section>
<section id="poni-evidence" tabindex="-1"><p class="eyebrow">03 / 深入阅读</p><h2>PONI 到底改了什么？</h2><p class="section-lead">保留可积累的语义地图和局部执行，把昂贵交互学得的长程搜索选择，改成从离线地图学得的双潜力预测。</p><div class="evidence-grid"><article><span class="label">保留</span><h3>语义建图与局部执行接口</h3><p>PONI §3.4 说明沿用 SemExp 的语义建图；§5 的对应比较控制 mapper 与 local policy。不能把模块接口相同理解成所有权重和实现细节都相同。</p><p class="source">{psource('核对 §3.4、§5')}</p></article><article><span class="label">替换</span><h3>长程搜索预测与训练信号</h3><p>部分语义图输入潜力网络，预测 area / object potential，再组合为长程搜索点。训练标签来自完整标注地图，无需交互导航 rollout 来训练这一网络。</p><p class="source">{psource('核对 §3.3、Fig.2–3、§3.6')}</p></article><article><span class="label">依据</span><h3>同文对照和双潜力消融</h3><p>§5 的同条件对照与 Table 3 消融用于检验收益；去掉任一潜力都会损失性能。GT segmentation 是特权感知设置，不应混入一般方法比较。</p><p class="source">{psource('核对 §5、Table 1 / 3')}</p><a href="#analysis-ablation-core">直达已核消融解析 ↓</a></article></div><p class="boundary">Interaction-free 不等于无需训练或无需数据。训练仍依赖标注 3D 场景/完整语义地图；本页证据不是独立复现，也不证明开放词汇或真实噪声下的普适鲁棒性。</p>
<details id="challenge"><summary>Challenge → Insight：为什么这个替换有意义？</summary><p class="section-lead">覆盖更多未知空间，不一定更快找到指定目标。</p>{ci}<a href="#comparison">↑ 返回方法比较</a></details></section>
<section id="analysis" tabindex="-1"><h2>PONI：按需打开原论文解析</h2><p class="section-lead">22 / 59 个原模板节点有已核回答，其余 37 个保持未填写。</p><p>保留原图的五章、顺序、层级、注记与非对称贡献槽位。以下是选定章节的部分解析，不是三阶段精读全部完成。方法与代码未完整核读，未运行实验。</p><nav class="jump-links" aria-label="PONI 解析直达"><a href="#analysis-abstract-task">任务</a><a href="#analysis-abstract-insight-one">Insight</a><a href="#analysis-comparison">同文对照</a><a href="#analysis-ablation-core">消融</a><a href="#analysis-limitation">限制</a></nav><div class="template-root" data-template-id="paper-analysis"><p>{esc(byid['paper-analysis-tree']['label'])} · 原模板根节点未填写</p></div>{analysis}<p><a href="#poni-evidence">↑ 返回 PONI 保留 / 替换 / 依据</a> · <a href="#comparison">返回方法比较</a></p></section>
<section id="sources" tabindex="-1"><h2>回到原文与原上下文</h2><ul class="source-list"><li>{cite('obj20','ObjectNav Revisited · 固定 arXiv v2 · 2020-08-30')}</li><li>{cite('semexp2020','SemExp · NeurIPS 2020 正式论文')}</li><li>{psource('PONI · CVPR 2022 正式论文 · pp.18890–18899')}</li><li>{external('https://arxiv.org/html/2312.03275v1','VLFM · 固定 arXiv:2312.03275v1 · 2023-12-06 · 选段核读')}</li></ul><p>中文为来源约束下的概括。来源在新标签页打开，保留当前阅读位置；本页章节用普通链接导航，支持浏览器前进/后退。</p><p><a href="../radar-c2-analysis/index.html">回到原三树入口</a> · <a href="#overview">回到任务总览</a></p></section>
<footer><p>ObjectNav 隔离试读 v1 · 选择性证据 · 不重排其他研究分支</p><p>来源固定与阅读完成是不同状态。VLFM 本页方法证据已补核固定 arXiv v1；选段核读不等于全文精读，亦未改变旧树来源记录。</p></footer></main></body></html>'''

def validate_preview(root,target):
    root=Path(root).absolute();target=safe_target(root,target)
    require(target.relative_to(root).parts[0] not in SOURCE_DIRS, 'Output must not overlap protected source namespace')
    payload,data=payloads(root)
    return root,target,payload,data

def write_preview(root,target):
    root,target,payload,data=validate_preview(root,target)
    dest=safe_path(root,target/ROUTE)
    if dest.exists():
        require(set(p.relative_to(dest).as_posix() for p in dest.rglob('*'))=={'index.html','style.css','reader.js'},'Unexpected exemplar output')
        for p in dest.rglob('*'):
            safe_path(root,p)
            require(stat.S_ISREG(p.stat().st_mode), 'Existing output must contain regular files')
    rendered=render(data,payload).encode()
    dest.mkdir(parents=True,exist_ok=True)
    for name,content in {'index.html':rendered,'style.css':payload['style.css'],'reader.js':payload['reader.js']}.items():
        path=safe_path(root,dest/name); fd,tmp=tempfile.mkstemp(prefix='.objectnav-',dir=dest)
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(content)
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return dest
