const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib'),cp=require('node:child_process'),{JSDOM}=require('jsdom');
const root=path.resolve(__dirname,'..'),M=require('../assets/navigation-product-model.js'),b=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,'data/navigation-product/model.json.gz'))));
const html=cp.execFileSync('python3',['-c',"import sys;from pathlib import Path;sys.path.insert(0,'scripts');import navigation_product as p;r=Path('.').resolve();print(p.render(r,p.payloads(r)[1]))"],{cwd:root,encoding:'utf8',maxBuffer:12e6});
const expected=[
  {
    "scopeId": "task:language-objectnav",
    "paperId": "vlmaps",
    "versionId": "arxiv:2210.05714v2",
    "sourceURL": "https://arxiv.org/html/2210.05714v2",
    "association": "condition",
    "claims": [
      {
        "id": "candidate:vlmaps:arxiv-2210.05714v2:1",
        "statement": "VLM图文匹配与空间建图脱节，难关联多视角对象或定位精细空间目标。",
        "locator": "§I，HTML L53–55",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:vlmaps:arxiv-2210.05714v2:2",
        "statement": "LSeg特征投影到地图；文本检索地标，代码型LLM组合空间primitive与偏移，现成导航栈执行。",
        "locator": "§III-A–D，L82–123",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:vlmaps:arxiv-2210.05714v2:3",
        "statement": "让语义检索与几何目标计算共享空间表示。",
        "locator": "§III-A、D",
        "attribution": "editorial_synthesis"
      }
    ],
    "boundaries": [
      "§III-D明确查询预生成地图；空间偏移primitive不是对象关系图。"
    ],
    "remainingUnverified": [
      "未知环境在线搜索、实例唯一定位与目标验证尚无本轮证据。"
    ]
  },
  {
    "scopeId": "task:language-objectnav",
    "paperId": "conceptgraphs",
    "versionId": "arxiv:2309.16650v1",
    "sourceURL": "https://arxiv.org/html/2309.16650v1",
    "association": "condition",
    "claims": [
      {
        "id": "candidate:conceptgraphs:arxiv-2309.16650v1:1",
        "statement": "密集逐点特征冗余且难分解更新；既有场景图受闭集语义限制。",
        "locator": "§I-A，L68–70",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:conceptgraphs:arxiv-2309.16650v1:2",
        "statement": "跨视角几何/语义融合对象，生成caption与关系；LLM从对象JSON选目标，将pose交下游执行。",
        "locator": "§II-A–C",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:conceptgraphs:arxiv-2309.16650v1:3",
        "statement": "对象化压缩与开放词汇关系查询结合。",
        "locator": "§II-A–C",
        "attribution": "editorial_synthesis"
      }
    ],
    "boundaries": [
      "对象融合增量，但caption在图像序列处理后生成；关系边不等于可走边；caption、漏检、重复检测会错。"
    ],
    "remainingUnverified": [
      "不能据§II-C声称每次LLM检索使用全部关系边；不能外推未知场景探索控制器。"
    ]
  },
  {
    "scopeId": "task:language-objectnav",
    "paperId": "hovsg",
    "versionId": "arxiv:2403.17846v2",
    "sourceURL": "https://arxiv.org/html/2403.17846v2",
    "association": "condition",
    "claims": [
      {
        "id": "candidate:hovsg:arxiv-2403.17846v2:1",
        "statement": "大场景开放词汇表示须兼顾层级抽象、存储效率、可查询性与可执行性。",
        "locator": "§I，L67–70",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:hovsg:arxiv-2403.17846v2:2",
        "statement": "RGB-D/odometry建楼层—房间—对象层级；分解查询逐层相似度检索，以另建跨楼层Voronoi图规划。",
        "locator": "§III-A–C，Fig.5",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:hovsg:arxiv-2403.17846v2:3",
        "statement": "语义层级缩小候选范围，可达图承担路径规划。",
        "locator": "§III-B/C",
        "attribution": "editorial_synthesis"
      }
    ],
    "boundaries": [
      "语义包含边不是通行边；依赖已构建环境记录、几何和位姿。"
    ],
    "remainingUnverified": [
      "不能据此声称零先验ObjectNav覆盖或跨episode持久学习。"
    ]
  },
  {
    "scopeId": "setting:portable-objectnav",
    "paperId": "portable-objectnav-tap",
    "versionId": "arxiv:2403.09905v5",
    "sourceURL": "https://arxiv.org/html/2403.09905v5",
    "association": "direct",
    "claims": [
      {
        "id": "candidate:portable-objectnav-tap:arxiv-2403.09905v5:1",
        "statement": "目标在episode内随agent运动而转移，静态距离奖励可能诱发追逐和高方差；只在episode间换位置不能代表本设定。",
        "locator": "§I/II、§IV、§VI-C",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:portable-objectnav-tap:arxiv-2403.09905v5:2",
        "statement": "DOM保持拓扑边固定，节点对象属性随时间改变。Random任意房间/路径；Semi-Routine固定房间但路径变化；Fully-Routine房间/路径固定。",
        "locator": "§III、Table I、§VI-A",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:portable-objectnav-tap:arxiv-2403.09905v5:3",
        "statement": "离线产生对象路径：选目的节点，经最短路径移动，停留2或3步再选下一节点；用时间—节点字典提供当前物体。",
        "locator": "补充§VIII-A",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:portable-objectnav-tap:arxiv-2403.09905v5:4",
        "statement": "主文称每步给全部物体位置快照、不提供整条未来路径。补充具体为全图每节点唯一目标对象计数列表，加当前位置和时间；动作mask仅允许邻居节点。计数不是语义类别数，也不支持推导显式对象身份轨迹输入。",
        "locator": "§IV；补充§VIII-B",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:portable-objectnav-tap:arxiv-2403.09905v5:5",
        "statement": "以路径相交奖励替代距离奖励并配合发现奖励；补充明确：到达目标最近5步出现过的节点即触发相交奖励。",
        "locator": "§IV；补充§VIII-B",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:portable-objectnav-tap:arxiv-2403.09905v5:6",
        "statement": "把时间、截至当前动作序列、已观测对象放入prompt，超上下文删最早观测。LGX对象检测列表加当前便携物体，LLM选对象后映射到相邻节点。",
        "locator": "§IV；补充§VIII-C",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:portable-objectnav-tap:arxiv-2403.09905v5:7",
        "statement": "§VI-D实验明确跨episode传递时间/动作/检测对象记录；主方法只给有界历史prompt，不能据此断言所有实验采用同一无限持久记忆。",
        "locator": "§VI-D L149–150；§IV、§VIII-C",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:portable-objectnav-tap:arxiv-2403.09905v5:8",
        "statement": "利用目标转移的时间规律安排相遇，而不只追当前最近位置。",
        "locator": "§IV",
        "attribution": "editorial_synthesis"
      }
    ],
    "boundaries": [
      "DOM是环境生成表示，TAP是方法；不要将两者混为一个记忆模块。",
      "TAP-RL主设置使用全图目标计数快照，不是纯局部视觉部分可观测导航。§VI-C局部相邻节点计数消融显著下降，需保留观察特权。",
      "主文的路径相交公式未显式保留时间；补充最近5步实现更具体，不可把该奖励直接写成同一时刻发现目标。",
      "§VI-D lab实验从采集图像建立图，再DOM化并随机采样已采观点；不能仅凭real-world措辞称作持续实机闭环家庭试验。",
      "SR按发现物体数/最优策略可发现数，不是常规单目标二元成功率。",
      "v5内容不能覆盖v1身份/指标；本轮未重新打开v1，不新增v1题名结论。"
    ],
    "remainingUnverified": [
      "训练/推理时观察一致性及奖励实际代码待核。",
      "LLM跨episode历史清空策略、horizon数值和不同实验一致性待核。",
      "真实运动控制与在线检测范围需视频/代码再核，不在本轮。"
    ]
  },
  {
    "scopeId": "task:multistage-language-navigation",
    "paperId": "lhvln-mgdm",
    "versionId": "publication:cvpr2025:lhvln",
    "sourceURL": "https://openaccess.thecvf.com/content/CVPR2025/papers/Song_Towards_Long-Horizon_Vision-Language_Navigation_Platform_Benchmark_and_Method_CVPR_2025_paper.pdf",
    "association": "direct",
    "claims": [
      {
        "id": "candidate:lhvln-mgdm:publication-cvpr2025-lhvln:1",
        "statement": "长链子任务需要持续理解与衔接；历史累积过多，而简单删除旧观测又可能丢关键内容。",
        "locator": "§1，§4.2，pp.12079、12083",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:lhvln-mgdm:publication-cvpr2025-lhvln:2",
        "statement": "ViT多方向视觉经Transformer融合，加入方向与历史步骤嵌入，由LLM选动作。",
        "locator": "§4.1，Eq.5–7",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:lhvln-mgdm:publication-cvpr2025-lhvln:3",
        "statement": "子任务开始及导航期间定期用当前观测、历史和指令生成反馈提示。",
        "locator": "§4.2 CoT Feedback",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:lhvln-mgdm:publication-cvpr2025-lhvln:4",
        "statement": "历史达到上限后，比较置信度序列不同局部池化的熵，选最小者；对应池化历史编码，再添新观测。",
        "locator": "§4.2，Eq.8–11",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:lhvln-mgdm:publication-cvpr2025-lhvln:5",
        "statement": "按目标从LHPR-VLN数据集取观察–动作对，匹配当前观测选top-k，以检索动作均值加权当前决策。",
        "locator": "§4.2，Eq.12–14",
        "attribution": "author_statement_paraphrased"
      },
      {
        "id": "candidate:lhvln-mgdm:publication-cvpr2025-lhvln:6",
        "statement": "保留任务内历史并压缩，再用数据集检索辅助当前决策。",
        "locator": "Fig.4/§4.2",
        "attribution": "editorial_synthesis"
      }
    ],
    "boundaries": [
      "长期记忆的原文来源是数据集；不能等同跨独立任务积累的自身经历。",
      "任务内跨子阶段记忆有论述，但未核跨episode保存/清空规则。",
      "Table 2所有方法整链SR为0，不能称MGDM解决长链成功；正文只支持相对改善与局部指标。"
    ],
    "remainingUnverified": [
      "补充的动作/成功阈值和记忆上限N、top-k值未核。",
      "池化公式的索引与长度表述需代码确认，不能据排版自行修正。",
      "长期记忆数据划分与是否跨独立任务更新未由已读范围证实。"
    ]
  }
];
async function boot(){const d=new JSDOM(html,{url:'https://example.org/RoboPaperAtlas/research/navigation/',runScripts:'outside-only',pretendToBeVisual:true}),w=d.window;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=function(){};w.NAVIGATION_PRODUCT=b;for(const n of ['navigation-product-model.js','navigation-product.js'])w.eval(fs.readFileSync(path.join(root,'assets',n),'utf8'));await new Promise(r=>setTimeout(r,40));assert.ok(w.NavigationProductApp);return d;}
test('fixed evidence inventory remains scoped and source-bound',()=>{assert.equal(b.schemaVersion,'navigation-product/1');assert.equal(Object.keys(b.claims).length,436);assert.equal(Object.keys(b.versions).length,274);assert.equal(Object.keys(b.papers).length,89);assert.equal(Object.keys(b.positions).length,1641);assert.equal(expected.flatMap(p=>p.claims).length,23);for(const p of expected){const version=b.versions[p.versionId];assert.equal(version.paperId,p.paperId);assert.equal(version.url,p.sourceURL);assert.equal(Object.values(b.versions).filter(v=>v.url===p.sourceURL).length,1);assert.equal(version.analysisStatus,'not_imported');assert.equal(b.analyses[p.paperId],undefined);for(const c of p.claims){const claim=b.claims[c.id];assert.equal(claim.paperId,p.paperId);assert.equal(claim.versionId,p.versionId);for(const field of ['statement','locator','attribution'])assert.equal(claim[field],c[field]);assert.ok(b.papers[p.paperId].claimIds.includes(c.id));}}});
test('former unbound versions resolve once while ambiguous Portable abstract stays unpinned',()=>{for(const [old,canonical] of [['source:source:7c58a92a9fe9','arxiv:2403.09905v5'],['publication:unbound:2627c434a35b','publication:cvpr2025:lhvln']]){assert.equal(b.versions[old],undefined);assert.equal(b.versionAliases[old],canonical);assert.ok(b.versions[canonical]);}const v=b.versions['source:source:1f0f45a22f61'];assert.equal(v.paperId,null);assert.equal(v.url,'https://arxiv.org/abs/2403.09905');assert.equal(v.versionStatus,'snapshot_not_version_pinned');assert.equal(b.versionAliases[v.id],undefined);});
test('condition evidence does not fill direct language methods or paper analyses',()=>{const c=b.coverage['task:language-objectnav'];assert.equal(c.direct.methodCount,0);assert.equal(c.direct.challengeCount,0);assert.equal(c.condition.methodCount,4);assert.equal(c.condition.challengeCount,3);assert.equal(c.context.challengeCount,13);assert.equal(b.summary.methodGapScopes,14);assert.equal(b.summary.ciGapScopes,16);assert.equal(b.summary.answeredAnalysisContexts,3);assert.equal(b.template.nodeCount,59);assert.equal(b.template.leafCount,40);for(const p of expected)assert.equal(b.coverage[p.scopeId].analysisCount,0);});
for(const p of expected)test('fixed-version card and 59-node unread reference: '+p.paperId,async t=>{const d=await boot();t.after(()=>d.window.close());const w=d.window;for(const c of p.claims){const pos=Object.values(b.positions).find(n=>n.scopeId===p.scopeId&&n.paperId===p.paperId&&n.versionId===p.versionId&&n.claimIds.includes(c.id));assert.ok(pos,c.id);assert.equal(pos.association,p.association);const route=M.routeForPosition(b,{scope:p.scopeId},pos.id,{claim:c.id});w.NavigationProductApp.navigate(route);const txt=w.document.querySelector('#np-detail-content').textContent;for(const text of [c.statement,c.locator,c.attribution,...p.boundaries,...p.remainingUnverified])assert.ok(txt.includes(text),text);for(const overrides of [{paper:'poni'},{version:'arxiv:0000.00000v1'},{scope:'task:pointnav'},{claim:'claim:t:eval18:goals'}])assert.throws(()=>M.validateRoute(b,{...route,...overrides}));}w.NavigationProductApp.navigate({scope:p.scopeId,tree:'a',paper:p.paperId,version:p.versionId,template:'1',node:b.template.roots[0]});assert.equal(w.NavigationProductApp.getState().route.version,p.versionId);assert.match(w.document.querySelector('#np-detail-content').textContent,/未填/);assert.ok([...w.document.querySelectorAll('#np-tree [data-position]')].every(n=>b.positions[n.dataset.position].genericTemplate));});

