window.RADAR_GRAPH_DATA = {
  "schema": "radar-c-view/1",
  "title": "RoboPaperAtlas Radar",
  "public_only": true,
  "checked_at": "2026-10-05",
  "graph_revision": 2,
  "edge_semantics": "curator_organization",
  "academic_edges": [],
  "tasks": [
    {
      "id": "task-vln",
      "label": "VLN",
      "subtitle": "视觉语言指令导航",
      "full_label": "视觉语言指令导航"
    },
    {
      "id": "task-objectnav",
      "label": "ObjectNav",
      "subtitle": "物体与多模态目标",
      "full_label": "物体目标与多模态目标导航"
    },
    {
      "id": "task-continual",
      "label": "持续导航",
      "subtitle": "跨任务经验与记忆",
      "full_label": "跨任务经验与持续导航"
    }
  ],
  "routes": [
    {
      "id": "route-runtime",
      "label": "运行与反馈闭环",
      "subtitle": "提案 · 执行 · 恢复 · 停止",
      "full_label": "提案 / 工具接口 → 几何执行 → 状态反馈 → 恢复与停止"
    },
    {
      "id": "route-spatial-memory",
      "label": "空间与实例记忆",
      "subtitle": "观察 · 检索 · 跨任务更新",
      "full_label": "观测 → 空间 / 实例记忆 → 按目标检索 → 跨任务更新"
    },
    {
      "id": "route-context",
      "label": "上下文分配",
      "subtitle": "选择 · 压缩 · token预算",
      "full_label": "历史观测 → 选择 / 压缩 / token分配 → 当前决策"
    },
    {
      "id": "route-learned-policy",
      "label": "学习策略",
      "subtitle": "表征 · 动作或轨迹",
      "full_label": "视觉语言表征 → 学习策略 → 低层动作或轨迹"
    },
    {
      "id": "route-protocol",
      "label": "任务与评测协议",
      "subtitle": "观测 · 动作 · 成功契约",
      "full_label": "任务与本体 → 观察 / 动作契约 → 成功与效率评价"
    }
  ],
  "task_routes": [
    {
      "source": "task-vln",
      "target": "route-runtime",
      "attribution": "curator_organization"
    },
    {
      "source": "task-objectnav",
      "target": "route-runtime",
      "attribution": "curator_organization"
    },
    {
      "source": "task-continual",
      "target": "route-runtime",
      "attribution": "curator_organization"
    },
    {
      "source": "task-vln",
      "target": "route-spatial-memory",
      "attribution": "curator_organization"
    },
    {
      "source": "task-objectnav",
      "target": "route-spatial-memory",
      "attribution": "curator_organization"
    },
    {
      "source": "task-continual",
      "target": "route-spatial-memory",
      "attribution": "curator_organization"
    },
    {
      "source": "task-vln",
      "target": "route-context",
      "attribution": "curator_organization"
    },
    {
      "source": "task-objectnav",
      "target": "route-context",
      "attribution": "curator_organization"
    },
    {
      "source": "task-vln",
      "target": "route-learned-policy",
      "attribution": "curator_organization"
    },
    {
      "source": "task-objectnav",
      "target": "route-learned-policy",
      "attribution": "curator_organization"
    },
    {
      "source": "task-vln",
      "target": "route-protocol",
      "attribution": "curator_organization"
    },
    {
      "source": "task-objectnav",
      "target": "route-protocol",
      "attribution": "curator_organization"
    },
    {
      "source": "task-continual",
      "target": "route-protocol",
      "attribution": "curator_organization"
    }
  ],
  "groups": [
    {
      "id": "evidence-and-action",
      "label": "证据与行动",
      "subtitle": "执行 · 反馈 · 成功判定",
      "attribution": "curator_organization",
      "note": "编辑归组，不是论文作者共同提出的研究分类；分组不建立论文之间的学术关系。",
      "paper_ids": [
        "harnessvln",
        "holoagent-0",
        "krantz2020vlnce",
        "batra2020objectnav"
      ]
    },
    {
      "id": "memory-validity",
      "label": "记忆的有效性",
      "subtitle": "保留 · 检索 · 修订",
      "attribution": "curator_organization",
      "note": "编辑归组，不是论文作者共同提出的研究分类；分组不建立论文之间的学术关系。",
      "paper_ids": [
        "navharness",
        "krantz2023ivln",
        "goat",
        "goat-bench"
      ]
    },
    {
      "id": "context-allocation",
      "label": "上下文分配",
      "subtitle": "历史 · 信息 · 预算",
      "attribution": "curator_organization",
      "note": "编辑归组，不是论文作者共同提出的研究分类；分组不建立论文之间的学术关系。",
      "paper_ids": [
        "qwen-robotnav",
        "agenticnav-tool-harness"
      ]
    },
    {
      "id": "prediction-interface",
      "label": "空间预测的接口",
      "subtitle": "本期编辑归组 · 训练用途",
      "attribution": "curator_organization",
      "note": "编辑归组，不是论文作者共同提出的研究分类；分组不建立论文之间的学术关系。",
      "paper_ids": []
    }
  ],
  "papers": [
    {
      "paper_id": "harnessvln",
      "short_name": "HarnessVLN",
      "version": "arXiv 2609.15195v3",
      "source_url": "https://arxiv.org/html/2609.15195v3",
      "read_scope": "section",
      "read_locations": [
        "§3.1–3.3",
        "§4.1–4.4 and Tables 2–4",
        "Appendix 1.1–1.2",
        "§2 and selected References"
      ],
      "not_read": [
        "未逐图视觉核验",
        "未核全部补充内容",
        "代码未读/未运行"
      ],
      "task": "指令导航与物体目标导航",
      "pipeline": "规划提案 → 来源/几何/进度检查 → 工具执行 → 状态更新",
      "representation": "事件记忆 + 带观测来源的时空图",
      "module": "检索、执行反馈、停止验证",
      "challenge": "看见目标、提出动作和真正完成子目标并不等价",
      "insight": "把证据、进度与执行结果统一管理，而非仅增强语义规划",
      "evidence": [
        {
          "kind": "method",
          "locator": "§3.1.2, §3.2, §3.3",
          "statement": "派发前检查观测来源、几何及子目标；停止请求另验语义、几何和进度。",
          "attribution": "author_claim"
        },
        {
          "kind": "protocol",
          "locator": "§4.4, Table 4",
          "statement": "固定100-episode子集上的memory→graph→stop累加消融，估计已有组件条件下增量，不是完整析因。",
          "attribution": "direct_observation"
        },
        {
          "kind": "relation",
          "locator": "§4.2, Appendix 1.2; Reference Cai et al. (2026)",
          "statement": "明确把NavDP作为楼梯执行工具；采用范围不扩成整套方法继承。",
          "attribution": "author_claim"
        }
      ],
      "open_question": "同一模型与预算下，停止验证改善了成功率还是仅改变拒停及额外观察次数？",
      "limits": "跨论文结果受backbone和子集影响；未独立复现实验。",
      "tasks": [
        "task-vln",
        "task-objectnav"
      ],
      "routes": [
        "route-runtime",
        "route-spatial-memory"
      ],
      "title": "HarnessVLN: Unifying Training-Free Embodied Navigation through an Agent Harness",
      "year": 2026,
      "canonical_id": "harnessvln",
      "groups": [
        "evidence-and-action"
      ],
      "mode": "baseline",
      "insight_attribution": "curator_summary",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "navharness",
      "short_name": "NavHarness",
      "version": "arXiv 2609.34276v1",
      "source_url": "https://arxiv.org/html/2609.34276v1",
      "read_scope": "section",
      "read_locations": [
        "§2–3.5",
        "§4.1",
        "Appendix B.3, C.1",
        "Appendix D.4, E.1–E.9"
      ],
      "not_read": [
        "未逐图核验",
        "未完整审查全部案例",
        "代码未读/未运行"
      ],
      "task": "连续目标与恢复会话中的经验利用",
      "pipeline": "新会话读取记录 → 搜索/修正 → 检验结果 → 交接/跨run整理",
      "representation": "地图、任务记录与长期房屋知识分层保留",
      "module": "恢复交接、结果核验、经验整理",
      "challenge": "旧搜索记录可能不完整或与新观测冲突",
      "insight": "传递可追溯搜索证据，而非让旧判断自动成为事实",
      "evidence": [
        {
          "kind": "method",
          "locator": "§3.3–3.5",
          "statement": "恢复保留剩余任务预算；交接区分已搜索和有证据排除，原任务记录不可由后续会话覆盖。",
          "attribution": "author_claim"
        },
        {
          "kind": "protocol",
          "locator": "Appendix C.1, Table 3 A–D",
          "statement": "独立会话是整套策略对比，不是memory-only消融；组件干预分别从full出发。",
          "attribution": "direct_observation"
        },
        {
          "kind": "limitation",
          "locator": "Appendix E.3–E.6, E.9",
          "statement": "评测为静态模拟环境；旧占据格不随SLAM回环校正更新，judge也会误判。",
          "attribution": "author_claim"
        }
      ],
      "open_question": "在相同预算下加入可控环境变化，证据修订是否优于等长普通总结？",
      "limits": "有限静态序列不证明真实终身运行或动态环境适应。",
      "tasks": [
        "task-continual"
      ],
      "routes": [
        "route-runtime",
        "route-spatial-memory"
      ],
      "title": "NavHarness: Towards Lifelong Embodied Navigation",
      "year": 2026,
      "canonical_id": "navharness",
      "groups": [
        "memory-validity"
      ],
      "mode": "baseline",
      "insight_attribution": "curator_summary",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "agenticnav-tool-harness",
      "short_name": "AgenticNav",
      "version": "arXiv 2606.10577v3 (2026-10-02)",
      "source_url": "https://arxiv.org/html/2606.10577v3",
      "read_scope": "section",
      "read_locations": [
        "§II–III-D",
        "§IV-A and Tables I–III",
        "§V excerpt"
      ],
      "not_read": [
        "未完整核真实机器人实验",
        "未逐图核验",
        "代码未读/未运行"
      ],
      "task": "episode内免训练VLN-CE",
      "pipeline": "RGB目标像素 → 按需深度 → 几何检查 → 执行/选择性回看",
      "representation": "六步理由记录、BEV图和可查询历史图像",
      "module": "query_depth、move_to、recall",
      "challenge": "固定waypoint候选限制动作，堆历史使上下文冗余",
      "insight": "让模型按需索取数值/视觉证据，几何计算留在工具",
      "evidence": [
        {
          "kind": "method",
          "locator": "§III-C–D",
          "statement": "像素反投影后检查障碍；记忆限当前episode，每步重建有界上下文。",
          "attribution": "author_claim"
        },
        {
          "kind": "protocol",
          "locator": "§IV-A, Tables I–III",
          "statement": "100条R2R-CE子集；76%对应Gemini-3.7-Flash，GPT-5.5为55%，不能把差值当版本进步。",
          "attribution": "direct_observation"
        },
        {
          "kind": "limitation",
          "locator": "§IV-A Memory and Context Management",
          "statement": "作者将进度文本较差表现解释为错误判断延续；该解释不等于独立因果证实。",
          "attribution": "author_claim"
        }
      ],
      "open_question": "等token和工具调用预算下，理由历史、进度记录与证据索引哪种更抗错误传播？",
      "limits": "早期v1也曾查看，但本核心以v3为准；未做完整版本diff。",
      "tasks": [
        "task-vln"
      ],
      "routes": [
        "route-runtime",
        "route-context"
      ],
      "title": "AgenticNav: Zero-Shot Vision-and-Language Navigation as a Tool-Calling Harness",
      "year": 2026,
      "canonical_id": "agenticnav-tool-harness",
      "groups": [
        "context-allocation"
      ],
      "mode": "baseline",
      "insight_attribution": "curator_summary",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "qwen-robotnav",
      "short_name": "Qwen-RobotNav",
      "version": "arXiv 2606.18112v3",
      "source_url": "https://arxiv.org/html/2606.18112v3",
      "read_scope": "section",
      "read_locations": [
        "§2.1–2.2, Algorithm 1",
        "§5.5, Fig.15 caption and associated text"
      ],
      "not_read": [
        "未完整审训练数据",
        "未读取图像像素或全部曲线",
        "代码未读/未运行"
      ],
      "task": "可被上层agent配置的多任务导航策略",
      "pipeline": "分配视觉token → 编码历史/视角 → 预测waypoint轨迹",
      "representation": "任务参数化的历史视觉上下文",
      "module": "token预算、时间衰减、相机权重、采样模式",
      "challenge": "不同任务对历史长度和近期细节的需求不同",
      "insight": "把上下文策略做成推理时可调接口",
      "evidence": [
        {
          "kind": "method",
          "locator": "§2.2, Algorithm 1",
          "statement": "按时间与相机权重分配有上下限的视觉token；作者明确称其启发式。",
          "attribution": "author_claim"
        },
        {
          "kind": "protocol",
          "locator": "§5.5, Fig.15 text",
          "statement": "4B模型在500条R2R验证轨迹上扫描预算与衰减；收益不是严格单调。",
          "attribution": "direct_observation"
        }
      ],
      "open_question": "固定总预算时，按当前不确定性分配上下文是否优于固定时间衰减？",
      "limits": "此处读的是正文与图注文本，不声称独立量取曲线。",
      "tasks": [
        "task-vln",
        "task-objectnav"
      ],
      "routes": [
        "route-context",
        "route-learned-policy"
      ],
      "title": "Qwen-RobotNav Technical Report: A Scalable Navigation Model Designed for an Agentic Navigation System",
      "year": 2026,
      "canonical_id": "qwen-robotnav",
      "groups": [
        "context-allocation"
      ],
      "mode": "baseline",
      "insight_attribution": "curator_summary",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "holoagent-0",
      "short_name": "HoloAgent-0",
      "version": "arXiv 2606.23565v1",
      "source_url": "https://arxiv.org/html/2606.23565v1",
      "read_scope": "section",
      "read_locations": [
        "§2–3.1",
        "§4.5",
        "§5.1–5.2"
      ],
      "not_read": [
        "未完整核空间建图指标",
        "未观看视频",
        "代码未读/未运行"
      ],
      "task": "异构技能的闭环机器人任务执行",
      "pipeline": "检索空间状态 → 技能图调度 → 状态反馈 → 监控/重规划",
      "representation": "空间记忆与任务执行轨迹",
      "module": "typed技能接口、ROS2状态总线、事件更新",
      "challenge": "物理技能会部分失败，反馈不完整且有延迟",
      "insight": "动作接口同时承载预期效果、进度和可恢复性",
      "evidence": [
        {
          "kind": "method",
          "locator": "§2.2–3.1, §4.5",
          "statement": "技能返回结构化状态；新观测、物体操作结果或用户纠正触发局部记忆更新。",
          "attribution": "author_claim"
        },
        {
          "kind": "protocol",
          "locator": "§5.1–5.2",
          "statement": "定量导航/建图与全系统定性演示分开；没有统一端到端全技能成功率。",
          "attribution": "direct_observation"
        }
      ],
      "open_question": "固定导航后端时，结构化失败反馈是否比仅success/failure更能减少错误恢复？",
      "limits": "异构技能展示不直接证明持续导航或全部机器人能力稳定有效。",
      "tasks": [
        "task-objectnav",
        "task-continual"
      ],
      "routes": [
        "route-runtime",
        "route-spatial-memory"
      ],
      "title": "HoloAgent-0: A Unified Embodied Agent Framework with 3D Spatial Memory",
      "year": 2026,
      "canonical_id": "holoagent-0",
      "groups": [
        "evidence-and-action"
      ],
      "mode": "baseline",
      "insight_attribution": "curator_summary",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "krantz2023ivln",
      "short_name": "IVLN",
      "version": "arXiv v3, 2023-12-24",
      "source_url": "https://arxiv.org/html/2210.03087v3",
      "read_scope": "section",
      "read_locations": [
        "摘要；§1–2相关段；§3 tour/数据/指标；§4.1 TourHAMT段与§4.2；§5表2–4及分析；§6限制与未来工作"
      ],
      "not_read": [
        "附录A–C未系统读；无代码审计、数据下载或实验复现；图主要读取图注，未做逐像素图形核验"
      ],
      "task": "同场景多指令 tour；IR2R 为图导航，IR2R-CE 为连续导航",
      "pipeline": "RGB-D→占据/13类语义地图→自中心裁剪→CNN→CMA动作；另测跨episode隐状态/历史",
      "representation": "显式语义栅格记忆；隐状态/历史扩展对照",
      "module": "显式语义栅格记忆；隐状态/历史扩展对照",
      "challenge": "跨任务经验保留；长程指标与oracle隔离",
      "insight": "把“记忆保留周期”和“oracle观察来源”拆成独立开关；用同一已训练模型切换记忆，比跨模型总分更能定位记忆贡献",
      "evidence": [
        {
          "kind": "protocol",
          "locator": "§3 The Iterative Paradigm, HTML L100–102",
          "statement": "每episode后 oracle纠偏并带至下一起点；agent沿途被动观察",
          "attribution": "direct_observation"
        },
        {
          "kind": "protocol",
          "locator": "§4.2.2, L184–193; Table 4",
          "statement": "地图分别按episode、tour重置或预先给定；训练与评测模式交叉比较",
          "attribution": "direct_observation"
        },
        {
          "kind": "limitation",
          "locator": "§5.2, L259–267",
          "statement": "map对CMA的优势混有DAgger训练差异；known map也未胜iterative map",
          "attribution": "author_claim"
        }
      ],
      "open_question": "同训练预算、同DAgger配置下，结构记忆优势还剩多少？；禁用纠偏阶段的被动观察后，后续收益是否保留？",
      "limits": "不能从这些基线的负结果推出所有Transformer长期记忆都无效；不能把tour等同无oracle长期自主部署 ",
      "tasks": [
        "task-vln",
        "task-continual"
      ],
      "routes": [
        "route-spatial-memory",
        "route-protocol"
      ],
      "insight_attribution": "curator_inference",
      "title": "Iterative Vision-and-Language Navigation",
      "year": 2023,
      "canonical_id": "krantz2023ivln",
      "groups": [
        "memory-validity"
      ],
      "mode": "baseline",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "goat",
      "short_name": "GOAT",
      "version": "arXiv v1, 2023-11-10",
      "source_url": "https://arxiv.org/html/2311.06430v1",
      "read_scope": "section",
      "read_locations": [
        "§1相关段；§2.1–2.2任务/主实验及表1、图3图注；§2.3社会导航段；§3讨论目标匹配与检测局限；§4.1–4.2方法/协议；§5.1首段与匹配表局部"
      ],
      "not_read": [
        "未系统阅读全文参考文献；未观看视频；未审计代码；补充表未逐格验证；未逐页核对RSS版与v1差异"
      ],
      "task": "同屋依次寻找5–10个类别、图像或语言目标",
      "pipeline": "RGB-D/pose→实例分割与语义图+多视角实例记忆→CLIP/SuperGlue匹配或frontier→FMM/本体控制器",
      "representation": "实例视图记忆；语义地图+局部规划",
      "module": "实例视图记忆；语义地图+局部规划",
      "challenge": "同类实例消歧；记忆收益与探索阶段耦合；本体执行差异",
      "insight": "把“记住了目标位置”与“探索后匹配策略变了”拆开测；同时记录感知、检索、规划、执行四级失败，避免把总SR归因给单一记忆模块",
      "evidence": [
        {
          "kind": "protocol",
          "locator": "§4.1 Global/Local Policy, L200–208",
          "statement": "探索时阈值匹配，探索后取最高分；Spot与Stretch采用不同低层执行",
          "attribution": "direct_observation"
        },
        {
          "kind": "protocol",
          "locator": "§4.2, L210–219; Table 1",
          "statement": "定量主测Spot：9宅、15类；每目标200步、STOP且距离\u003c1m",
          "attribution": "direct_observation"
        },
        {
          "kind": "limitation",
          "locator": "§3 Matching Performance During Exploration, L155–157; §4.1 L177",
          "statement": "固定匹配阈值有误报/漏报；实测选MaskRCNN而非较不稳的Detic",
          "attribution": "author_claim"
        }
      ],
      "open_question": "冻结goal matcher后，记忆还能带来多少效率提升？；移位对象、同类相邻对象会造成错误实例合并吗？",
      "limits": "不能把15类实机评测解释为任意开放词汇实证；也不能把小规模动态人实验解释为普遍动态场景稳健性 v1 §4.1 与§5.1出现不同匹配阈值；本次不把任一组当成可复现默认值，需对照发布代码/最终版",
      "tasks": [
        "task-objectnav",
        "task-continual"
      ],
      "routes": [
        "route-spatial-memory",
        "route-runtime"
      ],
      "insight_attribution": "curator_inference",
      "title": "GOAT: GO to Any Thing",
      "year": 2024,
      "canonical_id": "goat",
      "groups": [
        "memory-validity"
      ],
      "mode": "baseline",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "goat-bench",
      "short_name": "GOAT-Bench",
      "version": "arXiv v1, 2024-04-09",
      "source_url": "https://arxiv.org/html/2404.06609v1",
      "read_scope": "section",
      "read_locations": [
        "摘要；§1–2；§3；§4数据/生成流程与split相关段；§5；§6表2；§7.1–7.4；§8；附录C只零散段"
      ],
      "not_read": [
        "附录A–D未系统全读；图4–7主要核图注与正文结果而非逐像素读图；无训练复现或代码核验"
      ],
      "task": "开放词汇5–10子目标；类别/描述/实例图像",
      "pipeline": "比较modular实例地图、按模态skill chain、跨子任务GRU隐状态monolithic",
      "representation": "模块化显式地图；神经隐式记忆；分模态skill routing",
      "module": "模块化显式地图；神经隐式记忆；分模态skill routing",
      "challenge": "可复现长期多模态协议；记忆利用因果诊断；目标输入鲁棒性",
      "insight": "至少联合报告SR/SPL、目标模态、子任务序号和是否先前见过目标；单个总分会把识别能力与路线复用混在一起",
      "evidence": [
        {
          "kind": "protocol",
          "locator": "§3, L99–105; §4 Evaluation Splits, L134–145",
          "statement": "Stretch/Habitat，RGB-D+GPS/Compass；500动作/子目标，1m+STOP；三split环境均未见",
          "attribution": "direct_observation"
        },
        {
          "kind": "protocol",
          "locator": "§6, L168–169",
          "statement": "SPL最短路从上一子任务实际结束位置算，不从理想前一目标算",
          "attribution": "direct_observation"
        },
        {
          "kind": "protocol",
          "locator": "§7.2/Fig.5, L196–201",
          "statement": "逐子任务清空：GOAT SPL17.6→9.4；monolithic 9.4→9.0",
          "attribution": "direct_observation"
        }
      ],
      "open_question": "清空、打乱、过期记忆分别影响什么失败环节？；固定视觉与goal encoder后，显式/隐式记忆差异是否仍在？",
      "limits": "RNN基线失败不等于长期上下文路线被否定；goal扰动不等于机器人视觉观测或位姿噪声鲁棒性 ",
      "tasks": [
        "task-objectnav",
        "task-continual"
      ],
      "routes": [
        "route-protocol",
        "route-spatial-memory"
      ],
      "insight_attribution": "curator_inference",
      "title": "GOAT-Bench: A Benchmark for Multi-Modal Lifelong Navigation",
      "year": 2024,
      "canonical_id": "goat-bench",
      "groups": [
        "memory-validity"
      ],
      "mode": "baseline",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "krantz2020vlnce",
      "short_name": "VLN-CE",
      "version": "arXiv v2, 2020-05-01",
      "source_url": "https://arxiv.org/html/2004.02857v2",
      "read_scope": "section",
      "read_locations": [
        "摘要；§1–3；§4.1–4.2公式与架构；§4.3部分训练段；§5.1–5.3表2–4与失败/caveats；§6首段"
      ],
      "not_read": [
        "§6余段及§6.1补充转换算法未系统读；未做视觉图形细节核验、代码审计或实验复现"
      ],
      "task": "R2R指令转入Matterport3D/Habitat连续空间",
      "pipeline": "RGB/深度ResNet特征+语言编码→Seq2Seq或双GRU跨模态注意力→低层动作",
      "representation": "端到端低层动作；跨模态注意力基线",
      "module": "端到端低层动作；跨模态注意力基线",
      "challenge": "上层决策与真实执行接口；观测覆盖；评测环境先验",
      "insight": "比较两个planner前先固定它们究竟得到哪种拓扑、定位与低层控制帮助；否则harness差异本身就可能解释成绩",
      "evidence": [
        {
          "kind": "protocol",
          "locator": "§1, L56–73; §3, L115–117",
          "statement": "不供位置/朝向；前进0.25m、转15°、STOP；无图拓扑及短程oracle",
          "attribution": "direct_observation"
        },
        {
          "kind": "protocol",
          "locator": "§4.2, Eq.(4–8), L163–179",
          "statement": "视觉GRU供语言注意力，再对RGB/深度注意；第二GRU输出动作",
          "attribution": "direct_observation"
        },
        {
          "kind": "limitation",
          "locator": "§5.2 qualitative L235–236; §5.3 Caveats L243–244",
          "statement": "窄视野可能漏见指令对象；映射回nav-graph的比较受轨迹排除和转换误差影响",
          "attribution": "author_claim"
        }
      ],
      "open_question": "同一高层轨迹经真实可失败控制器执行后，损失出现在哪一层？；增加观测覆盖与增加语言推理能力，哪个更能修复失败？",
      "limits": "continuous指连续可导航空间，不代表动作是连续值；不能把连续版/图版原始SPL直接当作公平同条件排名 ",
      "tasks": [
        "task-vln"
      ],
      "routes": [
        "route-protocol",
        "route-learned-policy"
      ],
      "insight_attribution": "curator_inference",
      "title": "Beyond the Nav-Graph: Vision-and-Language Navigation in Continuous Environments",
      "year": 2020,
      "canonical_id": "krantz2020vlnce",
      "groups": [
        "evidence-and-action"
      ],
      "mode": "baseline",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    },
    {
      "paper_id": "batra2020objectnav",
      "short_name": "ObjectNav Revisited",
      "version": "arXiv v2, 2020-08-30",
      "source_url": "https://arxiv.org/html/2006.13171v2",
      "read_scope": "section",
      "read_locations": [
        "摘要；§1–2.3；§2.1.1全部列出的SPL问题；§3 Habitat场景/目标/valid-viewpoint相关段"
      ],
      "not_read": [
        "§3余下挑战流程、§4 RoboTHOR、结论与参考文献未系统读；未检查挑战代码或现行规则"
      ],
      "task": "未知环境寻找指定类别的任一实例",
      "pipeline": "规范输入/本体→可达成功区域→STOP判定→SR与路径效率；没有新policy表示",
      "representation": "评测契约基础",
      "module": "评测契约基础",
      "challenge": "成功判定与目标语义；效率指标盲区",
      "insight": "让harness显式记录STOP、目标ID/类别、几何距离、可见性判定与动作成本；用失败原因与部分进展补足二元成功",
      "evidence": [
        {
          "kind": "protocol",
          "locator": "§2.1, L76–92",
          "statement": "成功拆成STOP意图、位置合法、表面距离、可见性；允许oracle-visibility变体",
          "attribution": "direct_observation"
        },
        {
          "kind": "limitation",
          "locator": "§2.1.1, L106–121",
          "statement": "SPL不分近失误/彻底失败，不罚原地转动；不可跨不同路径分布直接比较",
          "attribution": "author_claim"
        },
        {
          "kind": "protocol",
          "locator": "§3, L151–153",
          "statement": "Habitat实例化预计算1m内、可导航且oracle可见的valid viewpoints",
          "attribution": "direct_observation"
        }
      ],
      "open_question": "到对位置却朝向错误，算导航失败还是终端视觉确认失败？；多实例任务的参考最短路是否与目标语义一致？",
      "limits": "不能把所有ObjectNav实现都说成采用同一1m/visibility细则；这里也没有证明某种新指标更优 ",
      "tasks": [
        "task-objectnav"
      ],
      "routes": [
        "route-protocol"
      ],
      "insight_attribution": "curator_inference",
      "title": "ObjectNav Revisited: On Evaluation of Embodied Agents Navigating to Objects",
      "year": 2020,
      "canonical_id": "batra2020objectnav",
      "groups": [
        "evidence-and-action"
      ],
      "mode": "baseline",
      "challenge_attribution": "curator_summary",
      "conditions": [
        "版本与实际读到的范围以来源记录为准。"
      ]
    }
  ],
  "candidates": [
    {
      "versioned_id": "2609.37353v1",
      "short_name": "SeekVLN",
      "title": "Seek Before You Move: Evidence Seeking for Progress Grounding in Vision-Language Navigation",
      "first_author": "Zhimin Wang",
      "source_url": "https://arxiv.org/abs/2609.37353v1",
      "existing_paper_id": null,
      "source_scope": "primary_complete_abstract",
      "fresh_checked_at": "2026-10-05",
      "original_checked_at": "2026-10-04T13:09:50Z",
      "abstract_sha256": "94f1d1ecb084da8801980b08e8326a636c01514c527da4b70d8abc7c8b646dc0",
      "locator": "Abstract，网页行 16–20",
      "event_at": "2026-09-29T12:18:16Z",
      "event_kind": "new",
      "problem": "长程VLN中，局部观测不足仍继续行动会误判进度。",
      "author_solution": "先用未来专家动作补视角监督，再以同状态反事实分支奖励训练主动取证。",
      "attribution": "author_claim_and_curator_problem_summary",
      "placements": [
        {
          "node_id": "task-vln",
          "fit": "direct",
          "why": "摘要明确是长指令、部分第一视角观测下的视觉语言导航。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-learned-policy",
          "fit": "direct",
          "why": "先监督微调，再按后续导航收益进行强化微调；对应学习出的取证与导航策略。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-runtime",
          "fit": "partial",
          "why": "主动补充观测服务当前进度判断与后续行动；仅贴合反馈闭环，不据摘要认定几何工具执行或恢复/停止机制。",
          "status": "candidate",
          "attribution": "curator_organization"
        }
      ],
      "weekly_theme_ids": [
        "evidence-and-action"
      ],
      "next_checks": [
        "核正文中补视角动作、额外观测成本及动作预算，确认取证在何时触发。",
        "核FRG是否使用训练专有未来信息、C2PO同状态分支与奖励实现，以及R2R-CE/RxR-CE的基座和消融控制。"
      ],
      "comparison_limits": [
        "摘要所称提升是相对其基座；没有核实训练量、传感器、视角或预算，不能与其他论文摘要SR排名。",
        "训练时使用未来专家动作不等于测试时可知未来；主动取证也不等于人工求助。"
      ],
      "branch_proposals": [
        {
          "label": "主动感知 / 证据获取",
          "why": "现有route-runtime过宽，不能单独表达何时主动取得新观测。",
          "status": "uncreated_candidate"
        }
      ],
      "full_paper_read": false,
      "version_comparison_performed": false,
      "experiments_independently_verified": false,
      "canonical_id": "arxiv:2609.37353",
      "paper_id": "arxiv:2609.37353",
      "groups": [
        "evidence-and-action"
      ],
      "tasks": [
        "task-vln"
      ],
      "routes": [
        "route-learned-policy",
        "route-runtime"
      ],
      "mode": "weekly"
    },
    {
      "versioned_id": "2609.39579v1",
      "short_name": "AVERT-VLN",
      "title": "AVERT-VLN: Abstention-aware Visual Error Recovery and Training for Vision-and-Language Navigation",
      "first_author": "Minrui Liu",
      "source_url": "https://arxiv.org/abs/2609.39579v1",
      "existing_paper_id": null,
      "source_scope": "primary_complete_abstract",
      "fresh_checked_at": "2026-10-05",
      "original_checked_at": "2026-10-04T13:09:50Z",
      "abstract_sha256": "915e8dbc779cc626bf6107f6084ffd5c29656eaf00c9ab841618b67b66b65756",
      "locator": "Abstract，网页行 16–20",
      "event_at": "2026-09-30T12:10:53Z",
      "event_kind": "new",
      "problem": "未见环境VLN偏航时如何识别并恢复。",
      "author_solution": "用独立监测器判偏航，暂停自主执行并请求人工指引，再把纠错轨迹转为偏好训练。",
      "attribution": "author_claim_and_curator_problem_summary",
      "placements": [
        {
          "node_id": "task-vln",
          "fit": "direct",
          "why": "摘要明确为未见环境中的指令执行、偏航监测与恢复。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-runtime",
          "fit": "direct",
          "why": "旁路监测执行一致性；控制器接受LOST判定后暂停、请求人工指引并恢复。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-learned-policy",
          "fit": "direct",
          "why": "离线把偏航失败变成共享决策上下文中的偏好对，限定被纠正决策。",
          "status": "candidate",
          "attribution": "curator_organization"
        }
      ],
      "weekly_theme_ids": [
        "evidence-and-action"
      ],
      "next_checks": [
        "核人工协助协议：触发门槛、帮助形式、介入次数/成本、协助者可见信息与公平对照。",
        "核监测器训练数据、误报漏报、异步延迟，以及在线协助与离线偏好学习分别带来的收益。"
      ],
      "comparison_limits": [
        "摘要的R2R-CE/RxR-CE成绩明确来自human-assisted评测，不能当成纯自主导航成绩。",
        "使用视觉历史评估一致性不等于上下文压缩，故不挂route-context；LOSTNAV训练数据不自动等于新评测协议。"
      ],
      "branch_proposals": [
        {
          "label": "选择性人工协助 / 拒绝与恢复",
          "why": "现route-runtime未区分自主恢复与请求人类指引，需把协助条件作为显式协议维度。",
          "status": "uncreated_candidate"
        }
      ],
      "full_paper_read": false,
      "version_comparison_performed": false,
      "experiments_independently_verified": false,
      "canonical_id": "arxiv:2609.39579",
      "paper_id": "arxiv:2609.39579",
      "groups": [
        "evidence-and-action"
      ],
      "tasks": [
        "task-vln"
      ],
      "routes": [
        "route-runtime",
        "route-learned-policy"
      ],
      "mode": "weekly"
    },
    {
      "versioned_id": "2609.39915v1",
      "short_name": "NavHarness · Adaptive Goals",
      "title": "NavHarness: Adaptive Goals for Agentic Vision-Language Navigation",
      "first_author": "Haoxiang Shi",
      "source_url": "https://arxiv.org/abs/2609.39915v1",
      "existing_paper_id": null,
      "source_scope": "primary_complete_abstract",
      "fresh_checked_at": "2026-10-05",
      "original_checked_at": "2026-10-04T13:09:50Z",
      "abstract_sha256": "485d0308a4c0f3e4acd0087016e33402118a2133522b8fcdbd272e8d29d6bbba",
      "locator": "Abstract，网页行 16–19",
      "event_at": "2026-09-30T15:06:45Z",
      "event_kind": "new",
      "problem": "长程VLN既要局部动作符合路线，又要控制历史开销。",
      "author_solution": "让目标、执行、验证代理协作，并在目标完成后压缩多模态上下文。",
      "attribution": "author_claim_and_curator_problem_summary",
      "placements": [
        {
          "node_id": "task-vln",
          "fit": "direct",
          "why": "摘要明确以指令和观测驱动长程VLN，并在R2R-CE/RxR-CE评测。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-runtime",
          "fit": "direct",
          "why": "自适应局部目标→视动执行→目标专用问题验证完成，形成目标反馈闭环。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-context",
          "fit": "direct",
          "why": "已验证的目标完成标记压缩边界，保留后续导航所需多模态历史。",
          "status": "candidate",
          "attribution": "curator_organization"
        }
      ],
      "weekly_theme_ids": [
        "evidence-and-action"
      ],
      "next_checks": [
        "核目标表示、验证问题、失败后的重试/重规划及具体动作接口。",
        "核压缩保留内容、token/推理时延及基座控制；核实机8条路线×3次的路线难度、成功规则与重复试验协议。"
      ],
      "comparison_limits": [
        "Memory Agent在摘要中做交互历史压缩，不能据名称认定其具有空间地图或跨任务长期记忆。",
        "这是2609.39915v1，不能合并为2609.34276v1；未核相同基座和预算，实机或仿真数字不作跨文排名。"
      ],
      "branch_proposals": [],
      "full_paper_read": false,
      "version_comparison_performed": false,
      "experiments_independently_verified": false,
      "canonical_id": "arxiv:2609.39915",
      "paper_id": "arxiv:2609.39915",
      "groups": [
        "evidence-and-action"
      ],
      "tasks": [
        "task-vln"
      ],
      "routes": [
        "route-runtime",
        "route-context"
      ],
      "mode": "weekly"
    },
    {
      "versioned_id": "2609.34276v1",
      "short_name": "NavHarness · Lifelong",
      "title": "NavHarness: Towards Lifelong Embodied Navigation",
      "first_author": "Xunyi Zhao",
      "source_url": "https://arxiv.org/abs/2609.34276v1",
      "existing_paper_id": "navharness",
      "source_scope": "primary_complete_abstract",
      "fresh_checked_at": "2026-10-05",
      "original_checked_at": "2026-10-04T13:09:50Z",
      "abstract_sha256": "87fa8de6df6dc16bdd63c6744d2284f8c3df0fbb1156ca7ca7bd400384eb2093",
      "locator": "Abstract，网页行 16–19",
      "event_at": "2026-09-28T04:24:47Z",
      "event_kind": "new",
      "problem": "连续任务中旧地图与搜索记录可能缺失或冲突。",
      "author_solution": "以免训练导航框架将观测核对、修正、结果验证及会话交接纳入跨任务记忆循环。",
      "attribution": "author_claim_and_curator_problem_summary",
      "placements": [
        {
          "node_id": "task-continual",
          "fit": "direct",
          "why": "摘要核心是新任务或恢复会话复用此前地图、记录和房屋知识。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-spatial-memory",
          "fit": "direct",
          "why": "读取地图/记录/房屋知识，依新观测纠正，跨新会话保留经验。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-runtime",
          "fit": "direct",
          "why": "导航循环内核对记忆并引导动作，以结果验证和运行总结支持后续使用。",
          "status": "candidate",
          "attribution": "curator_organization"
        }
      ],
      "weekly_theme_ids": [
        "memory-validity"
      ],
      "next_checks": [
        "核GOAT-Bench、IR2R-CE的顺序任务、恢复预算、位姿来源与s-SR/e-SR定义。",
        "核经验存储和纠错权限、交接与等长摘要对照、跨房屋整理设置及环境是否实际动态。"
      ],
      "comparison_limits": [
        "training-free和跨会话记忆不等于权重持续学习，有限任务序列也不自动证明无限期终身运行。",
        "摘要中的基座不同；GOAT-Bench s-SR/e-SR不能与R2R-CE单任务SR直接比较。",
        "本轮不沿用旧试点正文已核范围；两个NavHarness不是版本关系。"
      ],
      "branch_proposals": [
        {
          "label": "跨会话经验整理与纠错",
          "why": "可暂挂空间记忆和运行闭环，但跨会话记录治理需要更细分支。",
          "status": "uncreated_candidate"
        }
      ],
      "full_paper_read": false,
      "version_comparison_performed": false,
      "experiments_independently_verified": false,
      "canonical_id": "navharness",
      "paper_id": "navharness",
      "groups": [
        "memory-validity"
      ],
      "tasks": [
        "task-continual"
      ],
      "routes": [
        "route-spatial-memory",
        "route-runtime"
      ],
      "mode": "weekly"
    },
    {
      "versioned_id": "2609.39166v2",
      "short_name": "EvolvingNav",
      "title": "Beyond the Remembered World: Predictive 4D Belief for Persistent Navigation in Evolving Worlds",
      "first_author": "Mingjian Gao",
      "source_url": "https://arxiv.org/abs/2609.39166v2",
      "existing_paper_id": null,
      "source_scope": "primary_complete_abstract",
      "fresh_checked_at": "2026-10-05",
      "original_checked_at": "2026-10-04T13:09:50Z",
      "abstract_sha256": "68b3075149180704df42b5cf39c4648b1192a3d6a1104f3208fac4ed18a8b5b4",
      "locator": "Abstract，网页行 16–19",
      "event_at": "2026-10-01T12:48:26Z",
      "event_kind": "revision",
      "problem": "反复访问时目标会在不可见处移动。",
      "author_solution": "由带时标物体历史建立持续/迁移信念，预测检查时刻占据，并用可见性校准证据更新导航。",
      "attribution": "author_claim_and_curator_problem_summary",
      "placements": [
        {
          "node_id": "task-objectnav",
          "fit": "partial",
          "why": "任务是推断目标位置并前往检查；当前物体目标分支可容纳，但缺少演化世界条件。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "task-continual",
          "fit": "partial",
          "why": "反复访问与持久空间记忆贴合持续导航部分；摘要未证明跨任务策略学习。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-spatial-memory",
          "fit": "partial",
          "why": "时间化物体历史驱动belief传播、预测和证据修订，超出静态位置检索。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-runtime",
          "fit": "partial",
          "why": "冻结零样本视觉语言控制器利用更新belief选动作、重规划；不声称已核几何执行实现。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-protocol",
          "fit": "direct",
          "why": "作者另提出EvoWorld-Bench，明确设置导航前及导航期间变化，适合作为协议候选。",
          "status": "candidate",
          "attribution": "curator_organization"
        }
      ],
      "weekly_theme_ids": [
        "memory-validity"
      ],
      "next_checks": [
        "核隐藏变化过程、时间参数学习来源、候选集外概率质量、漏检概率校准与证据去重。",
        "核EvoWorld-Bench划分、变化模式可学习性、传感器/动作/预算及配对对照；若要判断v2变化，先逐版本diff。"
      ],
      "comparison_limits": [
        "动态目标、到达时刻预测和可见性条件与静态ObjectNav不同，不能与静态基准直接排优劣。",
        "此处预测参与运行时belief与规划；不能和只用地图预测作训练监督的InsightMap混为同一路测试机制。",
        "v2仅说明修订事件；本轮未读v1，贡献变化未知。"
      ],
      "branch_proposals": [
        {
          "label": "演化世界中的持续目标导航",
          "why": "现任务树缺少目标在导航期间变化的专门任务条件。",
          "status": "uncreated_candidate"
        },
        {
          "label": "时序不确定性 / 预测belief与证据过滤",
          "why": "现空间记忆主线不能完整表达到达时预测和可见性条件的负证据更新。",
          "status": "uncreated_candidate"
        }
      ],
      "full_paper_read": false,
      "version_comparison_performed": false,
      "experiments_independently_verified": false,
      "canonical_id": "arxiv:2609.39166",
      "paper_id": "arxiv:2609.39166",
      "groups": [
        "memory-validity"
      ],
      "tasks": [
        "task-objectnav",
        "task-continual"
      ],
      "routes": [
        "route-spatial-memory",
        "route-runtime",
        "route-protocol"
      ],
      "mode": "weekly"
    },
    {
      "versioned_id": "2609.37187v1",
      "short_name": "InsightMap",
      "title": "InsightMap: Structured Spatial Modeling for Embodied Multimodal Reasoning",
      "first_author": "Hongpei Zheng",
      "source_url": "https://arxiv.org/abs/2609.37187v1",
      "existing_paper_id": null,
      "source_scope": "primary_complete_abstract",
      "fresh_checked_at": "2026-10-05",
      "original_checked_at": "2026-10-04T13:09:50Z",
      "abstract_sha256": "90b00578404a87b0270e264f42fc7ae98998e636ad2799682a944cb9184480c0",
      "locator": "Abstract，网页行 16–18",
      "event_at": "2026-09-29T10:10:18Z",
      "event_kind": "new",
      "problem": "语言导航需把局部观察连到稳定空间参照。",
      "author_solution": "用俯视图记忆联结历史视角，联合训练动作与动作后地图预测；预测仅作训练辅助。",
      "attribution": "author_claim_and_curator_problem_summary",
      "placements": [
        {
          "node_id": "task-vln",
          "fit": "direct",
          "why": "摘要明确语言导航且报告R2R-CE/RxR-CE；其他静态空间任务另留待建分支。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-spatial-memory",
          "fit": "partial",
          "why": "历史视角关联标注地图位置，显式俯视图作空间记忆；不据此推断跨任务更新。",
          "status": "candidate",
          "attribution": "curator_organization"
        },
        {
          "node_id": "route-learned-policy",
          "fit": "direct",
          "why": "共享多模态骨干联合学习动作和地图预测，导航推理从观测空间上下文解码动作。",
          "status": "candidate",
          "attribution": "curator_organization"
        }
      ],
      "weekly_theme_ids": [
        "prediction-interface"
      ],
      "next_checks": [
        "核俯视图坐标、标签和RGB-D对齐，确认训练/测试信息可见性及记忆容量。",
        "核动作与地图预测联合损失和辅助监督消融；分别核导航、问答、情境推理与3D定位的数据划分和指标。"
      ],
      "comparison_limits": [
        "地图预测是辅助训练监督；摘要未采用测试时预测rollout来选动作，不可画成想象规划链。",
        "共享骨干支持多个任务不等于ObjectNav或跨任务持续导航；CIDEr、问答准确率、IoU定位和SR不能混合排名。"
      ],
      "branch_proposals": [
        {
          "label": "静态具身空间问答 / 情境推理 / 3D定位",
          "why": "现三类任务树仅导航，不能硬塞ScanQA、SQA3D、ScanRefer。",
          "status": "uncreated_candidate"
        },
        {
          "label": "动作条件空间预测辅助训练",
          "why": "可挂学习策略，但需独立标出训练辅助用途，避免误读为运行时预测规划。",
          "status": "uncreated_candidate"
        }
      ],
      "full_paper_read": false,
      "version_comparison_performed": false,
      "experiments_independently_verified": false,
      "canonical_id": "arxiv:2609.37187",
      "paper_id": "arxiv:2609.37187",
      "groups": [
        "prediction-interface"
      ],
      "tasks": [
        "task-vln"
      ],
      "routes": [
        "route-spatial-memory",
        "route-learned-policy"
      ],
      "mode": "weekly"
    }
  ],
  "daily": {
    "date": "2026-10-05",
    "window": {
      "start": "2026-10-04T08:11:15Z",
      "end": "2026-10-05T08:11:15Z",
      "timezone": "UTC",
      "date_field": "updated_at",
      "inclusive": true,
      "duration_hours": 24
    },
    "status": "no_material_update",
    "candidate_count": 0,
    "mapping_ids": []
  },
  "weekly": {
    "date": "2026-10-04",
    "window": {
      "start": "2026-09-27T12:41:03Z",
      "end": "2026-10-04T12:41:03Z",
      "timezone": "UTC",
      "date_field": "updated_at",
      "inclusive": true,
      "duration_hours": 168
    },
    "status": "ready",
    "candidate_count": 238,
    "abstract_count": 11,
    "mapping_ids": [
      "2609.37353v1",
      "2609.39579v1",
      "2609.39915v1",
      "2609.34276v1",
      "2609.39166v2",
      "2609.37187v1"
    ],
    "unmapped_abstracts": [
      {
        "versioned_id": "2609.34707v1",
        "reason": "本轮未重新核摘要并制作位置映射；不是不相关或已排除。"
      },
      {
        "versioned_id": "2609.33581v1",
        "reason": "空中导航条件尚无专门任务分支，本轮未重新核摘要和迁移适用性。"
      },
      {
        "versioned_id": "2609.39763v1",
        "reason": "本轮未重新核摘要并制作位置映射；不是不相关或已排除。"
      },
      {
        "versioned_id": "2610.01612v1",
        "reason": "涉及足臂控制/移动操作，超出当前导航双树完整覆盖；保留待补领域分支，不硬挂导航方法。"
      },
      {
        "versioned_id": "2609.39388v1",
        "reason": "涉及足臂控制/移动操作，超出当前导航双树完整覆盖；保留待补领域分支，不硬挂导航方法。"
      }
    ]
  },
  "limitations": [
    "六篇重新核读摘要，只覆盖本期11条摘要证据的一部分，不代表238候选全部挂树。",
    "核查发生在10月5日，不把上周论文改标为今日发现。",
    "本overlay只提出编辑性位置候选，不修改已有双树节点或学术关系。",
    "缺分支是当前组织覆盖缺口，不是研究空白；修订不等于贡献变化。",
    "全文、代码、独立复现和跨期比较均未在本轮执行。"
  ],
  "core_definition": "实际读取指定正文段落与评测/限制；非全文阅读",
  "pool_counts": {
    "candidate_pool": 28,
    "targeted_body_core": 10,
    "full_papers_read": 0,
    "independent_reproductions": 0
  },
  "method_reference": {
    "url": "https://aoiota.github.io/ResearchVoyager/review/editorial/",
    "label": "ResearchVoyager · 公开方法说明",
    "note": "方法概念图帮助组织阅读，不表示论文引用、继承关系或研究价值排名。"
  },
  "source_files": [
    "shared-tree.json",
    "core-papers.json",
    "navigation-evidence.json",
    "candidate-pool.json",
    "radar-tree-overlay.json"
  ]
};