test('every historical exact node route remains valid in the new evidence model',()=>{const old=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,'tests/fixtures/navigation-product-20261008.json.gz'))));for(const p of Object.values(old.positions)){const base={scope:p.scopeId||'scope:all',tree:p.tree};if(p.genericTemplate)base.template='1';const route=M.routeForPosition(old,base,p.id);assert.doesNotThrow(()=>M.validateRoute(b,route),p.id);}assert.equal(Object.keys(old.positions).length,1557);});
for(const [type,label] of [['selected_fixed_version_condition','已核固定版本·条件关联'],['selected_fixed_version_task','已核固定版本·任务关联']])test('fixed-version relation uses readable Chinese without changing its scientific association: '+type,async t=>{const positions=Object.values(b.positions).filter(p=>p.relationType===type);assert.ok(positions.length);const d=await boot();t.after(()=>d.window.close());const w=d.window;for(const p of positions){w.NavigationProductApp.navigate(M.routeForPosition(b,{scope:p.scopeId},p.id));const node=w.document.getElementById('np-node-'+p.id),edge=[...node.children].find(n=>n.classList.contains('np-edge-label'));assert.ok(edge);assert.equal(edge.dataset.relationType,type);assert.ok(edge.textContent.startsWith(label));assert.doesNotMatch(edge.textContent,/selected[_ ]fixed[_ ]version/);if(p.scopeId==='task:language-objectnav')assert.equal(p.association,'condition');}assert.equal(b.coverage['task:language-objectnav'].direct.methodCount,0);assert.equal(b.coverage['task:language-objectnav'].direct.challengeCount,0);});
