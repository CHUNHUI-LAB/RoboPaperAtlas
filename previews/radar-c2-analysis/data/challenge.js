window.CHALLENGE_TREE = {
  "schema": "challenge-insight-candidate/1",
  "title": "从共同challenge收集distinct insights：导航39篇可核查重建候选",
  "status": "candidate_not_published",
  "source_snapshot_sha256": "289901d53734196a8469c67303e423c799412c665dbacff84c9db531e8eb41be",
  "checked_at": "2026-10-06",
  "coverage": {
    "source_records": 39,
    "canonical_papers": 39,
    "mapped_papers": 39,
    "challenges": 12,
    "algorithmic_challenges": 10,
    "evaluation_challenges": 2,
    "distinct_insight_nodes": 49,
    "method_or_protocol_nodes": 44,
    "mapping_variants": 70,
    "unique_evidence_records_used": 101,
    "new_primary_targeted_body_rechecks": 11,
    "additional_complete_abstract_only_rechecks": 2,
    "full_papers_read_in_this_rebuild": 0,
    "code_read_or_run_in_this_rebuild": 0,
    "independent_reproductions": 0,
    "academic_edges": 0,
    "insights_with_at_least_one_direct_author_rationale_anchor": 15,
    "insights_with_editorial_rationale_pending_author_check": 34,
    "mapping_status_counts": {
      "candidate_requires_finer_locator": 27,
      "primary_method_rechecked": 5,
      "primary_protocol_rechecked": 1,
      "supported_by_recorded_source_claim": 37
    }
  },
  "challenges": [
    {
      "challenge_id": "C01",
      "title": "目标尚未出现时，怎样在未知场景中选择下一处搜索区域？",
      "task_conditions": [
        "未知室内类别/物体目标导航；目标尚未可靠检测",
        "可获得在线空间表示或局部候选，步数/路程预算有限；语义先验可能错误"
      ],
      "testable_difficulty": "应能在相同传感器与控制器下区分：语义先验把搜索引向有用区域，还是只增加绕路/重复探索；目标可见后的接近不属于本问题。",
      "scope": "algorithmic_search",
      "comparison_guardrails": [
        "ESC/L3MVN/LFG/VoroNav为相近搜索子问题，传感器、GT语义、frontier定义及训练组件不同，不能按原表SR排序",
        "ImagineNav以未来视图和PointNav动作候选工作，与frontier搜索是相邻表示形式",
        "Engineering Outruns Intelligence的几何替换结论带GT语义/检测器条件"
      ],
      "insight_ids": [
        "I01-1",
        "I01-2",
        "I01-3",
        "I01-4"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "engineering-outruns-intelligence",
        "esc",
        "imaginenav",
        "l3mvn",
        "lfg",
        "voronav"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C02",
      "title": "目标含实例属性或房间/楼层约束时，怎样避免找到同类却找错目标？",
      "task_conditions": [
        "图像、描述或层级空间语言指定目标，不只是任一同类物体",
        "多个外观相似实例或空间约束；候选需要绑定可导航位置"
      ],
      "testable_difficulty": "将类别识别、实例/关系检索与最终到达分别检查，统计同类误匹配、房间约束违反和检索正确但到达失败。",
      "scope": "target_grounding",
      "comparison_guardrails": [
        "GOAT实机多模态、HOV-SG预建图层级检索、SAP-Nav在线层级开放词汇任务是相邻任务；共享消歧困难，不是统一benchmark",
        "类别ObjectNav成功不能代替实例目标成功",
        "检索准确率不能当导航SR"
      ],
      "insight_ids": [
        "I02-1",
        "I02-2",
        "I02-3"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "anwar2025remembr",
        "goat",
        "goat-bench",
        "sap-nav",
        "werby2024hovsg"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C03",
      "title": "连续空间中，怎样把语义决策落到当前可通行的动作？",
      "task_conditions": [
        "动作实际经过空间，不是沿给定导航图瞬移",
        "高层模型输出像素、方向、局部目标或语义子目标；可见不等于可达"
      ],
      "testable_difficulty": "记录无效目标、无候选、碰撞、局部执行失败；在同一机器人尺寸、深度、位姿及碰撞规则下检验。",
      "scope": "continuous_action_grounding",
      "comparison_guardrails": [
        "预定义图上的可导航候选不作为本挑战已解决的直接证据",
        "地图路径检查不等于物理安全保证",
        "碰撞滑动、机器人尺寸、低层oracle/学习控制器必须分列"
      ],
      "insight_ids": [
        "I03-1",
        "I03-2",
        "I03-3",
        "I03-4"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "agenticnav-tool-harness",
        "harnessvln",
        "holoagent-0",
        "imaginenav",
        "instructnav",
        "qwen-robotnav",
        "rajvanshi2024saynav",
        "vlmnav"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C04",
      "title": "路线跟随中走错已探索分支后，怎样识别偏离并回到有用路径？",
      "task_conditions": [
        "主要为VLN路线跟随",
        "有已访节点/地点标识和可回退路径；完成度或路线信息可能不可靠"
      ],
      "testable_difficulty": "区分进度估计质量、回退触发、实际回退路径代价，以及再次访问时是否重犯；不能只看终点SR。",
      "scope": "route_recovery",
      "comparison_guardrails": [
        "离散图回退与连续机器人碰撞恢复分开",
        "估计进度不是独立完成证据",
        "训练策略与零样本LLM agent不以原始总分排名"
      ],
      "insight_ids": [
        "I04-1",
        "I04-2",
        "I04-3"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "ham-vln",
        "ma2019regretful",
        "mapgpt",
        "navgpt2"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C05",
      "title": "长episode中，怎样在有限输入预算内保留当前决策真正需要的历史？",
      "task_conditions": [
        "导航或取证交互不断产生图像、动作和文本历史",
        "上下文/视觉token有限，截短可能丢进度、目标证据或路径信息"
      ],
      "testable_difficulty": "固定骨干、任务及执行预算，分别测漏证据/遗忘失败、token成本与任务表现；存储、输入token、总费用和时延分开。",
      "scope": "bounded_decision_context",
      "comparison_guardrails": [
        "episode内压缩不能写成跨任务lifelong记忆",
        "目标检索、摘要、token分配属于不同insight，不用“有memory”统一",
        "MemoNav是多目标ImageNav；ReMEmbR主要为历史QA，属相邻任务"
      ],
      "insight_ids": [
        "I05-1",
        "I05-2",
        "I05-3",
        "I05-4",
        "I05-5",
        "I05-6",
        "I05-7"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "3d-mem",
        "agenticnav-tool-harness",
        "arxiv:2609.39915",
        "ham-vln",
        "li2024memonav",
        "navgpt",
        "navmcp",
        "profocus",
        "qwen-robotnav",
        "rana2023sayplan"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C06",
      "title": "同一环境有后续任务时，怎样把先前经验用于当前目标而不是重新探索？",
      "task_conditions": [
        "跨子目标、跨episode或恢复会话，环境信息可能复用",
        "先前看到的区域/实例/行为不一定与当前目标相关"
      ],
      "testable_difficulty": "区分记忆是否保留、是否取到相关项、是否改变搜索/执行；按目标先前可见性与序号分析。",
      "scope": "cross_task_experience",
      "comparison_guardrails": [
        "IVLN含oracle纠偏/搬运与被动观察；GOAT系列从实际结束点接续；会话恢复又是另一边界",
        "静态有限序列不是无限期动态部署",
        "同一论文的EM-EQA被动输入不可被说成在线探索"
      ],
      "insight_ids": [
        "I06-1",
        "I06-2",
        "I06-3",
        "I06-4",
        "I06-5"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "3d-mem",
        "anwar2025remembr",
        "goat",
        "goat-bench",
        "krantz2023ivln",
        "navharness",
        "wang2026lmee",
        "xu2026memoir"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C07",
      "title": "错误检测、推断或旧状态进入记忆后，怎样防止它继续误导后续搜索？",
      "task_conditions": [
        "将过去观察/推断用于后续决策",
        "观测与假设、暂时未见与有证据排除不能混淆"
      ],
      "testable_difficulty": "人为或自然出现错误记录后，检查错误是否被撤回/降权、依赖结果是否保留、是否误把未见当不存在，并统计恢复代价。",
      "scope": "memory_correction",
      "comparison_guardrails": [
        "HGR假设依赖、TriHelper检测误报、NavHarness会话交接是不同错误来源/时间尺度",
        "不能把地点失败笔记等同自动删除错误知识",
        "错误修复的机制存在不等于动态场景已验证"
      ],
      "insight_ids": [
        "I07-1",
        "I07-2",
        "I07-3",
        "I07-4"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "holoagent-0",
        "hypothesis-graph-refinement",
        "navharness",
        "trihelper"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C08",
      "title": "模型说“完成/停止”时，怎样判断局部目标或最终导航目标真的已满足？",
      "task_conditions": [
        "高层会发出子目标完成或STOP决策",
        "当前语义判断可能与几何到达、路线进度及实际执行结果不同"
      ],
      "testable_difficulty": "将误完成、过早STOP、延迟STOP和额外观察成本分别统计；局部子目标推进与最终SR分开。",
      "scope": "completion_verification",
      "comparison_guardrails": [
        "VLN路线进度、ObjectNav目标到达与EQA有证据可答不是同一成功条件",
        "独立调用不等于独立模型或可靠真值",
        "固定两次STOP、完成估计、几何/语义联合验证必须保持为不同insights"
      ],
      "insight_ids": [
        "I08-1",
        "I08-2",
        "I08-3",
        "I08-4"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "arxiv:2609.39915",
        "discussnav",
        "harnessvln",
        "instructnav",
        "vlmnav"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C09",
      "title": "当前观察不足以判断目标或回答问题时，下一次该看哪里？",
      "task_conditions": [
        "观测有限且带遮挡/角度/信息遗漏",
        "追加视觉查询或运动取景有成本，需要改变信息而非仅重复推理"
      ],
      "testable_difficulty": "检验追加观察是否减少目标误判/答案错误，同时报告裁剪调用、视点移动和总路程成本；不同动作不能计成同一预算。",
      "scope": "active_evidence_acquisition",
      "comparison_guardrails": [
        "ProFocus裁剪当前全景不等同SAP-Nav移动换位",
        "SafeVantage为ProcTHOR类别存在判断，不是到达目标ObjectNav",
        "3D-Mem/HGR的EM-EQA给定轨迹不能支持主动观察效果结论",
        "NavMCP是长程具身取证套件，不直接采用OpenEQA作为本次评测"
      ],
      "insight_ids": [
        "I09-1",
        "I09-2",
        "I09-3",
        "I09-4",
        "I09-5"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "3d-mem",
        "navmcp",
        "profocus",
        "safevantage",
        "sap-nav"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C10",
      "title": "执行遇到不可达、碰撞或重复失败时，怎样改变行为而非循环重试？",
      "task_conditions": [
        "已尝试或拟执行的局部动作有失败信号",
        "高层目标可能仍合理，但当前动作/计划不适合执行器或环境"
      ],
      "testable_difficulty": "逐类报告碰撞、无候选、无进展、重复目标、动作前置条件失败的恢复率与额外代价；不能只按最终SR归因。",
      "scope": "execution_recovery",
      "comparison_guardrails": [
        "实际机器人状态反馈、模拟PointNav失败与符号计划验证是不同失败证据",
        "路线走错的回退单列C04，不直接称为物理安全恢复",
        "恢复helper相互影响可能增加另一类失败"
      ],
      "insight_ids": [
        "I10-1",
        "I10-2",
        "I10-3",
        "I10-4"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "arxiv:2609.39915",
        "holoagent-0",
        "instructnav",
        "rajvanshi2024saynav",
        "rana2023sayplan",
        "trihelper"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C11",
      "title": "怎样确认比较的是同一个导航任务和同一种成功，而不是环境给了不同帮助？",
      "task_conditions": [
        "论文报告VLN/ObjectNav成功率或路径效率",
        "图拓扑、位姿、oracle可见性、低层控制、碰撞规则或成功距离可能不同"
      ],
      "testable_difficulty": "先列任务输入、动作/控制权、oracle信息、STOP规则、到达半径与可见性、样本和路径起点；缺项时不建立跨论文排名。",
      "scope": "evaluation_contract",
      "comparison_guardrails": [
        "此节点是评测challenge与作者协议insight，不强行当新policy机制",
        "协议相同仍需固定感知模型、训练、预算、场景及统计不确定性",
        "共同challenge的组织边不是论文引用或学术继承"
      ],
      "insight_ids": [
        "I11-1",
        "I11-2",
        "I11-3"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "batra2020objectnav",
        "goat",
        "goat-bench",
        "krantz2020vlnce"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    },
    {
      "challenge_id": "C12",
      "title": "长期任务成绩提高时，怎样分清记忆、探索、识别和执行分别贡献了什么？",
      "task_conditions": [
        "方法联合改变记忆、搜索、目标识别或训练",
        "总SR/SPL无法单独说明历史是否被有效调用"
      ],
      "testable_difficulty": "对同一模型固定其他条件清空/保留记忆，分别测目标模态、先前可见性、检索是否成功、探索与停止失败；避免把整套策略对比叫memory-only。",
      "scope": "evaluation_attribution",
      "comparison_guardrails": [
        "以下作者实际协议与编者建议分列；未运行新的消融",
        "记忆重置改变已知信息，不是自动无混杂的所有机制因果结论",
        "GT语义、训练量和子集/全量结果分开"
      ],
      "insight_ids": [
        "I12-1",
        "I12-2",
        "I12-3"
      ],
      "attribution": "editorial_synthesis",
      "diagnostic_status": "suggested_tests_not_new_experiments",
      "supporting_paper_ids": [
        "engineering-outruns-intelligence",
        "goat-bench",
        "ham-vln",
        "krantz2023ivln",
        "wang2026lmee"
      ],
      "not_claimed": [
        "领域全部challenge已穷尽",
        "所有作者使用相同challenge表述",
        "该challenge下各原论文分数可直接排名"
      ]
    }
  ],
  "insights": [
    {
      "insight_id": "I01-1",
      "challenge_id": "C01",
      "title": "让语言常识作为可被几何成本约束的软启发，而非完整路线",
      "mechanism": "把目标与房间/物体的语义关系变成候选搜索位置的分数，再由空间成本、规则或退路决定实际候选。",
      "conditions": [
        "保留显式空间规划/低层控制",
        "三种机制仅共享可错先验+几何约束这一设计原则，优化形式不能合并"
      ],
      "variants": [
        {
          "paper_id": "esc",
          "method_claim": "用GLIP语义、DeBERTa关联与PSL软规则联合距离选frontier。",
          "evidence_refs": [
            "esc:e1",
            "esc:pipeline",
            "esc:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "PSL软约束，不是生成式自由工具调用；GPS等条件需单列。",
          "mechanism_variant": "用GLIP语义、DeBERTa关联与PSL软规则联合距离选frontier。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [
            "esc:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "esc:method",
          "variant_id": "I01-1:1"
        },
        {
          "paper_id": "l3mvn",
          "method_claim": "语义低分时回退cost-utility；局部FMM逐步重规划。",
          "evidence_refs": [
            "l3mvn:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "语言评分/训练embedding head两支有别，非所有模块无训练。",
          "mechanism_variant": "语义低分时回退cost-utility；局部FMM逐步重规划。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "l3mvn:method",
          "variant_id": "I01-1:2"
        },
        {
          "paper_id": "lfg",
          "method_claim": "正负提示的采样启发与距离共同用于搜索；已见目标则从地图取位置。",
          "evidence_refs": [
            "lfg:e1",
            "lfg:pipeline",
            "lfg:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "模拟baseline采用GT语义，不能当真实检测下的一致比较。",
          "mechanism_variant": "正负提示的采样启发与距离共同用于搜索；已见目标则从地图取位置。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [
            "lfg:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "lfg:method",
          "variant_id": "I01-1:3"
        }
      ],
      "distinction_from_siblings": "区别于I01-2重构决策位置、I01-3将未来空间转换成视觉候选、I01-4检验移除复杂语义探索后的替代。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "语义常识可缩小搜索范围，却不能独立保证当前场景的目标位置。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "把它作为软偏置并同时保留距离/成本与退路，可在利用先验时限制错误先验的影响。",
      "rationale": {
        "recognition": "语义常识可缩小搜索范围，却不能独立保证当前场景的目标位置。",
        "explanation": "把它作为软偏置并同时保留距离/成本与退路，可在利用先验时限制错误先验的影响。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "lfg:rationale",
          "esc:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I01-2",
      "challenge_id": "C01",
      "title": "在可通行拓扑的决策节点获取远视信息再选择分支",
      "mechanism": "利用Reduced Voronoi Graph组织已探索空间，在节点获取全景/远视描述，并以探索与效率奖励约束语义偏好。",
      "conditions": [
        "有在线几何/语义地图",
        "图节点采观测不是固定频率blind frontier选择"
      ],
      "variants": [
        {
          "paper_id": "voronav",
          "method_claim": "决策点与Reduced Voronoi Graph绑定，到节点转一圈采观测；拓扑奖励与语义评分配合。",
          "evidence_refs": [
            "voronav:e1",
            "voronav:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "在线派生可通行图，不等同模拟器给定VLN导航图。",
          "mechanism_variant": "决策点与Reduced Voronoi Graph绑定，到节点转一圈采观测；拓扑奖励与语义评分配合。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "voronav:method",
          "variant_id": "I01-2:1"
        }
      ],
      "distinction_from_siblings": "核心变化是何处决策及可见信息，不是又一种语言常识打分器。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "搜索决策的质量同时受决策位置和可见的远处空间信息限制。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "把选择点放在可通行拓扑节点并提供路径/远视描述，可让分支选择依据超出眼前局部语义；该因果解释需与原文方法分开。",
      "rationale": {
        "recognition": "搜索决策的质量同时受决策位置和可见的远处空间信息限制。",
        "explanation": "把选择点放在可通行拓扑节点并提供路径/远视描述，可让分支选择依据超出眼前局部语义；该因果解释需与原文方法分开。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I01-3",
      "challenge_id": "C01",
      "title": "把下一步空间选择改写为候选未来视图选择",
      "mechanism": "由候选位姿与新视图合成生成可比较的视觉后果，让VLM选择，再交给局部PointNav执行。",
      "conditions": [
        "mapless视觉候选路线",
        "Where2Imagine经过训练；NVS预测不能当真实观察"
      ],
      "variants": [
        {
          "paper_id": "imaginenav",
          "method_claim": "Where2Imagine提出位姿、NVS合成视图，VLM选后交PointNav，再用新观测循环。",
          "evidence_refs": [
            "imaginenav:pipeline",
            "imaginenav:e1",
            "imaginenav:e2",
            "imaginenav:rationale"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "未来真实图像Oracle与合成视图结果分开；不是frontier分数形式。",
          "mechanism_variant": "Where2Imagine提出位姿、NVS合成视图，VLM选后交PointNav，再用新观测循环。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [
            "imaginenav:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "imaginenav:method",
          "variant_id": "I01-3:1"
        }
      ],
      "distinction_from_siblings": "利用想象辅助动作选择；与HGR显式维护可撤回语义假设、Memoir用想象检索历史也不相同。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "VLM较容易比较图像中的场景后果，空间位姿本身不直接提供这种信息。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "把候选位姿转为未来视图，能把抽象空间选择转成视觉判断；效果受视图预测真实性与PointNav执行能力约束。",
      "rationale": {
        "recognition": "VLM较容易比较图像中的场景后果，空间位姿本身不直接提供这种信息。",
        "explanation": "把候选位姿转为未来视图，能把抽象空间选择转成视觉判断；效果受视图预测真实性与PointNav执行能力约束。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "imaginenav:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I01-4",
      "challenge_id": "C01",
      "title": "把探索价值换为几何覆盖/代价，检验语言语义的必要性",
      "mechanism": "在共同地图与执行框架内替换探索value map，以FPE及轻量语义SHF进行条件化归因。",
      "conditions": [
        "对照实验必须固定感知、控制及任务集",
        "几何探索不意味着目标接近/停止完全不需要语义"
      ],
      "variants": [
        {
          "paper_id": "engineering-outruns-intelligence",
          "method_claim": "保留InstructNav框架，比较几何FPE与轻量语义SHF。",
          "evidence_refs": [
            "engineering-outruns-intelligence:pipeline",
            "engineering-outruns-intelligence:e1",
            "engineering-outruns-intelligence:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "主表GT语义；GLEE子集上FPE SR不胜InstructNav。",
          "mechanism_variant": "保留InstructNav框架，比较几何FPE与轻量语义SHF。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "engineering-outruns-intelligence:method",
          "variant_id": "I01-4:1"
        }
      ],
      "distinction_from_siblings": "这是替换和反事实检验路线，不可归并成“LLM导航无用”的共享观点。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "未知空间的几何覆盖和移动成本本身可以提供有效搜索信号。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "固定其他模块后更换探索value map，才能识别复杂语义推理在特定感知条件下是否有增益；不能外推为语言在导航中普遍无用。",
      "rationale": {
        "recognition": "未知空间的几何覆盖和移动成本本身可以提供有效搜索信号。",
        "explanation": "固定其他模块后更换探索value map，才能识别复杂语义推理在特定感知条件下是否有增益；不能外推为语言在导航中普遍无用。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I02-1",
      "challenge_id": "C02",
      "title": "保留实例的多视角外观与位置，再按目标模态匹配",
      "mechanism": "先区分场景中的实例，再把类别、语言或图像目标匹配到实例记录，而非只靠类别语义栅格。",
      "conditions": [
        "实例分割与位姿可用",
        "目标模态决定匹配器，类别过滤也会改变信息条件"
      ],
      "variants": [
        {
          "paper_id": "goat",
          "method_claim": "Object Instance Memory保存定位后的多视角；CLIP语言匹配与SuperGlue图像匹配后导航至实例。",
          "evidence_refs": [
            "goat:refresh",
            "goat:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "定量实机测试15类别；探索期阈值匹配与探索后最高分策略不同。",
          "mechanism_variant": "Object Instance Memory保存定位后的多视角；CLIP语言匹配与SuperGlue图像匹配后导航至实例。",
          "mapping_status": "primary_method_rechecked",
          "rationale_anchor_refs": [
            "goat:refresh"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "goat:method",
          "variant_id": "I02-1:1"
        },
        {
          "paper_id": "goat-bench",
          "method_claim": "Modular GOAT baseline用实例视图/CLIP特征及模态对应匹配；也与单一CLIP匹配baseline比较。",
          "evidence_refs": [
            "goat-bench:refresh"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "这是benchmark内已归因给GOAT的baseline实现说明，不是GOAT-Bench独立发明同一机制。",
          "mechanism_variant": "Modular GOAT baseline用实例视图/CLIP特征及模态对应匹配；也与单一CLIP匹配baseline比较。",
          "mapping_status": "primary_method_rechecked",
          "rationale_anchor_refs": [
            "goat-bench:refresh"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "goat-bench:protocol",
          "variant_id": "I02-1:2"
        }
      ],
      "distinction_from_siblings": "重点是实例粒度与模态匹配；不同于I02-2先用楼层/房间语义层级缩小候选。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "类别相同不足以标识目标实例，而同一实例不同视角可提供互补辨认线索。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "将多个视图绑定同一空间实例，再选择适合目标模态的匹配器，可支持类别地图无法单独提供的实例选择。",
      "rationale": {
        "recognition": "类别相同不足以标识目标实例，而同一实例不同视角可提供互补辨认线索。",
        "explanation": "将多个视图绑定同一空间实例，再选择适合目标模态的匹配器，可支持类别地图无法单独提供的实例选择。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "goat:refresh",
          "goat-bench:refresh"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I02-2",
      "challenge_id": "C02",
      "title": "把楼层—房间—物体关系作为检索约束",
      "mechanism": "将目标语言中的空间约束映射到层级语义结构，再关联候选物体和导航位置。",
      "conditions": [
        "层级空间分区有一定可靠性",
        "共享层级约束原则，离线建图与在线房间推断不合并"
      ],
      "variants": [
        {
          "paper_id": "werby2024hovsg",
          "method_claim": "建立楼层—房间—物体图，分层查询，并关联跨楼层Voronoi路径图。",
          "evidence_refs": [
            "werby2024hovsg:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "依赖先建图及里程计；41试次中检索与导航结果分开，非未知场景统一ObjectNav。",
          "mechanism_variant": "建立楼层—房间—物体图，分层查询，并关联跨楼层Voronoi路径图。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "werby2024hovsg:method",
          "variant_id": "I02-2:1"
        },
        {
          "paper_id": "sap-nav",
          "method_claim": "QSSR以房间语义BEV和快照表达空间约束，AVV再验证候选。",
          "evidence_refs": [
            "sap-nav:pipeline",
            "sap-nav:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "在线查询与主动验证；LangMap单目标/HM3D-OVON协议分列。",
          "mechanism_variant": "QSSR以房间语义BEV和快照表达空间约束，AVV再验证候选。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "sap-nav:method",
          "variant_id": "I02-2:2"
        }
      ],
      "distinction_from_siblings": "属于关系约束目标定位；不是把所有场景图或所有空间记忆都称为同一insight。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "目标语言中的房间和楼层约束能排除外观相似但位置不符的候选。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "显式语义层级使这些约束可在检索时使用，再把语义候选连接到几何路径；依赖分区和建图正确。",
      "rationale": {
        "recognition": "目标语言中的房间和楼层约束能排除外观相似但位置不符的候选。",
        "explanation": "显式语义层级使这些约束可在检索时使用，再把语义候选连接到几何路径；依赖分区和建图正确。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I02-3",
      "challenge_id": "C02",
      "title": "让检索结果保留时间与坐标，支持时空目标定位",
      "mechanism": "长期历史的语言问题通过文本、时间及位置条件多轮检索后，产生可交给导航的结构化位置。",
      "conditions": [
        "预先记录的机器人视频/历史",
        "NaVQA的目标生成与实例ObjectNav只属邻近支持"
      ],
      "variants": [
        {
          "paper_id": "anwar2025remembr",
          "method_claim": "VILA片段caption入库，LLM调用时间/空间/文本检索，输出答案及坐标。",
          "evidence_refs": [
            "anwar2025remembr:e1"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "主要评QA及目标定位；15米位置阈值不是近目标导航成功。",
          "mechanism_variant": "VILA片段caption入库，LLM调用时间/空间/文本检索，输出答案及坐标。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "anwar2025remembr:method",
          "variant_id": "I02-3:1"
        }
      ],
      "distinction_from_siblings": "此处是时空条件检索，并不声称解决GOAT式近距离实例识别。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "历史里“出现过什么”不足以产生导航目标，还需要“何时、何地”。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "把时间与空间条件作为检索键并保留坐标，可从长记录中找到与请求对应的位置；近距离到达仍需另测。",
      "rationale": {
        "recognition": "历史里“出现过什么”不足以产生导航目标，还需要“何时、何地”。",
        "explanation": "把时间与空间条件作为检索键并保留坐标，可从长记录中找到与请求对应的位置；近距离到达仍需另测。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I03-1",
      "challenge_id": "C03",
      "title": "把精确几何计算放在工具中约束视觉决策",
      "mechanism": "模型做语义选择，深度/几何工具承担像素到空间或可通行动作的构造、筛选。",
      "conditions": [
        "深度或等价几何信息可用",
        "像素查询与候选动作投影是不同实现，不能混称同一接口"
      ],
      "variants": [
        {
          "paper_id": "agenticnav-tool-harness",
          "method_claim": "query_depth反投影目标像素，move_to前检查障碍，按需召回视觉历史。",
          "evidence_refs": [
            "agenticnav-tool-harness:e1",
            "agenticnav-tool-harness:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "episode内；R2R-CE子集和指定模型条件，未读代码。",
          "mechanism_variant": "query_depth反投影目标像素，move_to前检查障碍，按需召回视觉历史。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "agenticnav-tool-harness:method",
          "variant_id": "I03-1:1"
        },
        {
          "paper_id": "vlmnav",
          "method_claim": "深度与探索体素生成候选，再将空间动作投影到图像让VLM选择。",
          "evidence_refs": [
            "vlmnav:e1",
            "vlmnav:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "可通行性未计机器人尺寸形状；allow_slide设置极大影响结果。",
          "mechanism_variant": "深度与探索体素生成候选，再将空间动作投影到图像让VLM选择。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "vlmnav:method",
          "variant_id": "I03-1:2"
        }
      ],
      "distinction_from_siblings": "区别在提案方向：AgenticNav由模型点像素后查几何；VLMnav先几何提案再让模型选。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "语义上看对方向不意味着具有可靠深度与可通行性。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "让精确几何工具约束目标或候选，减少模型从纯视觉文字直接臆测运动参数；仍可能遗漏本体尺寸与碰撞因素。",
      "rationale": {
        "recognition": "语义上看对方向不意味着具有可靠深度与可通行性。",
        "explanation": "让精确几何工具约束目标或候选，减少模型从纯视觉文字直接臆测运动参数；仍可能遗漏本体尺寸与碰撞因素。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I03-2",
      "challenge_id": "C03",
      "title": "将语言子目标转为空间价值场，再交显式路径规划",
      "mechanism": "DCoN分解/更新动作及地标，将多种value map组合成空间目标，由A*与低层控制执行。",
      "conditions": [
        "可构造场景点云/语义与轨迹图",
        "规划目标无可行点时反馈并重预测"
      ],
      "variants": [
        {
          "paper_id": "instructnav",
          "method_claim": "四类value map组合目标，障碍屏蔽、A*规划及低层执行形成反馈回路。",
          "evidence_refs": [
            "instructnav:e1",
            "instructnav:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "闭源模型及遮挡影响；不把失败反馈自动升级为独立验证器。",
          "mechanism_variant": "四类value map组合目标，障碍屏蔽、A*规划及低层执行形成反馈回路。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "instructnav:method",
          "variant_id": "I03-2:1"
        }
      ],
      "distinction_from_siblings": "价值场整合与几何路径规划，不是直接让LLM产出无约束低层运动。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "语言地标和动作约束必须与障碍、探索和历史访问约束作用在同一空间目标上。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "组合空间value map再规划路径，使多类约束能共同决定局部可执行目标，而不只输出自然语言路线。",
      "rationale": {
        "recognition": "语言地标和动作约束必须与障碍、探索和历史访问约束作用在同一空间目标上。",
        "explanation": "组合空间value map再规划路径，使多类约束能共同决定局部可执行目标，而不只输出自然语言路线。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I03-3",
      "challenge_id": "C03",
      "title": "语义子目标和局部导航执行采用明确分工",
      "mechanism": "上层按任务需要选择目标，下层使用专门导航策略/控制器完成局部运动，再由新观测推动下一步。",
      "conditions": [
        "下层控制器能力与信息必须单列",
        "学习控制、确定性控制、商业本体控制不是等价执行器"
      ],
      "variants": [
        {
          "paper_id": "rajvanshi2024saynav",
          "method_claim": "在线层次图支持短期navigate/look计划，并调用PointNav执行。",
          "evidence_refs": [
            "rajvanshi2024saynav:e1",
            "rajvanshi2024saynav:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "ProcTHOR 3目标；GT/视觉图、oracle/学习控制器分列，完整验证仍被列为未来工作。",
          "mechanism_variant": "在线层次图支持短期navigate/look计划，并调用PointNav执行。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "rajvanshi2024saynav:method",
          "variant_id": "I03-3:1"
        },
        {
          "paper_id": "imaginenav",
          "method_claim": "VLM从合成未来视图选择局部位姿，PointNav执行后再观察。",
          "evidence_refs": [
            "imaginenav:pipeline",
            "imaginenav:e1",
            "imaginenav:e2",
            "imaginenav:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "动作提案与视图合成有训练，不能据zero-shot称全系统免训练。",
          "mechanism_variant": "VLM从合成未来视图选择局部位姿，PointNav执行后再观察。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [
            "imaginenav:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "imaginenav:method",
          "variant_id": "I03-3:2"
        },
        {
          "paper_id": "qwen-robotnav",
          "method_claim": "策略编码任务参数化视觉历史并预测waypoint轨迹，供上层agent配置。",
          "evidence_refs": [
            "qwen-robotnav:pipeline",
            "qwen-robotnav:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "这是导航模型接口；不由接口存在推断上层验证或恢复机制。",
          "mechanism_variant": "策略编码任务参数化视觉历史并预测waypoint轨迹，供上层agent配置。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "qwen-robotnav:method",
          "variant_id": "I03-3:3"
        },
        {
          "paper_id": "holoagent-0",
          "method_claim": "技能图调度导航技能，typed接口与ROS2状态反馈连接执行。",
          "evidence_refs": [
            "holoagent-0:e1",
            "holoagent-0:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "导航定量与全技能定性分别解释；仅技能分工不证明所有技能稳健。",
          "mechanism_variant": "技能图调度导航技能，typed接口与ROS2状态反馈连接执行。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "holoagent-0:method",
          "variant_id": "I03-3:4"
        }
      ],
      "distinction_from_siblings": "仅共享执行职责分离。每一论文的目标空间、低层学习与调度形式在method变体中保留。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "高层选择“去哪”和低层解决“怎么移动”需要的信息与能力不同。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "明确目标接口后可让语义模型处理目标选择、专门控制器处理运动，并由新观察闭环；共享这一认识不代表低层控制器等价。",
      "rationale": {
        "recognition": "高层选择“去哪”和低层解决“怎么移动”需要的信息与能力不同。",
        "explanation": "明确目标接口后可让语义模型处理目标选择、专门控制器处理运动，并由新观察闭环；共享这一认识不代表低层控制器等价。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "imaginenav:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I03-4",
      "challenge_id": "C03",
      "title": "派发前联合检查观测来源、几何与当前任务进度",
      "mechanism": "执行动作前核对该提案所依赖的证据和可行性；动作完成后更新状态，而不直接接受语义计划。",
      "conditions": [
        "工具与证据管理接口可用",
        "检查是作者机制主张，性能贡献受条件化消融约束"
      ],
      "variants": [
        {
          "paper_id": "harnessvln",
          "method_claim": "动作派发前检查来源、几何和子目标，执行后更新事件与时空状态。",
          "evidence_refs": [
            "harnessvln:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "memory→graph→stop累加消融不能独立归因每个检查项。",
          "mechanism_variant": "动作派发前检查来源、几何和子目标，执行后更新事件与时空状态。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "harnessvln:method",
          "variant_id": "I03-4:1"
        }
      ],
      "distinction_from_siblings": "不同于只构造几何候选，还将来源及进度作为派发条件；不把它推成已验证的物理安全保证。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "动作提案正确与否取决于它引用的证据、空间可行性和当前任务状态共同成立。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "派发前对齐这些条件，可阻止缺来源、几何不成立或进度不符的提案直接进入执行；实际贡献仍需条件化证据。",
      "rationale": {
        "recognition": "动作提案正确与否取决于它引用的证据、空间可行性和当前任务状态共同成立。",
        "explanation": "派发前对齐这些条件，可阻止缺来源、几何不成立或进度不符的提案直接进入执行；实际贡献仍需条件化证据。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I04-1",
      "challenge_id": "C04",
      "title": "把相邻进度变化用于行动时前进/回退选择",
      "mechanism": "学习的进度估计不仅是训练辅助，也在决策时触发regret并为已访分支提供标记。",
      "conditions": [
        "可识别视点ID、可执行离散回退",
        "进度估计可能出错"
      ],
      "variants": [
        {
          "paper_id": "ma2019regretful",
          "method_claim": "Regret Module比较相邻进度，Progress Marker给已访方向附估计。",
          "evidence_refs": [
            "ma2019regretful:e1",
            "ma2019regretful:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "R2R离散图；禁用回退不使所有指标下降，不写全面胜出。",
          "mechanism_variant": "Regret Module比较相邻进度，Progress Marker给已访方向附估计。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "ma2019regretful:method",
          "variant_id": "I04-1:1"
        }
      ],
      "distinction_from_siblings": "是局部进度启发式；不等于外部事实核验或基于完整空间图的全局规划。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "走错分支可能先表现为指令完成度倒退，即使尚未到终点。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "把进度估计变化用于行动启发，可在错误积累前触发回退；误估进度也会引发不必要回退。",
      "rationale": {
        "recognition": "走错分支可能先表现为指令完成度倒退，即使尚未到终点。",
        "explanation": "把进度估计变化用于行动启发，可在错误积累前触发回退；误估进度也会引发不必要回退。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I04-2",
      "challenge_id": "C04",
      "title": "显式保留连通图，使回溯有全局可达路径依据",
      "mechanism": "把已访与可行动节点连通性提供给规划/策略，从图中选择下一节点或路线。",
      "conditions": [
        "导航图候选由环境提供或可可靠构建",
        "共享图结构支持回溯，规划器与学习策略不同"
      ],
      "variants": [
        {
          "paper_id": "mapgpt",
          "method_claim": "在线文字拓扑图加上轮多步计划，逐步重规划。",
          "evidence_refs": [
            "mapgpt:pipeline",
            "mapgpt:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "邻接候选来自模拟器；SR增加可伴随更长路径。",
          "mechanism_variant": "在线文字拓扑图加上轮多步计划，逐步重规划。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "mapgpt:method",
          "variant_id": "I04-2:1"
        },
        {
          "paper_id": "navgpt2",
          "method_claim": "拓扑图策略全局选节点并沿最短图路径执行，保留已访与相邻未访节点。",
          "evidence_refs": [
            "navgpt2:e1",
            "navgpt2:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "Q-former与动作policy经训练并使用DUET图方法，非纯提示法。",
          "mechanism_variant": "拓扑图策略全局选节点并沿最短图路径执行，保留已访与相邻未访节点。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "navgpt2:method",
          "variant_id": "I04-2:2"
        }
      ],
      "distinction_from_siblings": "MapGPT与NavGPT-2共用图支撑原则，但不能据此画继承边，亦不能混同提示规划与训练policy。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "恢复路线需要知道已探索节点如何连通，仅记动作序列未必足够。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "显式拓扑使模型能选择可达的旧分支或全局下一节点并获得路径，而不用把所有恢复交给局部贪心选择。",
      "rationale": {
        "recognition": "恢复路线需要知道已探索节点如何连通，仅记动作序列未必足够。",
        "explanation": "显式拓扑使模型能选择可达的旧分支或全局下一节点并获得路径，而不用把所有恢复交给局部贪心选择。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I04-3",
      "challenge_id": "C04",
      "title": "把放弃某分支的理由挂在地点上，回访时按需重读",
      "mechanism": "失败经验不反复塞进全部上下文，而在对应地点再次相关时检索。",
      "conditions": [
        "episode内地点关联记忆",
        "笔记必须被检索才影响决策"
      ],
      "variants": [
        {
          "paper_id": "ham-vln",
          "method_claim": "回退理由附于放弃地点；到相关位置读取，不直接改变得分或禁止访问。",
          "evidence_refs": [
            "ham-vln:e2",
            "ham-vln:e5",
            "ham-vln:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "去反思记忆时仍保留回退，不能把改进全归为新增回退动作。",
          "mechanism_variant": "回退理由附于放弃地点；到相关位置读取，不直接改变得分或禁止访问。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [
            "ham-vln:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "ham-vln:method",
          "variant_id": "I04-3:1"
        }
      ],
      "distinction_from_siblings": "软性地点关联经验，明确不同于HGR级联撤销、TriHelper暂时遮蔽或硬禁止规则。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "一条失败理由通常只在再次考虑对应地点或分支时最有用。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "将反思与地点绑定并按需检索，可在控制上下文长度的同时减少重复误选；笔记本身不是禁止访问规则。",
      "rationale": {
        "recognition": "一条失败理由通常只在再次考虑对应地点或分支时最有用。",
        "explanation": "将反思与地点绑定并按需检索，可在控制上下文长度的同时减少重复误选；笔记本身不是禁止访问规则。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "ham-vln:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I05-1",
      "challenge_id": "C05",
      "title": "对近期交互作有界摘要，并按需要召回原始观察",
      "mechanism": "将常驻输入压到有限历史/摘要，保留选择性访问更早观测的路径。",
      "conditions": [
        "摘要会丢信息；有界文本与可召回图像分开描述"
      ],
      "variants": [
        {
          "paper_id": "navgpt",
          "method_claim": "prompt manager组织视觉文字化观察、历史轨迹与摘要，交替推理/动作。",
          "evidence_refs": [
            "navgpt:pipeline",
            "navgpt:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "作者指出视觉文字化与历史摘要会损失信息；不虚构原图可召回接口。",
          "mechanism_variant": "prompt manager组织视觉文字化观察、历史轨迹与摘要，交替推理/动作。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "navgpt:method",
          "variant_id": "I05-1:1"
        },
        {
          "paper_id": "agenticnav-tool-harness",
          "method_claim": "每步重建有界上下文，保留六步理由记录与按需历史图像查询。",
          "evidence_refs": [
            "agenticnav-tool-harness:e1",
            "agenticnav-tool-harness:pipeline",
            "agenticnav-tool-harness:e3"
          ],
          "relation_to_challenge": "direct",
          "boundary": "进度文本表现差的作者解释不能当已验证一般因果规律。",
          "mechanism_variant": "每步重建有界上下文，保留六步理由记录与按需历史图像查询。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "agenticnav-tool-harness:method",
          "variant_id": "I05-1:2"
        }
      ],
      "distinction_from_siblings": "NavGPT主要压缩表示；AgenticNav额外提供选择性图像召回，二者不是相同完备机制。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "每步都需要部分历史，但不一定需要全部原始交互同样详细地常驻输入。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "近期/摘要可维持基本状态，选择性召回补更早证据；如果只文字化而不可回看，丢失的视觉信息无法由摘要自动恢复。",
      "rationale": {
        "recognition": "每步都需要部分历史，但不一定需要全部原始交互同样详细地常驻输入。",
        "explanation": "近期/摘要可维持基本状态，选择性召回补更早证据；如果只文字化而不可回看，丢失的视觉信息无法由摘要自动恢复。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I05-2",
      "challenge_id": "C05",
      "title": "根据任务、时间和视角动态分配视觉token",
      "mechanism": "直接控制不同历史帧/相机输入的编码粒度，将预算作为可调推理接口。",
      "conditions": [
        "任务参数、相机权重与时间衰减参数给定",
        "启发式配置而非保证最优"
      ],
      "variants": [
        {
          "paper_id": "qwen-robotnav",
          "method_claim": "按时间与相机权重分配有上下限的视觉token。",
          "evidence_refs": [
            "qwen-robotnav:e1",
            "qwen-robotnav:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "500条R2R预算扫描收益非严格单调；不可宣称普适最优分配。",
          "mechanism_variant": "按时间与相机权重分配有上下限的视觉token。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "qwen-robotnav:method",
          "variant_id": "I05-2:1"
        }
      ],
      "distinction_from_siblings": "改变视觉输入粒度，不同于只选择哪些历史项进入LLM。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "不同任务、时刻和相机的视觉细节对当前决策价值不相等。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "把预算按时间与视角分配，可在固定输入资源下保留更有用细节；启发式权重的优劣须依任务验证。",
      "rationale": {
        "recognition": "不同任务、时刻和相机的视觉细节对当前决策价值不相等。",
        "explanation": "把预算按时间与视角分配，可在固定输入资源下保留更有用细节；启发式权重的优劣须依任务验证。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I05-3",
      "challenge_id": "C05",
      "title": "让当前目标决定工作记忆，保留被筛除信息的其他访问通道",
      "mechanism": "按目标/候选相关性筛选历史，而不把全部历史同时用于每步决策。",
      "conditions": [
        "相关性筛选可能漏项",
        "不同任务与记忆结构只共享选择原则"
      ],
      "variants": [
        {
          "paper_id": "li2024memonav",
          "method_claim": "按注意力临时遗忘STM，global node聚合LTM，GATv2构建WM；换目标恢复节点。",
          "evidence_refs": [
            "li2024memonav:e1"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "多目标ImageNav学习策略；节点仍留作定位，存储不减少。",
          "mechanism_variant": "按注意力临时遗忘STM，global node聚合LTM，GATv2构建WM；换目标恢复节点。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "li2024memonav:method",
          "variant_id": "I05-3:1"
        },
        {
          "paper_id": "ham-vln",
          "method_claim": "同次规划返回动作与记忆写入，按相关性、时近性、显著性及一跳拓扑读历史。",
          "evidence_refs": [
            "ham-vln:e1",
            "ham-vln:e4",
            "ham-vln:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "episode内工作窗K=1；token下降不等同总时延或费用下降。",
          "mechanism_variant": "同次规划返回动作与记忆写入，按相关性、时近性、显著性及一跳拓扑读历史。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [
            "ham-vln:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "ham-vln:method",
          "variant_id": "I05-3:2"
        },
        {
          "paper_id": "profocus",
          "method_claim": "BD-MCTS筛航点，检索候选路径相关上下文供决策。",
          "evidence_refs": [
            "profocus:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "路线图导航；不是持续跨episode经验检索。",
          "mechanism_variant": "BD-MCTS筛航点，检索候选路径相关上下文供决策。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "profocus:method",
          "variant_id": "I05-3:3"
        }
      ],
      "distinction_from_siblings": "MemoNav是神经工作记忆筛选，HAM是显式agent读写，ProFocus按搜索候选取上下文；保留三条方法变体而非同名算法。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "可存储的历史和当前需要参与推理的历史不是同一集合。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "用当前目标或候选选择工作记忆，可避免无关历史挤占输入；必须保留回查或聚合途径并检查相关性漏检。",
      "rationale": {
        "recognition": "可存储的历史和当前需要参与推理的历史不是同一集合。",
        "explanation": "用当前目标或候选选择工作记忆，可避免无关历史挤占输入；必须保留回查或聚合途径并检查相关性漏检。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "ham-vln:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I05-4",
      "challenge_id": "C05",
      "title": "以验证完成的局部目标作为压缩边界",
      "mechanism": "只压缩已完成目标段，保留未满足条件及未完成状态，用任务进度定义摘要粒度。",
      "conditions": [
        "存在局部目标与验证回路",
        "修订目标不等于完成目标"
      ],
      "variants": [
        {
          "paper_id": "arxiv:2609.39915",
          "method_claim": "验证完成推进目标并触发完成段压缩，保留关键帧和未完成状态。",
          "evidence_refs": [
            "arxiv:2609.39915:e1",
            "arxiv:2609.39915:e2",
            "arxiv:2609.39915:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "压缩有部分SR/SPL代价；局部输入下降不等于整episode token下降。",
          "mechanism_variant": "验证完成推进目标并触发完成段压缩，保留关键帧和未完成状态。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [
            "arxiv:2609.39915:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "arxiv:2609.39915:method",
          "variant_id": "I05-4:1"
        }
      ],
      "distinction_from_siblings": "摘要边界由验证状态决定，区别于固定窗或任意历史摘要。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "已验证完成的局部任务，比任意时间截断更有明确的压缩边界。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "完成条件成立后才压缩该段，使未来仍可能需要的未满足条件和执行状态不被过早抹去。",
      "rationale": {
        "recognition": "已验证完成的局部任务，比任意时间截断更有明确的压缩边界。",
        "explanation": "完成条件成立后才压缩该段，使未来仍可能需要的未满足条件和执行状态不被过早抹去。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "arxiv:2609.39915:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I05-5",
      "challenge_id": "C05",
      "title": "先保留带来源的任务证据，再压缩工具交互历史",
      "mechanism": "将跨导航调用需要的证据、关键帧和未解目标独立保存，避免长工具记录压缩时一起消失。",
      "conditions": [
        "episode内跨调用取证",
        "证据账本和交互摘要是不同存储职责"
      ],
      "variants": [
        {
          "paper_id": "navmcp",
          "method_claim": "旅程摘要关联关键帧，账本保留正负证据及未解目标。",
          "evidence_refs": [
            "navmcp:e1",
            "navmcp:e2"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "HM-EQA/MT-HM3D/EXPRESS-Bench；EQA答案质量不是ObjectNav SR。",
          "mechanism_variant": "旅程摘要关联关键帧，账本保留正负证据及未解目标。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "navmcp:method",
          "variant_id": "I05-5:1"
        }
      ],
      "distinction_from_siblings": "强调保全可用证据而非仅减少上下文长度；不同于把旧推断自动当事实。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "历史交互可以冗长，支持最终回答的少量证据却不能随压缩一起丢掉。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "先把有来源的证据与未解目标单独保全，再缩短工具轨迹，可维持跨调用取证所需的事实基础。",
      "rationale": {
        "recognition": "历史交互可以冗长，支持最终回答的少量证据却不能随压缩一起丢掉。",
        "explanation": "先把有来源的证据与未解目标单独保全，再缩短工具轨迹，可维持跨调用取证所需的事实基础。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I05-6",
      "challenge_id": "C05",
      "title": "任务所需子图通常小于全场景图，可通过层级检索限制输入规模",
      "mechanism": "利用expand/contract只展开任务相关层级子图，再由外部路径与验证工具处理未放进LLM的低层细节。",
      "conditions": [
        "预建层级场景图",
        "局部内容选择不能丢失满足任务所需的对象与动作前置条件"
      ],
      "variants": [
        {
          "paper_id": "rana2023sayplan",
          "method_claim": "expand/contract操作层级场景图，仅暴露任务相关子图。",
          "evidence_refs": [
            "rana2023sayplan:e1"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "预建静态场景图任务规划；不是在线未知ObjectNav。",
          "mechanism_variant": "expand/contract操作层级场景图，仅暴露任务相关子图。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "rana2023sayplan:method",
          "variant_id": "I05-6:1"
        }
      ],
      "distinction_from_siblings": "通过检索限制文本图规模；与I05-7用图像保留难以文本化的空间关系是不同insight。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "完成一个任务通常只需要巨大场景图中的少量相关对象和关系。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "利用层级检索只暴露相关子图，可减小上下文规模；低层路径与可执行性由外部工具承担，而非把完整图展开到提示里。",
      "rationale": {
        "recognition": "完成一个任务通常只需要巨大场景图中的少量相关对象和关系。",
        "explanation": "利用层级检索只暴露相关子图，可减小上下文规模；低层路径与可执行性由外部工具承担，而非把完整图展开到提示里。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I06-1",
      "challenge_id": "C06",
      "title": "跨目标保留显式空间/实例记录，使再遇目标可直接定位",
      "mechanism": "将先前探索结果放在空间一致的地图或实例记忆中，下一任务继续使用。",
      "conditions": [
        "共享可复用空间经验原则",
        "语义栅格、实例视图与快照不是等价表示"
      ],
      "variants": [
        {
          "paper_id": "krantz2023ivln",
          "method_claim": "MAP-CMA利用tour持久语义/占据地图的自中心裁剪作为导航输入。",
          "evidence_refs": [
            "krantz2023ivln:refresh",
            "krantz2023ivln:e1",
            "krantz2023ivln:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "与latent baselines有训练差异，oracle观察需单列。",
          "mechanism_variant": "MAP-CMA利用tour持久语义/占据地图的自中心裁剪作为导航输入。",
          "mapping_status": "primary_method_rechecked",
          "rationale_anchor_refs": [
            "krantz2023ivln:refresh"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "krantz2023ivln:method",
          "variant_id": "I06-1:1"
        },
        {
          "paper_id": "goat",
          "method_claim": "新目标先查实例记忆，已见实例的位置成为局部导航目标，未命中再探索。",
          "evidence_refs": [
            "goat:refresh"
          ],
          "relation_to_challenge": "direct",
          "boundary": "5–10目标实机序列；类别/描述/图像目标分列。",
          "mechanism_variant": "新目标先查实例记忆，已见实例的位置成为局部导航目标，未命中再探索。",
          "mapping_status": "primary_method_rechecked",
          "rationale_anchor_refs": [
            "goat:refresh"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "goat:method",
          "variant_id": "I06-1:2"
        },
        {
          "paper_id": "goat-bench",
          "method_claim": "benchmark比较持久地图与GRU状态，并提供子任务清空的对照。",
          "evidence_refs": [
            "goat-bench:refresh",
            "goat-bench:e3"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "GOAT baseline是已发表机制的评测实例，不重复计为独立发明。",
          "mechanism_variant": "benchmark比较持久地图与GRU状态，并提供子任务清空的对照。",
          "mapping_status": "primary_method_rechecked",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "goat-bench:protocol",
          "variant_id": "I06-1:3"
        },
        {
          "paper_id": "3d-mem",
          "method_claim": "GOAT子任务间保留3D快照记忆，当前目标从已有snapshot或frontier中选择。",
          "evidence_refs": [
            "3d-mem:pipeline",
            "3d-mem:e2",
            "3d-mem:navmesh"
          ],
          "relation_to_challenge": "direct",
          "boundary": "GOAT主表278子任务子集与全量分开。 实际执行使用global navmesh prior的Habitat pathfinder；替换普通规划器未在本次配置验证。",
          "mechanism_variant": "GOAT子任务间保留3D快照记忆，当前目标从已有snapshot或frontier中选择。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "3d-mem:method",
          "variant_id": "I06-1:4"
        }
      ],
      "distinction_from_siblings": "不声称隐状态普遍无用；该原则不包含如何验证旧记忆仍为真。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "先前任务探索到的区域和实例可能恰是后续目标所需的信息。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "跨目标保留空间一致的记录，让下一任务直接复用已见位置或语义，减少从空白状态搜索；具体收益也可能包含目标匹配改善。",
      "rationale": {
        "recognition": "先前任务探索到的区域和实例可能恰是后续目标所需的信息。",
        "explanation": "跨目标保留空间一致的记录，让下一任务直接复用已见位置或语义，减少从空白状态搜索；具体收益也可能包含目标匹配改善。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "krantz2023ivln:refresh",
          "goat:refresh"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I06-2",
      "challenge_id": "C06",
      "title": "以预测未来状态检索过去相关观察和行为经验",
      "mechanism": "将想象用于构造检索query，分别搜索视点锚定观察库与行为历史库，再与当前导航状态融合。",
      "conditions": [
        "memory-persistent VLN及可用视点锚点",
        "想象是检索线索，不升级为实际环境事实"
      ],
      "variants": [
        {
          "paper_id": "xu2026memoir",
          "method_claim": "想象匹配检索观测与行为历史，扩展DUET的编码分支融合结果。",
          "evidence_refs": [
            "xu2026memoir:e1",
            "xu2026memoir:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "IR2R/GSA-R2R及训练设置分列；不与工具harness作免训练同类比较。",
          "mechanism_variant": "想象匹配检索观测与行为历史，扩展DUET的编码分支融合结果。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "xu2026memoir:method",
          "variant_id": "I06-2:1"
        }
      ],
      "distinction_from_siblings": "与I06-1直接重用已见位置不同，核心是用未来需要检索过去经验。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "与下一步预期需求匹配的过去经历，可能比固定邻域或全库信息更相关。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "用预测未来状态作query选择观察和行为历史，可把检索聚焦到当前将要用到的经验；想象只用于检索，不充当事实。",
      "rationale": {
        "recognition": "与下一步预期需求匹配的过去经历，可能比固定邻域或全库信息更相关。",
        "explanation": "用预测未来状态作query选择观察和行为历史，可把检索聚焦到当前将要用到的经验；想象只用于检索，不充当事实。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I06-3",
      "challenge_id": "C06",
      "title": "把调用长期记忆作为可学习的动作，并给予检索相关训练/评测",
      "mechanism": "允许模型调用记忆检索工具，联合导航、回答及格式奖励学习何时利用历史。",
      "conditions": [
        "多目标探索与目标相关问答",
        "训练时GRPO与单轮检索限制属于机制条件"
      ],
      "variants": [
        {
          "paper_id": "wang2026lmee",
          "method_claim": "MemoryExplorer在GRPO中联合动作/frontier/回答/格式奖励，调用CLIP记忆检索。",
          "evidence_refs": [
            "wang2026lmee:e1",
            "wang2026lmee:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "LMEE基准与MemoryExplorer模型两角色；推理慢，voxel不支持多层。",
          "mechanism_variant": "MemoryExplorer在GRPO中联合动作/frontier/回答/格式奖励，调用CLIP记忆检索。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "wang2026lmee:method",
          "variant_id": "I06-3:1"
        }
      ],
      "distinction_from_siblings": "不只是增加一个存储库，而是训练使用记忆的行为；结果仍需辨别导航与QA指标。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "存了记忆不代表策略知道何时调用，导航总分也不直接显示是否用到了历史。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "把检索作为模型动作并给相关任务训练信号，使记忆使用本身可学习；问答与导航仍需分别评价。",
      "rationale": {
        "recognition": "存了记忆不代表策略知道何时调用，导航总分也不直接显示是否用到了历史。",
        "explanation": "把检索作为模型动作并给相关任务训练信号，使记忆使用本身可学习；问答与导航仍需分别评价。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I06-4",
      "challenge_id": "C06",
      "title": "按时间/空间/语义条件多轮检索长历史",
      "mechanism": "记忆构建与在线问答分开，以工具检索而不是全库注入处理长时段记录。",
      "conditions": [
        "长历史定位/QA邻近任务",
        "可返回导航目标不等于测到端到端导航成功"
      ],
      "variants": [
        {
          "paper_id": "anwar2025remembr",
          "method_claim": "检索文本、时间、位置条件，迭代后输出结构化答案与坐标。",
          "evidence_refs": [
            "anwar2025remembr:e1",
            "anwar2025remembr:e2"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "NaVQA视频与实机部署说明；主要统计QA与时空定位。",
          "mechanism_variant": "检索文本、时间、位置条件，迭代后输出结构化答案与坐标。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "anwar2025remembr:method",
          "variant_id": "I06-4:1"
        }
      ],
      "distinction_from_siblings": "与主动导航中的跨目标记忆复用相邻，但任务输出和评测终点不同。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "长历史问答常由少数带时间/位置约束的片段决定，无需一次全部注入。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "多轮工具检索逐渐缩小相关证据集合，可支持长时段定位和推理；caption遗漏仍可能让目标证据不可检索。",
      "rationale": {
        "recognition": "长历史问答常由少数带时间/位置约束的片段决定，无需一次全部注入。",
        "explanation": "多轮工具检索逐渐缩小相关证据集合，可支持长时段定位和推理；caption遗漏仍可能让目标证据不可检索。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I06-5",
      "challenge_id": "C06",
      "title": "恢复会话时传递可追溯搜索状态与剩余预算",
      "mechanism": "将任务记录与长期房屋知识分层，交接已搜区域、有证据排除的项和未解决目标。",
      "conditions": [
        "连续目标/恢复会话",
        "原任务记录不能被后继会话覆盖；预算不重置"
      ],
      "variants": [
        {
          "paper_id": "navharness",
          "method_claim": "恢复保留剩余任务预算，区分已搜索和有证据排除，原任务记录不可覆写。",
          "evidence_refs": [
            "navharness:e1",
            "navharness:e2",
            "navharness:e3"
          ],
          "relation_to_challenge": "direct",
          "boundary": "2609.34276 Lifelong；静态模拟、judge可能误判，占据图回环不自动校正。",
          "mechanism_variant": "恢复保留剩余任务预算，区分已搜索和有证据排除，原任务记录不可覆写。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "navharness:method",
          "variant_id": "I06-5:1"
        }
      ],
      "distinction_from_siblings": "会话边界的交接协议，不能与2609.39915局部目标压缩合并成一篇NavHarness。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "重新开始一个推理会话，不应重置环境经验、剩余预算或未解决问题。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "交接可追溯搜索状态与预算可接续工作，区分已搜和已排除有助于避免把旧判断当事实。",
      "rationale": {
        "recognition": "重新开始一个推理会话，不应重置环境经验、剩余预算或未解决问题。",
        "explanation": "交接可追溯搜索状态与预算可接续工作，区分已搜和已排除有助于避免把旧判断当事实。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I07-1",
      "challenge_id": "C07",
      "title": "观测与推测分开保存，并记录可撤回的推导依赖",
      "mechanism": "维护与导航连通图不同的假设依赖DAG，验证反驳一个假设时撤回传递依赖。",
      "conditions": [
        "存在显式语义假设及现场验证",
        "导航边与逻辑依赖边不可混用"
      ],
      "variants": [
        {
          "paper_id": "hypothesis-graph-refinement",
          "method_claim": "验证失败删除该假设及传递依赖节点，避免错误预测持续传播。",
          "evidence_refs": [
            "hypothesis-graph-refinement:e1",
            "hypothesis-graph-refinement:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "A-EQA/EM-EQA/GOAT不同任务分开；重实现baseline与原版不等价。",
          "mechanism_variant": "验证失败删除该假设及传递依赖节点，避免错误预测持续传播。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [
            "hypothesis-graph-refinement:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "hypothesis-graph-refinement:method",
          "variant_id": "I07-1:1"
        }
      ],
      "distinction_from_siblings": "真正处理推论的级联撤销，不等于普通记忆摘要、黑名单或记录失败理由。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "错误预测的危害不仅是自身置信度，还在于依赖它产生的后续结论。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "仅降低原节点置信度会留下错误子图；记录依赖并级联撤回，才能同步取消建立在被反驳前提上的推断。",
      "rationale": {
        "recognition": "错误预测的危害不仅是自身置信度，还在于依赖它产生的后续结论。",
        "explanation": "仅降低原节点置信度会留下错误子图；记录依赖并级联撤回，才能同步取消建立在被反驳前提上的推断。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "hypothesis-graph-refinement:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I07-2",
      "challenge_id": "C07",
      "title": "负面记录保留可追溯依据，避免把未见写成永久排除",
      "mechanism": "交接时标明搜过与有证据排除的差别，并保留原始任务记录供后续修正。",
      "conditions": [
        "跨恢复会话的搜索记录",
        "有证据排除仍可能受judge误判影响"
      ],
      "variants": [
        {
          "paper_id": "navharness",
          "method_claim": "任务交接区分已搜索与有证据排除，后继会话不能覆盖原任务记录。",
          "evidence_refs": [
            "navharness:e1",
            "navharness:e3"
          ],
          "relation_to_challenge": "direct",
          "boundary": "不自动解决SLAM回环导致旧地图坐标不一致。",
          "mechanism_variant": "任务交接区分已搜索与有证据排除，后继会话不能覆盖原任务记录。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "navharness:method",
          "variant_id": "I07-2:1"
        }
      ],
      "distinction_from_siblings": "管理证据地位和来源，不声称具备HGR的逻辑依赖级联删除。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "没有找到目标，不等于已经拥有目标不存在的证据。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "把搜索经历和有根据的排除分开，并保留来源，使下一会话能重新评估不完整或冲突的旧判断。",
      "rationale": {
        "recognition": "没有找到目标，不等于已经拥有目标不存在的证据。",
        "explanation": "把搜索经历和有根据的排除分开，并保留来源，使下一会话能重新评估不完整或冲突的旧判断。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I07-3",
      "challenge_id": "C07",
      "title": "对疑似误检暂时抑制，保留条件性重新访问",
      "mechanism": "发现检测可能错误时暂时屏蔽该候选，搜索仍失败时允许回查，避免永久误排。",
      "conditions": [
        "episode内目标检测失败",
        "遮蔽是启发式控制策略"
      ],
      "variants": [
        {
          "paper_id": "trihelper",
          "method_claim": "误检目标记录被遮蔽；超过阈值未找到目标可回到记录点。",
          "evidence_refs": [
            "trihelper:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "作者亦报告遮蔽可能引发失败；不能作为可靠负证据保证。",
          "mechanism_variant": "误检目标记录被遮蔽；超过阈值未找到目标可回到记录点。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "trihelper:method",
          "variant_id": "I07-3:1"
        }
      ],
      "distinction_from_siblings": "相较永久黑名单有恢复入口；与SAP-Nav经主动观察后拒绝候选的语义也不同。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "疑似误检需要抑制，但一次判断也可能错，永久排除会封死恢复机会。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "暂时屏蔽加条件性回查可在减少重复误检与避免错过真目标之间折中；阈值会带来新的失败。",
      "rationale": {
        "recognition": "疑似误检需要抑制，但一次判断也可能错，永久排除会封死恢复机会。",
        "explanation": "暂时屏蔽加条件性回查可在减少重复误检与避免错过真目标之间折中；阈值会带来新的失败。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I07-4",
      "challenge_id": "C07",
      "title": "以新观测、执行结果或人工纠正触发局部状态更新",
      "mechanism": "让空间记忆随物理执行事件更新，而非只追加自然语言历史。",
      "conditions": [
        "异构机器人技能有结构化反馈",
        "事件更新与依赖追踪是不同能力"
      ],
      "variants": [
        {
          "paper_id": "holoagent-0",
          "method_claim": "新观测、物体操作结果或用户纠正触发局部记忆更新。",
          "evidence_refs": [
            "holoagent-0:e1"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "静态导航定量与全技能定性分开，未证明长期动态适应。",
          "mechanism_variant": "新观测、物体操作结果或用户纠正触发局部记忆更新。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "holoagent-0:method",
          "variant_id": "I07-4:1"
        }
      ],
      "distinction_from_siblings": "修正当前状态的机制，不据此推断完整长期知识库纠错或任意动态场景一致性。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "执行会改变环境或揭示旧记忆错误，只累加历史不能保证当前状态正确。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "由新观测与结构化执行结果触发局部更新，可把当前物理状态反馈到记忆；不等于完整因果依赖修复。",
      "rationale": {
        "recognition": "执行会改变环境或揭示旧记忆错误，只累加历史不能保证当前状态正确。",
        "explanation": "由新观测与结构化执行结果触发局部更新，可把当前物理状态反馈到记忆；不等于完整因果依赖修复。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I08-1",
      "challenge_id": "C08",
      "title": "把STOP提案与语义、几何和进度证据交叉核对",
      "mechanism": "对停止请求实施独立于提案的检查步骤，避免只凭一次目标语义匹配终止。",
      "conditions": [
        "可核对当前证据来源与几何",
        "收益需要独立于其他模块变化解释"
      ],
      "variants": [
        {
          "paper_id": "harnessvln",
          "method_claim": "停止请求另验语义、几何和进度。",
          "evidence_refs": [
            "harnessvln:e1",
            "harnessvln:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "100 episode累加消融不是完整析因；不能隔离所有模块贡献。",
          "mechanism_variant": "停止请求另验语义、几何和进度。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "harnessvln:method",
          "variant_id": "I08-1:1"
        }
      ],
      "distinction_from_siblings": "比重复询问STOP包含更多显式检查条件，但不是跨论文最优结论。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "看到类似目标或表达想停，尚不足以证明任务规定的完成条件成立。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "语义、几何、进度及来源交叉检查能识别不同的虚假完成情形；验证器也可能误判，不能视为真值。",
      "rationale": {
        "recognition": "看到类似目标或表达想停，尚不足以证明任务规定的完成条件成立。",
        "explanation": "语义、几何、进度及来源交叉检查能识别不同的虚假完成情形；验证器也可能误判，不能视为真值。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I08-2",
      "challenge_id": "C08",
      "title": "把未满足条件返回局部目标，只有验证完成才推进",
      "mechanism": "Goal/Verify/Visuomotor/Memory角色用观察结果判断继续、修订或推进，并保留未完成状态。",
      "conditions": [
        "连续局部目标式VLN",
        "修订与完成的状态转移明确区分"
      ],
      "variants": [
        {
          "paper_id": "arxiv:2609.39915",
          "method_claim": "验证返回未满足条件；修订不算完成，完成后推进并触发压缩。",
          "evidence_refs": [
            "arxiv:2609.39915:e1",
            "arxiv:2609.39915:e2",
            "arxiv:2609.39915:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "框架消融未分别隔离目标与验证；实机样本较小。",
          "mechanism_variant": "验证返回未满足条件；修订不算完成，完成后推进并触发压缩。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [
            "arxiv:2609.39915:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "arxiv:2609.39915:method",
          "variant_id": "I08-2:1"
        }
      ],
      "distinction_from_siblings": "侧重局部目标闭环状态机；并不等于每次最终STOP都有独立语义/几何检查。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "连续局部动作即便各自合理，累积后仍可能偏离指令预期路线。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "以明确局部完成条件核对实际观察，并区分继续、修订和推进，使状态转移以结果为依据。",
      "rationale": {
        "recognition": "连续局部动作即便各自合理，累积后仍可能偏离指令预期路线。",
        "explanation": "以明确局部完成条件核对实际观察，并区分继续、修订和推进，使状态转移以结果为依据。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "arxiv:2609.39915:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I08-3",
      "challenge_id": "C08",
      "title": "对STOP采用重复确认或任务状态触发规则",
      "mechanism": "用明确的终止规则降低单步决策任意性，但规则本身仍可能误判。",
      "conditions": [
        "停止输出可以单独调用或由指令状态触发",
        "不同启发式应作为独立变体比较"
      ],
      "variants": [
        {
          "paper_id": "vlmnav",
          "method_claim": "连续两次STOP才终止，首次STOP后去掉探索偏置。",
          "evidence_refs": [
            "vlmnav:e1",
            "vlmnav:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "这是重复确认，不是几何充分性证明。",
          "mechanism_variant": "连续两次STOP才终止，首次STOP后去掉探索偏置。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "vlmnav:method",
          "variant_id": "I08-3:1"
        },
        {
          "paper_id": "instructnav",
          "method_claim": "DCoN Flag或VLM判断可触发停止。",
          "evidence_refs": [
            "instructnav:e1",
            "instructnav:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "OR式触发与两次确认不是相同机制；本次未核独立stop消融。",
          "mechanism_variant": "DCoN Flag或VLM判断可触发停止。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "instructnav:method",
          "variant_id": "I08-3:2"
        }
      ],
      "distinction_from_siblings": "属于终止策略，可收在共同问题下但不写成相同验证洞见。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "单次终止判断容易受瞬时观察或探索偏置影响。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "重复确认或显式任务状态规则为终止增加门槛，但重复同一错误并不会自动产生新证据，两种方法的可靠性不能合并。",
      "rationale": {
        "recognition": "单次终止判断容易受瞬时观察或探索偏置影响。",
        "explanation": "重复确认或显式任务状态规则为终止增加门槛，但重复同一错误并不会自动产生新证据，两种方法的可靠性不能合并。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I08-4",
      "challenge_id": "C08",
      "title": "显式估计已完成、进行中和待执行动作再做决策",
      "mechanism": "把指令、感知和完成估计拆成固定讨论职责，候选不一致时增加决策检验。",
      "conditions": [
        "VLN多步指令跟踪",
        "完成估计本身不是独立物理证据"
      ],
      "variants": [
        {
          "paper_id": "discussnav",
          "method_claim": "轨迹摘要和完成估计反馈进入动作决策，五路候选不一致时交决策检验。",
          "evidence_refs": [
            "discussnav:e1",
            "discussnav:pipeline"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "角色不代表独立模型；多次调用成本必须计入。",
          "mechanism_variant": "轨迹摘要和完成估计反馈进入动作决策，五路候选不一致时交决策检验。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "discussnav:method",
          "variant_id": "I08-4:1"
        }
      ],
      "distinction_from_siblings": "帮助显式进度推理，但不能标为已解决“实际完成”的证据核验。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "指令理解、视觉判断和进度跟踪的错误可能在一次整体推理中相互掩盖。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "分开讨论并在候选冲突时检验，可显式暴露不一致；完成估计仍只是模型判断，未成为物理事实。",
      "rationale": {
        "recognition": "指令理解、视觉判断和进度跟踪的错误可能在一次整体推理中相互掩盖。",
        "explanation": "分开讨论并在候选冲突时检验，可显式暴露不一致；完成估计仍只是模型判断，未成为物理事实。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I09-1",
      "challenge_id": "C09",
      "title": "在已有全景中按语义需求主动查询局部区域",
      "mechanism": "先识别缺失信息，再针对当前图像区域进行视觉查询，信息充分后做导航候选推理。",
      "conditions": [
        "当前全景已经可用",
        "信息动作是裁剪/查询，不一定发生物理移动"
      ],
      "variants": [
        {
          "paper_id": "profocus",
          "method_claim": "局部视觉查询循环针对当前全景裁剪，编排代理判断信息是否充分。",
          "evidence_refs": [
            "profocus:e1",
            "profocus:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "REVERIE只评导航不评grounding；不可宣称真实移动主动感知效果。",
          "mechanism_variant": "局部视觉查询循环针对当前全景裁剪，编排代理判断信息是否充分。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "profocus:method",
          "variant_id": "I09-1:1"
        }
      ],
      "distinction_from_siblings": "与移动到新视点不同，需独立计视觉模型调用开销。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "当前图像可能已经包含所需线索，障碍在于尚未聚焦正确区域。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "按缺失语义查询裁剪可以补充决策细节，无需总先做物理移动；视野外信息不能靠裁剪获得。",
      "rationale": {
        "recognition": "当前图像可能已经包含所需线索，障碍在于尚未聚焦正确区域。",
        "explanation": "按缺失语义查询裁剪可以补充决策细节，无需总先做物理移动；视野外信息不能靠裁剪获得。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I09-2",
      "challenge_id": "C09",
      "title": "按观察充分性选择真实新视点后再验候选",
      "mechanism": "评估角度与可见性是否足够辨认目标，必要时移动，采用充分性更好的观察决定接受或拒绝。",
      "conditions": [
        "候选物体已提出但属性/关系不清",
        "移动可增加路径长度"
      ],
      "variants": [
        {
          "paper_id": "sap-nav",
          "method_claim": "AVV最多三次换位，以最高充分性视图验证；拒绝候选入黑名单。",
          "evidence_refs": [
            "sap-nav:e1",
            "sap-nav:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "房间约束与实例属性目标；定性实机例不等于量化实机SR。",
          "mechanism_variant": "AVV最多三次换位，以最高充分性视图验证；拒绝候选入黑名单。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "sap-nav:method",
          "variant_id": "I09-2:1"
        }
      ],
      "distinction_from_siblings": "针对目标候选的充分性检查；不同于一般信息增益探索或重复STOP。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "候选目标的属性或关系是否可判断，取决于视角和可见程度。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "先改善观察充分性再验目标，有望减少把看不清误当不符合；代价是额外移动和路径。",
      "rationale": {
        "recognition": "候选目标的属性或关系是否可判断，取决于视角和可见程度。",
        "explanation": "先改善观察充分性再验目标，有望减少把看不清误当不符合；代价是额外移动和路径。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I09-3",
      "challenge_id": "C09",
      "title": "按终局决策损失降低与路程代价选择视点",
      "mechanism": "让可见性预测和支持几何进入下一视点选择及选择性决策，输出存在判断需跨位置一致支持。",
      "conditions": [
        "固定预算离散视点图上的类别存在判断",
        "可见性模型与决策头经过训练/校准"
      ],
      "variants": [
        {
          "paper_id": "safevantage",
          "method_claim": "按预期决策损失下降及路程成本选视点，Yes需来自不同位置的几何一致支持。",
          "evidence_refs": [
            "safevantage:e1",
            "safevantage:e2"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "category-presence macro-F1不是导航SR；连续执行与实机尚属后续评估。",
          "mechanism_variant": "按预期决策损失下降及路程成本选视点，Yes需来自不同位置的几何一致支持。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "safevantage:method",
          "variant_id": "I09-3:1"
        }
      ],
      "distinction_from_siblings": "与SAP-Nav同样关注证据充分性，但目标函数、训练及输出任务不同，不能据分数判谁导航更好。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "更好的下一视点应改善最终判别，而不只提高语义相似度或覆盖率。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "把预计决策损失下降与移动成本联系，并要求跨位置几何一致支持，可使取景服务于是否可作答；结论限该存在判断任务。",
      "rationale": {
        "recognition": "更好的下一视点应改善最终判别，而不只提高语义相似度或覆盖率。",
        "explanation": "把预计决策损失下降与移动成本联系，并要求跨位置几何一致支持，可使取景服务于是否可作答；结论限该存在判断任务。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I09-4",
      "challenge_id": "C09",
      "title": "终点观察不足以支撑长程取证，沿途证据也必须跨调用保留",
      "mechanism": "把未解证据需求变为带模式、子目标、预算的导航调用，并返还关联关键帧的旅程证据。",
      "conditions": [
        "主动取证任务或探索阶段",
        "不同任务集与底层导航工具需分别标注"
      ],
      "variants": [
        {
          "paper_id": "navmcp",
          "method_claim": "导航调用带模式、子目标、预算；返回关联关键帧的旅程证据并更新未解目标。",
          "evidence_refs": [
            "navmcp:e1",
            "navmcp:e2"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "仅保留终点观察的消融与整套接口消融不同，不当作memory-only因果证据。",
          "mechanism_variant": "导航调用带模式、子目标、预算；返回关联关键帧的旅程证据并更新未解目标。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "navmcp:method",
          "variant_id": "I09-4:1"
        }
      ],
      "distinction_from_siblings": "这是取证调用和观察返回接口的认识；与I09-5同时呈现已知/未知视觉空间的记忆表示不同。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "取证问题需要的线索可能在导航途中出现，而不在调用终点。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "导航接口返回旅程证据并保留未解需求，可让上层根据仍缺什么继续派发取证，而不丢掉路过的观察。",
      "rationale": {
        "recognition": "取证问题需要的线索可能在导航途中出现，而不在调用终点。",
        "explanation": "导航接口返回旅程证据并保留未解需求，可让上层根据仍缺什么继续派发取证，而不丢掉路过的观察。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I10-1",
      "challenge_id": "C10",
      "title": "按失败类型触发不同的局部恢复机制",
      "mechanism": "碰撞/不可达、重复搜索及疑似检测错误不共享一个重规划提示，而采用针对性辅助。",
      "conditions": [
        "可诊断失败类型",
        "启发式组合需检查交互效应"
      ],
      "variants": [
        {
          "paper_id": "trihelper",
          "method_claim": "不可达或碰撞改向最大连通区中心；重复近目标使LM暂眠；误检屏蔽后再探索。",
          "evidence_refs": [
            "trihelper:pipeline",
            "trihelper:e1",
            "trihelper:e2",
            "trihelper:rationale"
          ],
          "relation_to_challenge": "direct",
          "boundary": "三个helper并用时探索失败反增，不能假定组合单调受益。",
          "mechanism_variant": "不可达或碰撞改向最大连通区中心；重复近目标使LM暂眠；误检屏蔽后再探索。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [
            "trihelper:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "trihelper:method",
          "variant_id": "I10-1:1"
        }
      ],
      "distinction_from_siblings": "是具体失败分型恢复，不是抽象“加反馈就更可靠”。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "碰撞、重复低效搜索和误检是不同失败来源，统一重试无法针对其原因。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "按失败类型提供辅助机制可分别改变运动目标、语义搜索介入和检测处理；组合后仍要检查失败类型转移。",
      "rationale": {
        "recognition": "碰撞、重复低效搜索和误检是不同失败来源，统一重试无法针对其原因。",
        "explanation": "按失败类型提供辅助机制可分别改变运动目标、语义搜索介入和检测处理；组合后仍要检查失败类型转移。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "trihelper:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I10-2",
      "challenge_id": "C10",
      "title": "执行失败回到短程计划/目标并用新观察修订",
      "mechanism": "把失败反馈交还上层，改变局部目标、补观察或重规划，再执行新的动作。",
      "conditions": [
        "在线更新目标与环境表示",
        "各方法的失败判定器不同，不能合并成已验证公共模块"
      ],
      "variants": [
        {
          "paper_id": "instructnav",
          "method_claim": "无可导航点时反馈给视觉模型重预测，同时屏蔽障碍。",
          "evidence_refs": [
            "instructnav:e1",
            "instructnav:pipeline"
          ],
          "relation_to_challenge": "direct",
          "boundary": "语义图受遮挡影响；不保证每类失败都能恢复。",
          "mechanism_variant": "无可导航点时反馈给视觉模型重预测，同时屏蔽障碍。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "instructnav:method",
          "variant_id": "I10-2:1"
        },
        {
          "paper_id": "rajvanshi2024saynav",
          "method_claim": "navigate/look与PointNav反馈用于更新计划、探索或补观察。",
          "evidence_refs": [
            "rajvanshi2024saynav:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "完整计划验证被作者列为未来工作；可能重复尝试看不到的门状态。",
          "mechanism_variant": "navigate/look与PointNav反馈用于更新计划、探索或补观察。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "rajvanshi2024saynav:method",
          "variant_id": "I10-2:2"
        },
        {
          "paper_id": "arxiv:2609.39915",
          "method_claim": "观察验证未完成时继续或修订局部目标，修订不算完成。",
          "evidence_refs": [
            "arxiv:2609.39915:e1"
          ],
          "relation_to_challenge": "direct",
          "boundary": "局部目标重设与最终成功验证是不同评估环节。",
          "mechanism_variant": "观察验证未完成时继续或修订局部目标，修订不算完成。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "arxiv:2609.39915:method",
          "variant_id": "I10-2:3"
        }
      ],
      "distinction_from_siblings": "共享短闭环修订原则，分别保留重预测、短期计划调整与Goal/Verify状态机。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "执行失败说明当前局部计划不适用，未必说明整个任务目标错误。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "把失败反馈回短程计划，并补观察或调整子目标，可在保留任务意图的同时改变不可执行步骤。",
      "rationale": {
        "recognition": "执行失败说明当前局部计划不适用，未必说明整个任务目标错误。",
        "explanation": "把失败反馈回短程计划，并补观察或调整子目标，可在保留任务意图的同时改变不可执行步骤。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I10-3",
      "challenge_id": "C10",
      "title": "让技能接口返回结构化执行状态供调度器处理",
      "mechanism": "动作调用不仅返回文本，还携带进度、结果等状态，使监控/重规划能依据执行结果。",
      "conditions": [
        "异构物理技能具有统一接口",
        "技能可靠性需要逐项及系统级证据"
      ],
      "variants": [
        {
          "paper_id": "holoagent-0",
          "method_claim": "typed技能接口和ROS2状态总线支撑技能调度、反馈及记忆事件更新。",
          "evidence_refs": [
            "holoagent-0:e1",
            "holoagent-0:pipeline",
            "holoagent-0:e2"
          ],
          "relation_to_challenge": "direct",
          "boundary": "全技能演示无统一端到端成功率，不能宣称全栈可靠。",
          "mechanism_variant": "typed技能接口和ROS2状态总线支撑技能调度、反馈及记忆事件更新。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "holoagent-0:method",
          "variant_id": "I10-3:1"
        }
      ],
      "distinction_from_siblings": "接口级可观察执行，不是仅在模型提示里要求自我反思。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "上层只有知道技能实际做到哪一步，才能区分继续等待、局部失败和需要重规划。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "结构化技能状态比孤立调用文本更便于调度和更新记忆；接口存在不代表状态估计总正确。",
      "rationale": {
        "recognition": "上层只有知道技能实际做到哪一步，才能区分继续等待、局部失败和需要重规划。",
        "explanation": "结构化技能状态比孤立调用文本更便于调度和更新记忆；接口存在不代表状态估计总正确。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I10-4",
      "challenge_id": "C10",
      "title": "在执行前用外部图模拟器检查计划前置条件",
      "mechanism": "为计划补齐低层路径，并让符号环境验证可执行性；返回失败信息后重规划。",
      "conditions": [
        "预建、静态场景图与可模拟动作",
        "这是执行前计划检查，不是实际失败后的传感器验证"
      ],
      "variants": [
        {
          "paper_id": "rana2023sayplan",
          "method_claim": "Dijkstra补路径，verify_plan图模拟器返回失败信息，触发重规划。",
          "evidence_refs": [
            "rana2023sayplan:e1",
            "rana2023sayplan:e2"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "图可执行不保证感知真实、物理安全或最终任务正确。",
          "mechanism_variant": "Dijkstra补路径，verify_plan图模拟器返回失败信息，触发重规划。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "rana2023sayplan:method",
          "variant_id": "I10-4:1"
        }
      ],
      "distinction_from_siblings": "与真实执行反馈不同，只作为相邻的前置条件检查支路。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "长计划可能在语义上合理，却违反图中动作前置条件或缺少连接路径。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "外部路径补全与符号验证可在执行前定位这种失败并反馈；真实感知和物理可行性仍在其保证范围外。",
      "rationale": {
        "recognition": "长计划可能在语义上合理，却违反图中动作前置条件或缺少连接路径。",
        "explanation": "外部路径补全与符号验证可在执行前定位这种失败并反馈；真实感知和物理可行性仍在其保证范围外。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I11-1",
      "challenge_id": "C11",
      "title": "把ObjectNav成功显式拆成意图、可达性、接近与可见性",
      "mechanism": "先定义类别目标、合法本体位置及成功区域，再报告成功与路径效率，明确可见性是否为oracle。",
      "conditions": [
        "指定类别任一实例ObjectNav",
        "距离/可见性口径需由具体benchmark明确"
      ],
      "variants": [
        {
          "paper_id": "batra2020objectnav",
          "method_claim": "成功分STOP意图、位置合法、距物体表面与可见性；oracle-visibility作为不同选择。",
          "evidence_refs": [
            "batra2020objectnav:refresh",
            "batra2020objectnav:e2",
            "batra2020objectnav:e3"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "论文建议不代表所有后续实现采用完全一致细则。",
          "mechanism_variant": "成功分STOP意图、位置合法、距物体表面与可见性；oracle-visibility作为不同选择。",
          "mapping_status": "primary_protocol_rechecked",
          "rationale_anchor_refs": [
            "batra2020objectnav:refresh"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "batra2020objectnav:protocol",
          "variant_id": "I11-1:1"
        }
      ],
      "distinction_from_siblings": "提供成功的操作化定义，不是“harness应多记录日志”这一编者扩展建议。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "ObjectNav一句“到目标附近”不足以唯一确定成功或比较算法。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "显式定义意图、位置合法、目标距离和可见性，使不同结果的前提可识别，而不让本体和oracle差异藏在总分里。",
      "rationale": {
        "recognition": "ObjectNav一句“到目标附近”不足以唯一确定成功或比较算法。",
        "explanation": "显式定义意图、位置合法、目标距离和可见性，使不同结果的前提可识别，而不让本体和oracle差异藏在总分里。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "batra2020objectnav:refresh"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I11-2",
      "challenge_id": "C11",
      "title": "移除预定义导航图与短程oracle，在连续空间评价低层动作",
      "mechanism": "将R2R任务转成连续可导航空间，明确观测与转向/前进/STOP动作接口，以暴露真实执行难度。",
      "conditions": [
        "R2R转换为VLN-CE",
        "continuous指可导航空间，不一定是连续值动作"
      ],
      "variants": [
        {
          "paper_id": "krantz2020vlnce",
          "method_claim": "不提供位置/朝向或导航图、短程oracle；低层前进/转向/STOP决策。",
          "evidence_refs": [
            "krantz2020vlnce:e1",
            "krantz2020vlnce:e2",
            "krantz2020vlnce:e3"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "图/连续对比受轨迹筛除和转换误差影响，原始SPL不可直接排名。",
          "mechanism_variant": "不提供位置/朝向或导航图、短程oracle；低层前进/转向/STOP决策。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "krantz2020vlnce:protocol",
          "variant_id": "I11-2:1"
        }
      ],
      "distinction_from_siblings": "协议把执行责任交给agent；不能据此认定所有后续VLN-CE系统使用同样低层帮助。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "给定导航图及短程oracle已替agent承担一部分空间执行问题。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "将评测移到连续可导航空间并要求低层动作，可检验原图任务未暴露的运动与观察困难；转换误差仍需单列。",
      "rationale": {
        "recognition": "给定导航图及短程oracle已替agent承担一部分空间执行问题。",
        "explanation": "将评测移到连续可导航空间并要求低层动作，可检验原图任务未暴露的运动与观察困难；转换误差仍需单列。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I11-3",
      "challenge_id": "C11",
      "title": "对长多目标任务固定实际接续与分项成本口径",
      "mechanism": "连续子任务保留实际位置，按每个子目标的目标形式、预算和真实起点计算结果。",
      "conditions": [
        "同环境多模态子目标序列",
        "不将理想上一目标位置当下一段实际起点"
      ],
      "variants": [
        {
          "paper_id": "goat-bench",
          "method_claim": "子任务SPL最短路从上一子任务实际结束位置起算，固定STOP及预算等协议。",
          "evidence_refs": [
            "goat-bench:e1",
            "goat-bench:e2",
            "goat-bench:refresh"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "Habitat/Stretch模拟，不能与Spot实机协议直接合并。",
          "mechanism_variant": "子任务SPL最短路从上一子任务实际结束位置起算，固定STOP及预算等协议。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "goat-bench:protocol",
          "variant_id": "I11-3:1"
        },
        {
          "paper_id": "goat",
          "method_claim": "实机5–10目标序列按每目标成功和SPL报告，并明确STOP及距离阈值。",
          "evidence_refs": [
            "goat:e2",
            "goat:refresh"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "本体控制器不同；实机15类不等同开放词汇任意类别实证。",
          "mechanism_variant": "实机5–10目标序列按每目标成功和SPL报告，并明确STOP及距离阈值。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "goat:protocol",
          "variant_id": "I11-3:2"
        }
      ],
      "distinction_from_siblings": "这是多目标接续与成本定义，不等同证明某个记忆模块产生全部收益。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "多目标任务的上一段实际结束位置决定下一段真实难度。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "以真实接续位置和分目标成本计算结果，避免把恢复或失败造成的起点变化从评测中隐去。",
      "rationale": {
        "recognition": "多目标任务的上一段实际结束位置决定下一段真实难度。",
        "explanation": "以真实接续位置和分目标成本计算结果，避免把恢复或失败造成的起点变化从评测中隐去。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I12-1",
      "challenge_id": "C12",
      "title": "以记忆生命周期和条件化重置实验检验复用作用",
      "mechanism": "使用episode/tour重置或每子目标清空等受控变化，区分保留已有经验与单任务能力。",
      "conditions": [
        "固定模型/训练或明确训练模式交叉差异",
        "重置实验不等同所有记忆设计的普遍因果结论"
      ],
      "variants": [
        {
          "paper_id": "krantz2023ivln",
          "method_claim": "比较episode重置、tour保留与known map，并交叉训练/评测模式。",
          "evidence_refs": [
            "krantz2023ivln:e2",
            "krantz2023ivln:e3",
            "krantz2023ivln:refresh"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "oracle观察及DAgger训练差异需保留，不能说地图单一因果优势。",
          "mechanism_variant": "比较episode重置、tour保留与known map，并交叉训练/评测模式。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [
            "krantz2023ivln:refresh"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "krantz2023ivln:protocol",
          "variant_id": "I12-1:1"
        },
        {
          "paper_id": "goat-bench",
          "method_claim": "每子任务清空GOAT地图或monolithic隐状态，并按目标模态分析。",
          "evidence_refs": [
            "goat-bench:refresh",
            "goat-bench:e3"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "同一干预可同时影响路线复用及实例匹配；不把总收益全归路线记忆。",
          "mechanism_variant": "每子任务清空GOAT地图或monolithic隐状态，并按目标模态分析。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [
            "goat-bench:refresh"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "goat-bench:protocol",
          "variant_id": "I12-1:2"
        }
      ],
      "distinction_from_siblings": "恢复“记忆何时保留/清空”的作者实验洞见，与旧记录里的编者测量建议分开。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "长期任务得分包含单任务能力和以往经验复用，两者不能仅由总分拆开。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "在固定或明确训练条件下改变记忆生命周期，可直接观察同一策略是否依赖先前经验；重置同时影响识别与路径时需保留歧义。",
      "rationale": {
        "recognition": "长期任务得分包含单任务能力和以往经验复用，两者不能仅由总分拆开。",
        "explanation": "在固定或明确训练条件下改变记忆生命周期，可直接观察同一策略是否依赖先前经验；重置同时影响识别与路径时需保留歧义。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "goat-bench:refresh",
          "krantz2023ivln:refresh"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I12-2",
      "challenge_id": "C12",
      "title": "把目标相关记忆问答纳入探索评测",
      "mechanism": "在多目标探索之外加入历史相关问答，使是否能访问/运用经验成为显式输出。",
      "conditions": [
        "LMEE探索与记忆任务",
        "QA含模型评分，指标不能与导航SR互换"
      ],
      "variants": [
        {
          "paper_id": "wang2026lmee",
          "method_claim": "LMEE联合多目标导航与目标相关记忆QA，MemoryExplorer为其学习基线。",
          "evidence_refs": [
            "wang2026lmee:e1",
            "wang2026lmee:e2"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "主表58/166任务；GOAT子集对比与全量原论文基线分开。",
          "mechanism_variant": "LMEE联合多目标导航与目标相关记忆QA，MemoryExplorer为其学习基线。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "wang2026lmee:protocol",
          "variant_id": "I12-2:1"
        }
      ],
      "distinction_from_siblings": "测了记忆利用的另一面，但不自动证明QA得分等同真实空间记忆正确率。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "到达目标不能完整显示探索期间是否存下且能调用目标相关记忆。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "增加明确依赖历史的问答输出，可从另一个维度检验记忆使用；回答评分质量本身也需审计。",
      "rationale": {
        "recognition": "到达目标不能完整显示探索期间是否存下且能调用目标相关记忆。",
        "explanation": "增加明确依赖历史的问答输出，可从另一个维度检验记忆使用；回答评分质量本身也需审计。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I12-3",
      "challenge_id": "C12",
      "title": "固定工程底座，替换具体决策部分来做条件化归因",
      "mechanism": "共同地图、感知及执行底座下改变探索策略，或固定执行与回退只移除经验，避免整套模型对比替代组件证据。",
      "conditions": [
        "只针对论文实际干预作结论",
        "不同干预不是同一个因果问题"
      ],
      "variants": [
        {
          "paper_id": "engineering-outruns-intelligence",
          "method_claim": "在同框架改变探索value map，并区分GT语义与GLEE检测条件。",
          "evidence_refs": [
            "engineering-outruns-intelligence:e1",
            "engineering-outruns-intelligence:e2",
            "engineering-outruns-intelligence:pipeline"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "语义检测条件可改变结论，不可概括为LLM无用。",
          "mechanism_variant": "在同框架改变探索value map，并区分GT语义与GLEE检测条件。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "engineering-outruns-intelligence:protocol",
          "variant_id": "I12-3:1"
        },
        {
          "paper_id": "ham-vln",
          "method_claim": "去反思记忆保留回退动作，固定规划/定位/控制器比较。",
          "evidence_refs": [
            "ham-vln:e5"
          ],
          "relation_to_challenge": "protocol",
          "boundary": "100条子集；不能推断所有反思机制或全量benchmark都同效。",
          "mechanism_variant": "去反思记忆保留回退动作，固定规划/定位/控制器比较。",
          "mapping_status": "supported_by_recorded_source_claim",
          "rationale_anchor_refs": [],
          "rationale_status": "editorial_explanation_pending_author_rationale_check",
          "method_id": "ham-vln:protocol",
          "variant_id": "I12-3:2"
        }
      ],
      "distinction_from_siblings": "编者将两种控制思想并列，不宣称作者共用实验或存在学术继承。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "整套系统之间的成绩差不能指明某一组件的贡献。",
      "candidate_evidence_status": "design_supported_editorial_rationale_pending_author_check",
      "why_it_addresses_challenge": "保持工程底座或回退动作等关键条件不变，再替换探索/移除反思，可把结论限制到实际改变的因素和测试范围。",
      "rationale": {
        "recognition": "整套系统之间的成绩差不能指明某一组件的贡献。",
        "explanation": "保持工程底座或回退动作等关键条件不变，再替换探索/移除反思，可把结论限制到实际改变的因素和测试范围。",
        "attribution": "editorial_explanation_from_recorded_design",
        "author_rationale_anchors": [],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I05-7",
      "challenge_id": "C05",
      "title": "图像快照能紧凑保留文本对象关系难以表达的空间信息",
      "mechanism": "将共可见对象及背景保留为多视图快照，并用增量聚合和目标预筛选管理规模。",
      "conditions": [
        "VLM可直接读取图像",
        "表达能力与检索覆盖都有限，快照不等于保留全部原始视频"
      ],
      "variants": [
        {
          "paper_id": "3d-mem",
          "method_claim": "以共可见对象组织memory snapshots，按相关类别预筛选，另保留frontier snapshots。",
          "evidence_refs": [
            "3d-mem:e1",
            "3d-mem:pipeline",
            "3d-mem:rationale",
            "3d-mem:navmesh"
          ],
          "relation_to_challenge": "direct",
          "boundary": "主动A-EQA、被动EM-EQA与GOAT分开；快照不是所有原始图像。 实际执行使用global navmesh prior的Habitat pathfinder；替换普通规划器未在本次配置验证。",
          "mechanism_variant": "以共可见对象组织memory snapshots，按相关类别预筛选，另保留frontier snapshots。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [
            "3d-mem:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "3d-mem:method",
          "variant_id": "I05-7:1"
        }
      ],
      "distinction_from_siblings": "关键在表示保真度：视觉快照保存对象间空隙、朝向与背景；不是SayPlan式只取更小文本子图。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "复杂空间关系并不总能被离散对象标签和少量文字关系充分保留。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "共可见快照同时保存对象、空隙、相对朝向与背景，现成VLM可直接读这些视觉线索，再以聚合与检索控制规模。",
      "rationale": {
        "recognition": "复杂空间关系并不总能被离散对象标签和少量文字关系充分保留。",
        "explanation": "共可见快照同时保存对象、空隙、相对朝向与背景，现成VLM可直接读这些视觉线索，再以聚合与检索控制规模。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "3d-mem:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    },
    {
      "insight_id": "I09-5",
      "challenge_id": "C09",
      "title": "同一视觉界面表达已知与未探索区域，才可在回答和继续找证据之间选择",
      "mechanism": "Memory Snapshots表示已探索区域，Frontier Snapshots提供尚待探索方向的可见线索，供VLM共同决策。",
      "conditions": [
        "A-EQA或GOAT主动阶段",
        "EM-EQA固定轨迹不支持主动探索归因"
      ],
      "variants": [
        {
          "paper_id": "3d-mem",
          "method_claim": "VLM从Memory Snapshots与Frontier Snapshots选择已有证据或探索目标。",
          "evidence_refs": [
            "3d-mem:e1",
            "3d-mem:pipeline",
            "3d-mem:e2",
            "3d-mem:rationale",
            "3d-mem:navmesh"
          ],
          "relation_to_challenge": "adjacent",
          "boundary": "仅A-EQA/GOAT探索支持此路径；EM-EQA不是主动取景。 实际执行使用global navmesh prior的Habitat pathfinder；替换普通规划器未在本次配置验证。",
          "mechanism_variant": "VLM从Memory Snapshots与Frontier Snapshots选择已有证据或探索目标。",
          "mapping_status": "candidate_requires_finer_locator",
          "rationale_anchor_refs": [
            "3d-mem:rationale"
          ],
          "rationale_status": "author_rationale_rechecked",
          "method_id": "3d-mem:method",
          "variant_id": "I09-5:1"
        }
      ],
      "distinction_from_siblings": "关键是已知/未知信息可在同一表示中比较；不等同NavMCP的跨调用证据账本。",
      "attribution": "editorial_synthesis_of_distinct_author_methods",
      "same_author_claim_not_asserted": true,
      "key_recognition": "只有已知区域的记忆不能表达继续探索可能获得什么信息。",
      "candidate_evidence_status": "author_rationale_anchor_available",
      "why_it_addresses_challenge": "将frontier的视觉线索与已知快照共同呈现，可让模型在利用现有证据和获取新证据之间作选择。",
      "rationale": {
        "recognition": "只有已知区域的记忆不能表达继续探索可能获得什么信息。",
        "explanation": "将frontier的视觉线索与已知快照共同呈现，可让模型在利用现有证据和获取新证据之间作选择。",
        "attribution": "editorial_synthesis_with_direct_author_rationale_anchors",
        "author_rationale_anchors": [
          "3d-mem:rationale"
        ],
        "author_wording_not_asserted": true,
        "unverified": "共同表述不是作者共同原话；未有rationale anchor的解释未核到作者直接如此论证，暂为待核解释。",
        "causal_effect_independently_verified": false
      }
    }
  ],
  "evidence": [
    {
      "evidence_id": "harnessvln:e1",
      "paper_id": "harnessvln",
      "source_url": "https://arxiv.org/html/2609.15195v3",
      "locator": "§3.1.2, §3.2, §3.3",
      "statement": "派发前检查观测来源、几何及子目标；停止请求另验语义、几何和进度。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "harnessvln:e2",
      "paper_id": "harnessvln",
      "source_url": "https://arxiv.org/html/2609.15195v3",
      "locator": "§4.4, Table 4",
      "statement": "固定100-episode子集上的memory→graph→stop累加消融，估计已有组件条件下增量，不是完整析因。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "harnessvln:e3",
      "paper_id": "harnessvln",
      "source_url": "https://arxiv.org/html/2609.15195v3",
      "locator": "§4.2, Appendix 1.2; Reference Cai et al. (2026)",
      "statement": "明确把NavDP作为楼梯执行工具；采用范围不扩成整套方法继承。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "relation"
    },
    {
      "evidence_id": "harnessvln:pipeline",
      "paper_id": "harnessvln",
      "source_url": "https://arxiv.org/html/2609.15195v3",
      "locator": "§3.1–3.3; §4.1–4.4 and Tables 2–4; Appendix 1.1–1.2; §2 and selected References",
      "statement": "规划提案 → 来源/几何/进度检查 → 工具执行 → 状态更新",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "navharness:e1",
      "paper_id": "navharness",
      "source_url": "https://arxiv.org/html/2609.34276v1",
      "locator": "§3.3–3.5",
      "statement": "恢复保留剩余任务预算；交接区分已搜索和有证据排除，原任务记录不可由后续会话覆盖。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "navharness:e2",
      "paper_id": "navharness",
      "source_url": "https://arxiv.org/html/2609.34276v1",
      "locator": "Appendix C.1, Table 3 A–D",
      "statement": "独立会话是整套策略对比，不是memory-only消融；组件干预分别从full出发。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "navharness:e3",
      "paper_id": "navharness",
      "source_url": "https://arxiv.org/html/2609.34276v1",
      "locator": "Appendix E.3–E.6, E.9",
      "statement": "评测为静态模拟环境；旧占据格不随SLAM回环校正更新，judge也会误判。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "limitation"
    },
    {
      "evidence_id": "navharness:pipeline",
      "paper_id": "navharness",
      "source_url": "https://arxiv.org/html/2609.34276v1",
      "locator": "§2–3.5; §4.1; Appendix B.3, C.1; Appendix D.4, E.1–E.9",
      "statement": "新会话读取记录 → 搜索/修正 → 检验结果 → 交接/跨run整理",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "agenticnav-tool-harness:e1",
      "paper_id": "agenticnav-tool-harness",
      "source_url": "https://arxiv.org/html/2606.10577v3",
      "locator": "§III-C–D",
      "statement": "像素反投影后检查障碍；记忆限当前episode，每步重建有界上下文。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "agenticnav-tool-harness:e2",
      "paper_id": "agenticnav-tool-harness",
      "source_url": "https://arxiv.org/html/2606.10577v3",
      "locator": "§IV-A, Tables I–III",
      "statement": "100条R2R-CE子集；76%对应Gemini-3.7-Flash，GPT-5.5为55%，不能把差值当版本进步。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "agenticnav-tool-harness:e3",
      "paper_id": "agenticnav-tool-harness",
      "source_url": "https://arxiv.org/html/2606.10577v3",
      "locator": "§IV-A Memory and Context Management",
      "statement": "作者将进度文本较差表现解释为错误判断延续；该解释不等于独立因果证实。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "limitation"
    },
    {
      "evidence_id": "agenticnav-tool-harness:pipeline",
      "paper_id": "agenticnav-tool-harness",
      "source_url": "https://arxiv.org/html/2606.10577v3",
      "locator": "§II–III-D; §IV-A and Tables I–III; §V excerpt",
      "statement": "RGB目标像素 → 按需深度 → 几何检查 → 执行/选择性回看",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "qwen-robotnav:e1",
      "paper_id": "qwen-robotnav",
      "source_url": "https://arxiv.org/html/2606.18112v3",
      "locator": "§2.2, Algorithm 1",
      "statement": "按时间与相机权重分配有上下限的视觉token；作者明确称其启发式。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "qwen-robotnav:e2",
      "paper_id": "qwen-robotnav",
      "source_url": "https://arxiv.org/html/2606.18112v3",
      "locator": "§5.5, Fig.15 text",
      "statement": "4B模型在500条R2R验证轨迹上扫描预算与衰减；收益不是严格单调。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "qwen-robotnav:pipeline",
      "paper_id": "qwen-robotnav",
      "source_url": "https://arxiv.org/html/2606.18112v3",
      "locator": "§2.1–2.2, Algorithm 1; §5.5, Fig.15 caption and associated text",
      "statement": "分配视觉token → 编码历史/视角 → 预测waypoint轨迹",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "holoagent-0:e1",
      "paper_id": "holoagent-0",
      "source_url": "https://arxiv.org/html/2606.23565v1",
      "locator": "§2.2–3.1, §4.5",
      "statement": "技能返回结构化状态；新观测、物体操作结果或用户纠正触发局部记忆更新。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "holoagent-0:e2",
      "paper_id": "holoagent-0",
      "source_url": "https://arxiv.org/html/2606.23565v1",
      "locator": "§5.1–5.2",
      "statement": "定量导航/建图与全系统定性演示分开；没有统一端到端全技能成功率。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "holoagent-0:pipeline",
      "paper_id": "holoagent-0",
      "source_url": "https://arxiv.org/html/2606.23565v1",
      "locator": "§2–3.1; §4.5; §5.1–5.2",
      "statement": "检索空间状态 → 技能图调度 → 状态反馈 → 监控/重规划",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "krantz2023ivln:e1",
      "paper_id": "krantz2023ivln",
      "source_url": "https://arxiv.org/html/2210.03087v3",
      "locator": "§3 The Iterative Paradigm, HTML L100–102",
      "statement": "每episode后 oracle纠偏并带至下一起点；agent沿途被动观察",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "krantz2023ivln:e2",
      "paper_id": "krantz2023ivln",
      "source_url": "https://arxiv.org/html/2210.03087v3",
      "locator": "§4.2.2, L184–193; Table 4",
      "statement": "地图分别按episode、tour重置或预先给定；训练与评测模式交叉比较",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "krantz2023ivln:e3",
      "paper_id": "krantz2023ivln",
      "source_url": "https://arxiv.org/html/2210.03087v3",
      "locator": "§5.2, L259–267",
      "statement": "map对CMA的优势混有DAgger训练差异；known map也未胜iterative map",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "limitation"
    },
    {
      "evidence_id": "krantz2023ivln:pipeline",
      "paper_id": "krantz2023ivln",
      "source_url": "https://arxiv.org/html/2210.03087v3",
      "locator": "摘要；§1–2相关段；§3 tour/数据/指标；§4.1 TourHAMT段与§4.2；§5表2–4及分析；§6限制与未来工作",
      "statement": "RGB-D→占据/13类语义地图→自中心裁剪→CNN→CMA动作；另测跨episode隐状态/历史",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "goat:e1",
      "paper_id": "goat",
      "source_url": "https://arxiv.org/html/2311.06430v1",
      "locator": "§4.1 Global/Local Policy, L200–208",
      "statement": "探索时阈值匹配，探索后取最高分；Spot与Stretch采用不同低层执行",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "goat:e2",
      "paper_id": "goat",
      "source_url": "https://arxiv.org/html/2311.06430v1",
      "locator": "§4.2, L210–219; Table 1",
      "statement": "定量主测Spot：9宅、15类；每目标200步、STOP且距离<1m",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "goat:e3",
      "paper_id": "goat",
      "source_url": "https://arxiv.org/html/2311.06430v1",
      "locator": "§3 Matching Performance During Exploration, L155–157; §4.1 L177",
      "statement": "固定匹配阈值有误报/漏报；实测选MaskRCNN而非较不稳的Detic",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "limitation"
    },
    {
      "evidence_id": "goat:pipeline",
      "paper_id": "goat",
      "source_url": "https://arxiv.org/html/2311.06430v1",
      "locator": "§1相关段；§2.1–2.2任务/主实验及表1、图3图注；§2.3社会导航段；§3讨论目标匹配与检测局限；§4.1–4.2方法/协议；§5.1首段与匹配表局部",
      "statement": "RGB-D/pose→实例分割与语义图+多视角实例记忆→CLIP/SuperGlue匹配或frontier→FMM/本体控制器",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "goat-bench:e1",
      "paper_id": "goat-bench",
      "source_url": "https://arxiv.org/html/2404.06609v1",
      "locator": "§3, L99–105; §4 Evaluation Splits, L134–145",
      "statement": "Stretch/Habitat，RGB-D+GPS/Compass；500动作/子目标，1m+STOP；三split环境均未见",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "goat-bench:e2",
      "paper_id": "goat-bench",
      "source_url": "https://arxiv.org/html/2404.06609v1",
      "locator": "§6, L168–169",
      "statement": "SPL最短路从上一子任务实际结束位置算，不从理想前一目标算",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "goat-bench:e3",
      "paper_id": "goat-bench",
      "source_url": "https://arxiv.org/html/2404.06609v1",
      "locator": "§7.2/Fig.5, L196–201",
      "statement": "逐子任务清空：GOAT SPL17.6→9.4；monolithic 9.4→9.0",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "goat-bench:pipeline",
      "paper_id": "goat-bench",
      "source_url": "https://arxiv.org/html/2404.06609v1",
      "locator": "摘要；§1–2；§3；§4数据/生成流程与split相关段；§5；§6表2；§7.1–7.4；§8；附录C只零散段",
      "statement": "比较modular实例地图、按模态skill chain、跨子任务GRU隐状态monolithic",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "krantz2020vlnce:e1",
      "paper_id": "krantz2020vlnce",
      "source_url": "https://arxiv.org/html/2004.02857v2",
      "locator": "§1, L56–73; §3, L115–117",
      "statement": "不供位置/朝向；前进0.25m、转15°、STOP；无图拓扑及短程oracle",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "krantz2020vlnce:e2",
      "paper_id": "krantz2020vlnce",
      "source_url": "https://arxiv.org/html/2004.02857v2",
      "locator": "§4.2, Eq.(4–8), L163–179",
      "statement": "视觉GRU供语言注意力，再对RGB/深度注意；第二GRU输出动作",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "krantz2020vlnce:e3",
      "paper_id": "krantz2020vlnce",
      "source_url": "https://arxiv.org/html/2004.02857v2",
      "locator": "§5.2 qualitative L235–236; §5.3 Caveats L243–244",
      "statement": "窄视野可能漏见指令对象；映射回nav-graph的比较受轨迹排除和转换误差影响",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "limitation"
    },
    {
      "evidence_id": "krantz2020vlnce:pipeline",
      "paper_id": "krantz2020vlnce",
      "source_url": "https://arxiv.org/html/2004.02857v2",
      "locator": "摘要；§1–3；§4.1–4.2公式与架构；§4.3部分训练段；§5.1–5.3表2–4与失败/caveats；§6首段",
      "statement": "RGB/深度ResNet特征+语言编码→Seq2Seq或双GRU跨模态注意力→低层动作",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "batra2020objectnav:e1",
      "paper_id": "batra2020objectnav",
      "source_url": "https://arxiv.org/html/2006.13171v2",
      "locator": "§2.1, L76–92",
      "statement": "成功拆成STOP意图、位置合法、表面距离、可见性；允许oracle-visibility变体",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "batra2020objectnav:e2",
      "paper_id": "batra2020objectnav",
      "source_url": "https://arxiv.org/html/2006.13171v2",
      "locator": "§2.1.1, L106–121",
      "statement": "SPL不分近失误/彻底失败，不罚原地转动；不可跨不同路径分布直接比较",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "limitation"
    },
    {
      "evidence_id": "batra2020objectnav:e3",
      "paper_id": "batra2020objectnav",
      "source_url": "https://arxiv.org/html/2006.13171v2",
      "locator": "§3, L151–153",
      "statement": "Habitat实例化预计算1m内、可导航且oracle可见的valid viewpoints",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "batra2020objectnav:pipeline",
      "paper_id": "batra2020objectnav",
      "source_url": "https://arxiv.org/html/2006.13171v2",
      "locator": "摘要；§1–2.3；§2.1.1全部列出的SPL问题；§3 Habitat场景/目标/valid-viewpoint相关段",
      "statement": "规范输入/本体→可达成功区域→STOP判定→SR与路径效率；没有新policy表示",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "navgpt:e1",
      "paper_id": "navgpt",
      "source_url": "https://arxiv.org/html/2305.16986v2",
      "locator": "§3.3 L122–125",
      "statement": "明确采用ReAct式推理/动作交替；推理本身不产生环境观测。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "navgpt:e2",
      "paper_id": "navgpt",
      "source_url": "https://arxiv.org/html/2305.16986v2",
      "locator": "§4.2–4.3 Tables 1–3",
      "statement": "主结果用GPT-4；视觉消融改用GPT-3.5及216样本，不能混作同一条件。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "navgpt:pipeline",
      "paper_id": "navgpt",
      "source_url": "https://arxiv.org/html/2305.16986v2",
      "locator": "完整摘要; §3.1–3.4，L94–129; §4.2–4.3，L155–195",
      "statement": "视觉模型转文本，prompt manager组织观测、规则与历史；每步先推理再选图上动作。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "mapgpt:e1",
      "paper_id": "mapgpt",
      "source_url": "https://aclanthology.org/2024.acl-long.529.pdf",
      "locator": "§3.2 L366–380",
      "statement": "邻接可导航节点由模拟器给出，在线记录图结构。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "mapgpt:e2",
      "paper_id": "mapgpt",
      "source_url": "https://aclanthology.org/2024.acl-long.529.pdf",
      "locator": "§4.1–4.2 L499–514",
      "statement": "REVERIE只评导航，不评object grounding；216轨迹子集与val-unseen分列。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "mapgpt:pipeline",
      "paper_id": "mapgpt",
      "source_url": "https://aclanthology.org/2024.acl-long.529.pdf",
      "locator": "完整摘要; §3.1–3.3 pp.9798–9801; §4.1–4.2 Tables 1–2 pp.9801–9802",
      "statement": "在线拓扑图文字化，保存上轮多步计划，逐步重规划。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "discussnav:e1",
      "paper_id": "discussnav",
      "source_url": "https://arxiv.org/html/2309.11382v1",
      "locator": "§III-C L118–123",
      "statement": "轨迹摘要和完成估计反馈进入动作决策。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "discussnav:e2",
      "paper_id": "discussnav",
      "source_url": "https://arxiv.org/html/2309.11382v1",
      "locator": "§IV-A–C L126–157",
      "statement": "GPT-4导航n=5；真实机器人仅20条指令，移动配激光避障规则。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "discussnav:pipeline",
      "paper_id": "discussnav",
      "source_url": "https://arxiv.org/html/2309.11382v1",
      "locator": "完整摘要; §III-B–C L88–123; §IV-A–C L125–159，Tables I–III",
      "statement": "按角色调用指令、感知、完成估计、决策检验专家，融合不一致候选。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "instructnav:e1",
      "paper_id": "instructnav",
      "source_url": "https://arxiv.org/html/2406.04882v1",
      "locator": "§3.3.4–3.4 L145–152",
      "statement": "显式失败反馈、障碍屏蔽、规划执行及停止接口。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "instructnav:e2",
      "paper_id": "instructnav",
      "source_url": "https://arxiv.org/html/2406.04882v1",
      "locator": "§4.3.1 L208–225",
      "statement": "模块消融每任务随机100条，不能等同全验证集主表。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "instructnav:pipeline",
      "paper_id": "instructnav",
      "source_url": "https://arxiv.org/html/2406.04882v1",
      "locator": "正式版完整摘要; 预印本§3.1–3.4 L85–153; §4.1–4.4 Tables 1–5，L188–246",
      "statement": "DCoN逐次更新动作与地标；四种value map合成目标，再用A*及低层控制。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "esc:e1",
      "paper_id": "esc",
      "source_url": "https://proceedings.mlr.press/v202/zhou23r/zhou23r.pdf",
      "locator": "§3.3.2 pp.4–5",
      "statement": "优化软约束后选一个frontier，不是自由文本工具调用。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "esc:e2",
      "paper_id": "esc",
      "source_url": "https://proceedings.mlr.press/v202/zhou23r/zhou23r.pdf",
      "locator": "§4.1 p.5",
      "statement": "MP3D/HM3D/RoboTHOR均500步；前两者提供GPS。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "esc:pipeline",
      "paper_id": "esc",
      "source_url": "https://proceedings.mlr.press/v202/zhou23r/zhou23r.pdf",
      "locator": "完整摘要; §2–3.3 pp.2–5; §4.1–4.3及Table 1 pp.5–6",
      "statement": "GLIP生成房间/物体语义，DeBERTa给关联分数，PSL软规则联合距离选frontier。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "l3mvn:e1",
      "paper_id": "l3mvn",
      "source_url": "https://arxiv.org/html/2304.05501v2",
      "locator": "§III-D.4–E L159–164",
      "statement": "语义低分时回退cost-utility，局部FMM逐步重规划。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "l3mvn:e2",
      "paper_id": "l3mvn",
      "source_url": "https://arxiv.org/html/2304.05501v2",
      "locator": "§IV-A.2 L202–209",
      "statement": "使用finetuned RedNet；feed-forward版本另训练RoBERTa/head。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "l3mvn:pipeline",
      "paper_id": "l3mvn",
      "source_url": "https://arxiv.org/html/2304.05501v2",
      "locator": "完整摘要; §III-B–E L105–165; §IV-A L198–212，Table I",
      "statement": "语言得分或训练的embedding head为frontier估分，置信区间规则融合cost-utility。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "lfg:e1",
      "paper_id": "lfg",
      "source_url": "https://proceedings.mlr.press/v229/shah23c/shah23c.pdf",
      "locator": "§5 Eq.1，Algorithm 2",
      "statement": "语言分数只是搜索启发项；目标已见则用地图取位置。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "lfg:e2",
      "paper_id": "lfg",
      "source_url": "https://proceedings.mlr.press/v229/shah23c/shah23c.pdf",
      "locator": "§6.1 pp.6–7",
      "statement": "模拟每场景10 episode，所有模拟baseline采用GT语义。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "lfg:pipeline",
      "paper_id": "lfg",
      "source_url": "https://proceedings.mlr.press/v229/shah23c/shah23c.pdf",
      "locator": "完整摘要; §4–5 pp.3–5 / Algorithms 1–2; §6.1–6.2和§7 pp.6–8",
      "statement": "正负提示多次采样形成启发分数，与距离联合指导frontier搜索。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "voronav:e1",
      "paper_id": "voronav",
      "source_url": "https://arxiv.org/html/2401.02695v2",
      "locator": "§3.3–3.4 L141–168",
      "statement": "决策点与图结构绑定，非固定步数盲选frontier。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "voronav:e2",
      "paper_id": "voronav",
      "source_url": "https://arxiv.org/html/2401.02695v2",
      "locator": "Table 1 / §4.1",
      "statement": "部分baseline视觉模块改为Grounded-SAM；HM3D 2000/HSSD 1200 episode。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "voronav:pipeline",
      "paper_id": "voronav",
      "source_url": "https://arxiv.org/html/2401.02695v2",
      "locator": "完整摘要; §3.1–3.4 L112–168; §4.1–4.2.2 Tables 1–2 L169–237",
      "statement": "从在线语义图提取Reduced Voronoi Graph，融合路径与远视描述给LLM。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "trihelper:e1",
      "paper_id": "trihelper",
      "source_url": "https://arxiv.org/html/2403.15223v1",
      "locator": "§IV-C.1 L153–155",
      "statement": "误检不永久排除，超阈值未发现目标时允许返回记录点。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "trihelper:e2",
      "paper_id": "trihelper",
      "source_url": "https://arxiv.org/html/2403.15223v1",
      "locator": "§V-E–F Tables I–II",
      "statement": "自动SR与人工复核SR分列；三helper同时使用时探索失败反而增多。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "trihelper:pipeline",
      "paper_id": "trihelper",
      "source_url": "https://arxiv.org/html/2403.15223v1",
      "locator": "完整摘要; §III-B / IV-B–C L97–161; §V-A–F Tables I–II L165–254",
      "statement": "增加碰撞、探索、检测三个动态helper。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "imaginenav:e1",
      "paper_id": "imaginenav",
      "source_url": "https://proceedings.iclr.cc/paper_files/paper/2025/file/eb261df4322a8bd0a73093c4d8a0d02d-Paper-Conference.pdf",
      "locator": "§3.2 p.5",
      "statement": "Where2Imagine用Habitat-Web人类轨迹训练ResNet18。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "imaginenav:e2",
      "paper_id": "imaginenav",
      "source_url": "https://proceedings.iclr.cc/paper_files/paper/2025/file/eb261df4322a8bd0a73093c4d8a0d02d-Paper-Conference.pdf",
      "locator": "§4.3 Table 1 p.7",
      "statement": "真实未来图像的Oracle结果与NVS运行结果分开。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "imaginenav:pipeline",
      "paper_id": "imaginenav",
      "source_url": "https://proceedings.iclr.cc/paper_files/paper/2025/file/eb261df4322a8bd0a73093c4d8a0d02d-Paper-Conference.pdf",
      "locator": "完整摘要; §3.1–3.3 pp.4–5; §4.1–4.4 Tables 1–2 pp.6–8",
      "statement": "Where2Imagine预测候选位姿，NVS合成未来视图，VLM选择后交PointNav。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "vlmnav:e1",
      "paper_id": "vlmnav",
      "source_url": "https://arxiv.org/html/2411.05755v1",
      "locator": "§3.2–3.5 L83–118",
      "statement": "外部动作提议和独立停止调用仍存在，端到端不等于无外层工程。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "vlmnav:e2",
      "paper_id": "vlmnav",
      "source_url": "https://arxiv.org/html/2411.05755v1",
      "locator": "§4.1 Table 1 L127–141",
      "statement": "allow_slide关闭后SR 50.4→12.9；成功阈值1.2m。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "vlmnav:pipeline",
      "paper_id": "vlmnav",
      "source_url": "https://arxiv.org/html/2411.05755v1",
      "locator": "完整摘要; §3.1–3.5 L74–118; §4–4.2 L121–151，Tables 1–2",
      "statement": "深度可通行性与探索偏置构造动作，再投影到图像供VLM选择；停止另调模型。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "navgpt2:e1",
      "paper_id": "navgpt2",
      "source_url": "https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/01143.pdf",
      "locator": "§3.2 pp.6–8",
      "statement": "图保存历史与支持回溯；策略借用DUET图方法。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "navgpt2:e2",
      "paper_id": "navgpt2",
      "source_url": "https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/01143.pdf",
      "locator": "§3.3 / §4.1",
      "statement": "10k GPT-4V推理数据，BC+DAgger训练；最优版本用PREVALENT合成数据。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "navgpt2:pipeline",
      "paper_id": "navgpt2",
      "source_url": "https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/01143.pdf",
      "locator": "完整摘要; §3.1–3.3 pp.5–9; §4.1–4.2和Table 1 pp.9–10",
      "statement": "冻结LLM视觉latent供拓扑图策略；先训Q-former，再训动作policy。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "engineering-outruns-intelligence:e1",
      "paper_id": "engineering-outruns-intelligence",
      "source_url": "https://arxiv.org/html/2507.20021v3",
      "locator": "§5 L234–244",
      "statement": "主实验换为GPT-4.1并采用GT语义；FPE终点接近/停止仍依赖语义。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "engineering-outruns-intelligence:e2",
      "paper_id": "engineering-outruns-intelligence",
      "source_url": "https://arxiv.org/html/2507.20021v3",
      "locator": "§6.1 L283–292",
      "statement": "GLEE子集上FPE SR不胜InstructNav，结论有传感器条件。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "engineering-outruns-intelligence:pipeline",
      "paper_id": "engineering-outruns-intelligence",
      "source_url": "https://arxiv.org/html/2507.20021v3",
      "locator": "完整摘要; §4–6.1 L136–292; §8及limitations L329–342",
      "statement": "在InstructNav框架内比较几何FPE与轻量语义SHF。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "ma2019regretful:e1",
      "paper_id": "ma2019regretful",
      "source_url": "https://openaccess.thecvf.com/content_CVPR_2019/papers/Ma_The_Regretful_Agent_Heuristic-Aided_Navigation_Through_Progress_Estimation_CVPR_2019_paper.pdf",
      "locator": "完整摘要；§2–6，Tables 1–3；未逐图、补充材料/代码未读",
      "statement": "Regret Module比较相邻进度估计，混合前进/回退表示；Progress Marker把已访视点的估计附着到候选方向。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "ma2019regretful:e2",
      "paper_id": "ma2019regretful",
      "source_url": "https://openaccess.thecvf.com/content_CVPR_2019/papers/Ma_The_Regretful_Agent_Heuristic-Aided_Navigation_Through_Progress_Estimation_CVPR_2019_paper.pdf",
      "locator": "完整摘要；§2–6，Tables 1–3；未逐图、补充材料/代码未读",
      "statement": "R2R离散图评测；Table2组件消融与Table3禁用回退实验，能区分进度提示和回退机制贡献。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "ma2019regretful:pipeline",
      "paper_id": "ma2019regretful",
      "source_url": "https://openaccess.thecvf.com/content_CVPR_2019/papers/Ma_The_Regretful_Agent_Heuristic-Aided_Navigation_Through_Progress_Estimation_CVPR_2019_paper.pdf",
      "locator": "完整摘要；§2–6，Tables 1–3；未逐图、补充材料/代码未读",
      "statement": "Regret Module比较相邻进度估计，混合前进/回退表示；Progress Marker把已访视点的估计附着到候选方向。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "rana2023sayplan:e1",
      "paper_id": "rana2023sayplan",
      "source_url": "https://proceedings.mlr.press/v229/rana23a/rana23a.pdf",
      "locator": "完整摘要；§1–6、Algorithm1、Tables1–3；附录未系统阅读",
      "statement": "expand/contract选择子图，Dijkstra补齐房间间路径，图模拟器verify_plan返回失败信息并触发重规划。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "rana2023sayplan:e2",
      "paper_id": "rana2023sayplan",
      "source_url": "https://proceedings.mlr.press/v229/rana23a/rana23a.pdf",
      "locator": "完整摘要；§1–6、Algorithm1、Tables1–3；附录未系统阅读",
      "statement": "两种大环境；区分计划Correctness与Executability，比较开放环LLM和仅加路径规划器的变体。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "rana2023sayplan:pipeline",
      "paper_id": "rana2023sayplan",
      "source_url": "https://proceedings.mlr.press/v229/rana23a/rana23a.pdf",
      "locator": "完整摘要；§1–6、Algorithm1、Tables1–3；附录未系统阅读",
      "statement": "expand/contract选择子图，Dijkstra补齐房间间路径，图模拟器verify_plan返回失败信息并触发重规划。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "rajvanshi2024saynav:e1",
      "paper_id": "rajvanshi2024saynav",
      "source_url": "https://arxiv.org/html/2309.04077v4",
      "locator": "完整摘要；§1–5、Algorithm1、Table1–2、§4.8真机演示说明",
      "statement": "层次图记录房间/大小物体；navigate/look工具转成PointNav；失败后更新计划、探索或补观察。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "rajvanshi2024saynav:e2",
      "paper_id": "rajvanshi2024saynav",
      "source_url": "https://arxiv.org/html/2309.04077v4",
      "locator": "完整摘要；§1–5、Algorithm1、Table1–2、§4.8真机演示说明",
      "statement": "132个ProcTHOR房屋、每次3目标；Table1区分GT/视觉图与oracle/学习控制器，防止混淆上限和可执行配置。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "rajvanshi2024saynav:pipeline",
      "paper_id": "rajvanshi2024saynav",
      "source_url": "https://arxiv.org/html/2309.04077v4",
      "locator": "完整摘要；§1–5、Algorithm1、Table1–2、§4.8真机演示说明",
      "statement": "层次图记录房间/大小物体；navigate/look工具转成PointNav；失败后更新计划、探索或补观察。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "li2024memonav:e1",
      "paper_id": "li2024memonav",
      "source_url": "https://openaccess.thecvf.com/content/CVPR2024/papers/Li_MemoNav_Working_Memory_Model_for_Visual_Navigation_CVPR_2024_paper.pdf",
      "locator": "完整摘要；§3–5、Tables1–3、补充§13；未核全部附录图",
      "statement": "从VGM扩展：注意力遗忘STM，global node聚合LTM，GATv2生成WM；换目标恢复被遗忘节点。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "li2024memonav:e2",
      "paper_id": "li2024memonav",
      "source_url": "https://openaccess.thecvf.com/content/CVPR2024/papers/Li_MemoNav_Working_Memory_Model_for_Visual_Navigation_CVPR_2024_paper.pdf",
      "locator": "完整摘要；§3–5、Tables1–3、补充§13；未核全部附录图",
      "statement": "Habitat中的Gibson/MP3D、多目标ImageNav；组件和LTM消融；SR/PR改善不等于所有SPL/PPL最优。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "li2024memonav:pipeline",
      "paper_id": "li2024memonav",
      "source_url": "https://openaccess.thecvf.com/content/CVPR2024/papers/Li_MemoNav_Working_Memory_Model_for_Visual_Navigation_CVPR_2024_paper.pdf",
      "locator": "完整摘要；§3–5、Tables1–3、补充§13；未核全部附录图",
      "statement": "从VGM扩展：注意力遗忘STM，global node聚合LTM，GATv2生成WM；换目标恢复被遗忘节点。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "werby2024hovsg:e1",
      "paper_id": "werby2024hovsg",
      "source_url": "https://roboticsproceedings.org/rss20/p077.pdf",
      "locator": "完整摘要；§II–IV，TablesI、IV–VI；非全文附录精读",
      "statement": "RGB-D/里程计形成分段特征，再建楼层—房间—物体图；分层查询目标，由跨楼层Voronoi图导航。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "werby2024hovsg:e2",
      "paper_id": "werby2024hovsg",
      "source_url": "https://roboticsproceedings.org/rss20/p077.pdf",
      "locator": "完整摘要；§II–IV，TablesI、IV–VI；非全文附录精读",
      "statement": "ScanNet/Replica/HM3DSem与Spot双层楼实验；TableVI把检索成功与导航成功分开，41物体试次为29次检索成功、23次导航成功。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "werby2024hovsg:pipeline",
      "paper_id": "werby2024hovsg",
      "source_url": "https://roboticsproceedings.org/rss20/p077.pdf",
      "locator": "完整摘要；§II–IV，TablesI、IV–VI；非全文附录精读",
      "statement": "RGB-D/里程计形成分段特征，再建楼层—房间—物体图；分层查询目标，由跨楼层Voronoi图导航。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "anwar2025remembr:e1",
      "paper_id": "anwar2025remembr",
      "source_url": "https://arxiv.org/html/2409.13682v1",
      "locator": "完整摘要；§III–VIII、TablesI–II；官方项目/仓库说明，代码未读",
      "statement": "VILA分段caption进入向量库；LLM调用文本/时间/位置检索，输出结构化答案及坐标。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "anwar2025remembr:e2",
      "paper_id": "anwar2025remembr",
      "source_url": "https://arxiv.org/html/2409.13682v1",
      "locator": "完整摘要；§III–VIII、TablesI–II；官方项目/仓库说明，代码未读",
      "statement": "NaVQA：7段CODa视频、210问题，评时空误差与描述正确性；比较单轮/多轮检索，并有Nova Carter部署。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "anwar2025remembr:pipeline",
      "paper_id": "anwar2025remembr",
      "source_url": "https://arxiv.org/html/2409.13682v1",
      "locator": "完整摘要；§III–VIII、TablesI–II；官方项目/仓库说明，代码未读",
      "statement": "VILA分段caption进入向量库；LLM调用文本/时间/位置检索，输出结构化答案及坐标。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "xu2026memoir:e1",
      "paper_id": "xu2026memoir",
      "source_url": "https://arxiv.org/html/2510.08553v2",
      "locator": "完整摘要；§II–V-A/B、Algorithms1–3、TablesII–III、retrieval limitation段；非全附录阅读",
      "statement": "按视点锚定观测库与行为历史库；想象匹配检索后，由扩展DUET的三个编码分支融合。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "xu2026memoir:e2",
      "paper_id": "xu2026memoir",
      "source_url": "https://arxiv.org/html/2510.08553v2",
      "locator": "完整摘要；§II–V-A/B、Algorithms1–3、TablesII–III、retrieval limitation段；非全附录阅读",
      "statement": "IR2R与GSA-R2R；TableII区分基础模型、增广和full-graph预训练。GR-DUET对应IR2R unseen SPL 67.9→73.3，为5.4百分点。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "xu2026memoir:pipeline",
      "paper_id": "xu2026memoir",
      "source_url": "https://arxiv.org/html/2510.08553v2",
      "locator": "完整摘要；§II–V-A/B、Algorithms1–3、TablesII–III、retrieval limitation段；非全附录阅读",
      "statement": "按视点锚定观测库与行为历史库；想象匹配检索后，由扩展DUET的三个编码分支融合。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "wang2026lmee:e1",
      "paper_id": "wang2026lmee",
      "source_url": "https://openaccess.thecvf.com/content/CVPR2026/papers/Wang_Explore_with_Long-term_Memory_A_Benchmark_and_Multimodal_LLM-based_Reinforcement_CVPR_2026_paper.pdf",
      "locator": "完整摘要；§3–5、Tables2–4；作者稿补充§7、§14–15；非所有附录/图",
      "statement": "GRPO奖励动作/frontier/回答/格式；模型调用CLIP检索工具，限单轮调用。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "wang2026lmee:e2",
      "paper_id": "wang2026lmee",
      "source_url": "https://openaccess.thecvf.com/content/CVPR2026/papers/Wang_Explore_with_Long-term_Memory_A_Benchmark_and_Multimodal_LLM-based_Reinforcement_CVPR_2026_paper.pdf",
      "locator": "完整摘要；§3–5、Tables2–4；作者稿补充§7、§14–15；非所有附录/图",
      "statement": "LMEE主表58/166任务，补充给全量；GOAT比较只取36场景278子任务，Table3明确另有全量原论文基线。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "wang2026lmee:pipeline",
      "paper_id": "wang2026lmee",
      "source_url": "https://openaccess.thecvf.com/content/CVPR2026/papers/Wang_Explore_with_Long-term_Memory_A_Benchmark_and_Multimodal_LLM-based_Reinforcement_CVPR_2026_paper.pdf",
      "locator": "完整摘要；§3–5、Tables2–4；作者稿补充§7、§14–15；非所有附录/图",
      "statement": "GRPO奖励动作/frontier/回答/格式；模型调用CLIP检索工具，限单轮调用。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "navmcp:e1",
      "paper_id": "navmcp",
      "source_url": "https://arxiv.org/html/2608.30396v1",
      "locator": "§3.2–3.4",
      "statement": "调用包含模式、子目标和预算；观测摘要关联关键帧，账本保留正负证据与未解目标。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "navmcp:e2",
      "paper_id": "navmcp",
      "source_url": "https://arxiv.org/html/2608.30396v1",
      "locator": "§4.1、§4.4 Table 4",
      "statement": "固定推理和执行骨干的整套episodic接口消融下降14.9点；仅terminal-only观测返回下降5.9点。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "navmcp:pipeline",
      "paper_id": "navmcp",
      "source_url": "https://arxiv.org/html/2608.30396v1",
      "locator": "固定版完整摘要；arXiv HTML L87–93; §3.1–3.4 L134–163; §4.1–4.5及Tables 1–5 L164–279; §5限制 L280–288",
      "statement": "证据需求→语义导航调用→轨迹证据→跨调用记忆。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "sap-nav:e1",
      "paper_id": "sap-nav",
      "source_url": "https://arxiv.org/html/2608.12707v1",
      "locator": "Method / Active Viewpoint Verification",
      "statement": "先评分可见性和观察角度；最多三次换位后用最高充分性视图验证，拒绝候选进入黑名单。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "sap-nav:e2",
      "paper_id": "sap-nav",
      "source_url": "https://arxiv.org/html/2608.12707v1",
      "locator": "Experimental Setup、Real-world Deployment",
      "statement": "LangMap单目标与HM3D-OVON分列；实机段为Lite3配RGB-D/LiDAR及Nav2的定性示例。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "sap-nav:pipeline",
      "paper_id": "sap-nav",
      "source_url": "https://arxiv.org/html/2608.12707v1",
      "locator": "固定版完整摘要；L54–58; Method：QSSR与AVV L102–177; 实验设置、Tables 1–2与实机段 L178–223",
      "statement": "在线空间语义查询→视点充分性判断→移位验证→接受或继续搜索。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "hypothesis-graph-refinement:e1",
      "paper_id": "hypothesis-graph-refinement",
      "source_url": "https://arxiv.org/html/2604.04108v1",
      "locator": "§3.1、§3.4",
      "statement": "导航连通边与推导依赖DAG分开；反驳后删除该假设及传递依赖节点。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "hypothesis-graph-refinement:e2",
      "paper_id": "hypothesis-graph-refinement",
      "source_url": "https://arxiv.org/html/2604.04108v1",
      "locator": "§4.1–4.2 Table 1",
      "statement": "GOAT-Bench的72.41% SR与56.22% SPL对应278-subtask子集；全验证集另列。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "hypothesis-graph-refinement:pipeline",
      "paper_id": "hypothesis-graph-refinement",
      "source_url": "https://arxiv.org/html/2604.04108v1",
      "locator": "固定版完整摘要 L91–97; §3.1–3.4、Algorithm 1 L132–217; §4.1–4.2及Table 1 L218–258",
      "statement": "frontier语义假设→探索→现场验证→确认或级联撤回。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "safevantage:e1",
      "paper_id": "safevantage",
      "source_url": "https://arxiv.org/html/2609.36906v2",
      "locator": "§III-B–C",
      "statement": "按预期终局决策损失下降及路程代价选视点；Yes还要求来自不同位置的几何一致支持。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "safevantage:e2",
      "paper_id": "safevantage",
      "source_url": "https://arxiv.org/html/2609.36906v2",
      "locator": "§IV-A、§V",
      "statement": "主任务为ProcTHOR类别存在判断；离散视点图固定预算，连续导航与真实机器人列为后续评估。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "safevantage:pipeline",
      "paper_id": "safevantage",
      "source_url": "https://arxiv.org/html/2609.36906v2",
      "locator": "v2完整摘要 L42–46；abs公开文本补核作者; §III-A–C L86–129; §IV-A–E L130–225; §V Limitations L226–228",
      "statement": "命题记忆→候选可见性预测→主动取景→选择性决策。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "profocus:e1",
      "paper_id": "profocus",
      "source_url": "https://arxiv.org/html/2603.05530v2",
      "locator": "§3.2–3.3",
      "statement": "视觉查询针对当前全景中的裁剪区域；BD-MCTS筛选航点并检索路径上下文。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "profocus:e2",
      "paper_id": "profocus",
      "source_url": "https://arxiv.org/html/2603.05530v2",
      "locator": "§4.1",
      "statement": "REVERIE只评导航，不评object grounding；重实现基线与原论文报告结果分列。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "profocus:pipeline",
      "paper_id": "profocus",
      "source_url": "https://arxiv.org/html/2603.05530v2",
      "locator": "CVPR2026官方元数据与完整摘要; 固定arXiv v2完整摘要 L38–42; §3.1–3.3 L78–140; §4.1–4.2、Tables 1–2 L141–197",
      "statement": "语义地图→局部视觉查询循环→BD-MCTS筛选→决策。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "arxiv:2609.39915:e1",
      "paper_id": "arxiv:2609.39915",
      "source_url": "https://arxiv.org/html/2609.39915v1",
      "locator": "§3.2–3.5",
      "statement": "验证根据已观测结果给出未满足条件；修订目标不视为完成，完成段才触发压缩。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "arxiv:2609.39915:e2",
      "paper_id": "arxiv:2609.39915",
      "source_url": "https://arxiv.org/html/2609.39915v1",
      "locator": "§4.3 Table 2、§4.4、Appendix E",
      "statement": "压缩的token节约伴随部分SR/SPL下降；框架消融未分别隔离目标与验证。实机8条路线各3次。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "arxiv:2609.39915:pipeline",
      "paper_id": "arxiv:2609.39915",
      "source_url": "https://arxiv.org/html/2609.39915v1",
      "locator": "固定版完整摘要；abs L16–19 / HTML L83–87; §3.1–3.5 L125–163; §4.1–4.5、Tables 1–3 L164–250; §5 L264–268；Appendix D后段及E L486–500",
      "statement": "局部目标→执行→观测验证→继续/修订/推进→完成段压缩。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "3d-mem:e1",
      "paper_id": "3d-mem",
      "source_url": "https://arxiv.org/html/2411.17735v5",
      "locator": "§3.2–3.3",
      "statement": "以相关对象类别预筛选快照；探索使用Habitat-sim pathfinder在已探索区域计算无碰撞路径。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "3d-mem:e2",
      "paper_id": "3d-mem",
      "source_url": "https://arxiv.org/html/2411.17735v5",
      "locator": "§4.1、§4.3、Appendix §6",
      "statement": "主表A-EQA为184问题子集，GOAT-Bench为278子任务子集；全量结果另列。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "3d-mem:pipeline",
      "paper_id": "3d-mem",
      "source_url": "https://arxiv.org/html/2411.17735v5",
      "locator": "CVPR2025官方元数据与完整摘要; arXiv v5完整摘要 L59–63; §3.1–3.3 L107–202; §4.1–4.3 Tables 1–3 L203–278; Appendix §6全量与子集区分 L283–292",
      "statement": "共可见聚类→增量快照→按目标预筛选→回答或探索。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "ham-vln:e1",
      "paper_id": "ham-vln",
      "source_url": "https://arxiv.org/html/2607.29600v1",
      "locator": "§3.2–3.3，Eq.2–5；HTML L125–176",
      "statement": "同次规划返回动作与记忆更新；旧历史由相关性、时近性、显著性及一跳拓扑检索。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "ham-vln:e2",
      "paper_id": "ham-vln",
      "source_url": "https://arxiv.org/html/2607.29600v1",
      "locator": "§3.4、Algorithm 1；HTML L177–225",
      "statement": "回退理由附于放弃的地点；检索到该处才重读。失败笔记不改得分、不禁止访问。",
      "attribution": "author_claim",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "method"
    },
    {
      "evidence_id": "ham-vln:e3",
      "paper_id": "ham-vln",
      "source_url": "https://arxiv.org/html/2607.29600v1",
      "locator": "§4.1；HTML L253–261；PDF p.5",
      "statement": "三基准各100条val-unseen子集、3次运行；工作窗口K=1。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "ham-vln:e4",
      "paper_id": "ham-vln",
      "source_url": "https://arxiv.org/html/2607.29600v1",
      "locator": "§4.3 Table 3；HTML L272–310；PDF p.7",
      "statement": "R2R-CE：244.9k API tokens/episode；相较全历史降67.2%，相较K=3降34.8%。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "ham-vln:e5",
      "paper_id": "ham-vln",
      "source_url": "https://arxiv.org/html/2607.29600v1",
      "locator": "§4.4 Table 4；HTML L311–328；PDF pp.6–7",
      "statement": "固定规划、定位及控制器；去反思记忆仍保留回退，SR 61.0→55.7，SPL 48.1→36.9。",
      "attribution": "direct_observation",
      "verification_origin": "existing_review_record_reused_not_re_read_here",
      "kind": "protocol"
    },
    {
      "evidence_id": "ham-vln:pipeline",
      "paper_id": "ham-vln",
      "source_url": "https://arxiv.org/html/2607.29600v1",
      "locator": "固定v1完整摘要：HTML L56–60；PDF p.1 Abstract; §3.1–3.4及Algorithm 1：HTML L107–225；PDF pp.2–5; §4.1–4.5、Tables 1–4与§5：HTML L226–336；PDF pp.5–7; arXiv v1摘要页元数据与提交历史；PDF末页范围及appendix引用定位核对",
      "statement": "观察与检索→决策及写回→执行／回退→下一航点。",
      "attribution": "curator_summary_of_reviewed_sections",
      "verification_origin": "existing_pipeline_summary_requires_finer_claim_locator",
      "kind": "method_summary"
    },
    {
      "evidence_id": "krantz2023ivln:refresh",
      "paper_id": "krantz2023ivln",
      "source_url": "https://arxiv.org/html/2210.03087v3",
      "locator": "§3; §4.2.1–4.2.2",
      "statement": "IVLN允许tour内跨指令保留经验；MAP-CMA把深度与语义投影为占据/语义栅格，编码自中心局部裁剪用于动作预测；隐状态持久化作为不同对照。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "goat:refresh",
      "paper_id": "goat",
      "source_url": "https://arxiv.org/html/2311.06430v1",
      "locator": "§2.1–2.2 GOAT Agent / Instance Matching Strategy; §4.1",
      "statement": "按实例保存位置和多视角图像；新目标先检索实例记忆，命中用记忆位置导航，否则探索；语言目标用CLIP、图像目标用SuperGlue匹配。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "goat-bench:refresh",
      "paper_id": "goat-bench",
      "source_url": "https://arxiv.org/html/2404.06609v1",
      "locator": "§3 Task; §5.1–5.2 Baselines; §7.1–7.2",
      "statement": "同一场景连续给5–10个多模态子目标；比较显式实例地图与GRU持久状态；按模态分项，并用每子任务清空地图/隐状态检验利用以往经验的效果。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "batra2020objectnav:refresh",
      "paper_id": "batra2020objectnav",
      "source_url": "https://arxiv.org/html/2006.13171v2",
      "locator": "§2 ObjectNav Task Definition; §2.1 Object Finding and Evaluation",
      "statement": "规定类别目标任务，并将成功分成STOP意图、位置合法、目标表面距离和可见性；允许单列oracle-visibility变体，要求明确本体与场景条件。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "lfg:rationale",
      "paper_id": "lfg",
      "source_url": "https://proceedings.mlr.press/v229/shah23c/shah23c.pdf",
      "locator": "§1 Introduction; §2 Related Work; §3 Problem Formulation（本轮公开正式PDF定向复核）",
      "statement": "作者指出语言叙事不掌握当前真实空间，可能错误；因此用其启发专用规划器而非依赖完整好计划，规划器可在预测不适用时覆盖语言建议。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "esc:rationale",
      "paper_id": "esc",
      "source_url": "https://proceedings.mlr.press/v202/zhou23r/zhou23r.pdf",
      "locator": "§1 Introduction; §2 Problem Definition（本轮公开正式PDF定向复核）",
      "statement": "作者把常识到动作的缺口及物体—房间关系非确定性作为关键困难，用连续值软逻辑谓词约束frontier选择。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "imaginenav:rationale",
      "paper_id": "imaginenav",
      "source_url": "https://proceedings.iclr.cc/paper_files/paper/2025/file/eb261df4322a8bd0a73093c4d8a0d02d-Paper-Conference.pdf",
      "locator": "Abstract; §1 Introduction（本轮公开正式PDF定向复核）",
      "statement": "作者认为文字化语义地图难充分表达几何和物体细节，VLM也不宜直接产出连续3D航点；把规划转为候选想象视图选择，再由PointNav到达相应位姿。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "voronav:abstract-refresh",
      "paper_id": "voronav",
      "source_url": "https://arxiv.org/html/2401.02695v2",
      "locator": "完整Abstract（本轮公开抽取只返回摘要）",
      "statement": "作者用Reduced Voronoi Graph组织探索路径与规划节点，并组合路径与远视描述为LLM提供环境上下文；本轮未新核完整正文。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_complete_abstract_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "trihelper:rationale",
      "paper_id": "trihelper",
      "source_url": "https://arxiv.org/html/2403.15223v1",
      "locator": "§I Introduction（本次公开正文定向复核）",
      "statement": "作者按碰撞、低效探索与目标误识别分解零样本导航失败，指出单一整体策略忽略这些具体失败，因而设计按情况触发的专门辅助。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "hypothesis-graph-refinement:rationale",
      "paper_id": "hypothesis-graph-refinement",
      "source_url": "https://arxiv.org/html/2604.04108v1",
      "locator": "Abstract; §1 Introduction（本次公开正文定向复核）",
      "statement": "作者认为错误预测会沿依赖链累积，单纯置信衰减保留错误子图；需要可修订假设与依赖撤回，同时利用预测进行定向探索。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "ham-vln:rationale",
      "paper_id": "ham-vln",
      "source_url": "https://arxiv.org/html/2607.29600v1",
      "locator": "§1 Introduction（本次公开正文定向复核）",
      "statement": "作者把瓶颈定位为后续决策需要地点、进度与失败经验，但不能无限增加上下文；动作决策同次写入，再按当前子目标检索旧经验。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "arxiv:2609.39915:rationale",
      "paper_id": "arxiv:2609.39915",
      "source_url": "https://arxiv.org/html/2609.39915v1",
      "locator": "完整Abstract（本轮公开抽取只返回摘要，正文依据原记录）",
      "statement": "作者指出局部动作看似合理不保证长程路线一致；按目标专属问题核查观察结果，验证完成为历史压缩提供边界。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_complete_abstract_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "3d-mem:rationale",
      "paper_id": "3d-mem",
      "source_url": "https://arxiv.org/html/2411.17735v5",
      "locator": "§1 Introduction（本次公开正文定向复核）",
      "statement": "作者认为对象图的有限文字关系会丢失细致空间关系，密集3D表示又难扩展且不利于现成VLM读取；快照保留共可见对象、空间关系和背景，并以frontier快照表示未知。",
      "attribution": "author_method_paraphrase",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "method_or_protocol"
    },
    {
      "evidence_id": "3d-mem:navmesh",
      "paper_id": "3d-mem",
      "source_url": "https://arxiv.org/html/2411.17735v5",
      "locator": "Appendix §11（本次公开正文定向复核）",
      "statement": "实际采用Habitat-sim pathfinder，使用global navmesh prior计算最短路径；可换普通基于可导航图规划器只是作者提出的替代可能，非已评测配置。",
      "attribution": "direct_observation",
      "verification_origin": "primary_targeted_body_rechecked_in_this_rebuild",
      "kind": "protocol"
    }
  ],
  "edge_semantics": "editorial_problem_solution_mapping_not_citation_or_inheritance",
  "academic_edges": [],
  "scope_note": "39条公开定向正文阅读记录的编辑综合候选；不是全领域穷尽，不声称39篇全文已读。树从任务条件下的共同困难开始，随后收集不同解决洞见，最后展开作者方法及论文证据。",
  "method_order": [
    "收集任务条件下可检验的共同challenge",
    "为每个challenge收集distinct insights；共性属编者综合",
    "展开同一insight的不同作者方法与协议条件",
    "保留作者claim与原文定位，标出相邻任务、待核及不能比较处"
  ],
  "attribution_policy": {
    "challenge": "editorial_synthesis：编者在语料范围内操作化共同困难，不冒充逐作者同一句问题陈述。",
    "insight": "editorial_synthesis_of_distinct_author_methods：共同原则是编者综合；method_claim是有来源的转述，不是直接引语。",
    "variant": "以作者方法证据/已读记录为依据，边界中保留不同假设和机制；仅pipeline支撑的精确claim标待细定位。",
    "diagnostic": "testable_difficulty是编者建议的检验问题，未运行新实验。",
    "evidence": "保留原记录author_claim/direct_observation；本次补核11篇指定正文段落另标primary_targeted_body_rechecked_in_this_rebuild；另有摘要补核。",
    "academic_relations": "本候选不含citation/inheritance边；papers间无自动学术继承连线。"
  },
  "relation_definitions": {
    "direct": "直接处理该具体子问题；不代表任务协议、指标或作者理论主张完全相同。",
    "adjacent": "共享困难/机制但目标任务、动作信息或输出有实质差别；不能当同任务结果。",
    "protocol": "规范/诊断该问题，或在benchmark中比较既有方法；不是新导航policy。"
  },
  "methods": [
    {
      "method_id": "esc:method",
      "paper_id": "esc",
      "node_kind": "method",
      "title": "ESC · 方法",
      "aspects": [
        {
          "variant_id": "I01-1:1",
          "insight_id": "I01-1",
          "claim": "用GLIP语义、DeBERTa关联与PSL软规则联合距离选frontier。",
          "evidence_refs": [
            "esc:e1",
            "esc:pipeline",
            "esc:rationale"
          ]
        }
      ]
    },
    {
      "method_id": "l3mvn:method",
      "paper_id": "l3mvn",
      "node_kind": "method",
      "title": "L3MVN · 方法",
      "aspects": [
        {
          "variant_id": "I01-1:2",
          "insight_id": "I01-1",
          "claim": "语义低分时回退cost-utility；局部FMM逐步重规划。",
          "evidence_refs": [
            "l3mvn:e1"
          ]
        }
      ]
    },
    {
      "method_id": "lfg:method",
      "paper_id": "lfg",
      "node_kind": "method",
      "title": "LFG · 方法",
      "aspects": [
        {
          "variant_id": "I01-1:3",
          "insight_id": "I01-1",
          "claim": "正负提示的采样启发与距离共同用于搜索；已见目标则从地图取位置。",
          "evidence_refs": [
            "lfg:e1",
            "lfg:pipeline",
            "lfg:rationale"
          ]
        }
      ]
    },
    {
      "method_id": "voronav:method",
      "paper_id": "voronav",
      "node_kind": "method",
      "title": "VoroNav · 方法",
      "aspects": [
        {
          "variant_id": "I01-2:1",
          "insight_id": "I01-2",
          "claim": "决策点与Reduced Voronoi Graph绑定，到节点转一圈采观测；拓扑奖励与语义评分配合。",
          "evidence_refs": [
            "voronav:e1",
            "voronav:pipeline"
          ]
        }
      ]
    },
    {
      "method_id": "imaginenav:method",
      "paper_id": "imaginenav",
      "node_kind": "method",
      "title": "ImagineNav · 方法",
      "aspects": [
        {
          "variant_id": "I01-3:1",
          "insight_id": "I01-3",
          "claim": "Where2Imagine提出位姿、NVS合成视图，VLM选后交PointNav，再用新观测循环。",
          "evidence_refs": [
            "imaginenav:pipeline",
            "imaginenav:e1",
            "imaginenav:e2",
            "imaginenav:rationale"
          ]
        },
        {
          "variant_id": "I03-3:2",
          "insight_id": "I03-3",
          "claim": "VLM从合成未来视图选择局部位姿，PointNav执行后再观察。",
          "evidence_refs": [
            "imaginenav:pipeline",
            "imaginenav:e1",
            "imaginenav:e2",
            "imaginenav:rationale"
          ]
        }
      ]
    },
    {
      "method_id": "engineering-outruns-intelligence:method",
      "paper_id": "engineering-outruns-intelligence",
      "node_kind": "method",
      "title": "Engineering Outruns Intelligence · 方法",
      "aspects": [
        {
          "variant_id": "I01-4:1",
          "insight_id": "I01-4",
          "claim": "保留InstructNav框架，比较几何FPE与轻量语义SHF。",
          "evidence_refs": [
            "engineering-outruns-intelligence:pipeline",
            "engineering-outruns-intelligence:e1",
            "engineering-outruns-intelligence:e2"
          ]
        }
      ]
    },
    {
      "method_id": "goat:method",
      "paper_id": "goat",
      "node_kind": "method",
      "title": "GOAT · 方法",
      "aspects": [
        {
          "variant_id": "I02-1:1",
          "insight_id": "I02-1",
          "claim": "Object Instance Memory保存定位后的多视角；CLIP语言匹配与SuperGlue图像匹配后导航至实例。",
          "evidence_refs": [
            "goat:refresh",
            "goat:e1"
          ]
        },
        {
          "variant_id": "I06-1:2",
          "insight_id": "I06-1",
          "claim": "新目标先查实例记忆，已见实例的位置成为局部导航目标，未命中再探索。",
          "evidence_refs": [
            "goat:refresh"
          ]
        }
      ]
    },
    {
      "method_id": "goat-bench:protocol",
      "paper_id": "goat-bench",
      "node_kind": "protocol",
      "title": "GOAT-Bench · 评测方案",
      "aspects": [
        {
          "variant_id": "I02-1:2",
          "insight_id": "I02-1",
          "claim": "Modular GOAT baseline用实例视图/CLIP特征及模态对应匹配；也与单一CLIP匹配baseline比较。",
          "evidence_refs": [
            "goat-bench:refresh"
          ]
        },
        {
          "variant_id": "I06-1:3",
          "insight_id": "I06-1",
          "claim": "benchmark比较持久地图与GRU状态，并提供子任务清空的对照。",
          "evidence_refs": [
            "goat-bench:refresh",
            "goat-bench:e3"
          ]
        },
        {
          "variant_id": "I11-3:1",
          "insight_id": "I11-3",
          "claim": "子任务SPL最短路从上一子任务实际结束位置起算，固定STOP及预算等协议。",
          "evidence_refs": [
            "goat-bench:e1",
            "goat-bench:e2",
            "goat-bench:refresh"
          ]
        },
        {
          "variant_id": "I12-1:2",
          "insight_id": "I12-1",
          "claim": "每子任务清空GOAT地图或monolithic隐状态，并按目标模态分析。",
          "evidence_refs": [
            "goat-bench:refresh",
            "goat-bench:e3"
          ]
        }
      ]
    },
    {
      "method_id": "werby2024hovsg:method",
      "paper_id": "werby2024hovsg",
      "node_kind": "method",
      "title": "HOV-SG · 方法",
      "aspects": [
        {
          "variant_id": "I02-2:1",
          "insight_id": "I02-2",
          "claim": "建立楼层—房间—物体图，分层查询，并关联跨楼层Voronoi路径图。",
          "evidence_refs": [
            "werby2024hovsg:e1"
          ]
        }
      ]
    },
    {
      "method_id": "sap-nav:method",
      "paper_id": "sap-nav",
      "node_kind": "method",
      "title": "SAP-Nav · 方法",
      "aspects": [
        {
          "variant_id": "I02-2:2",
          "insight_id": "I02-2",
          "claim": "QSSR以房间语义BEV和快照表达空间约束，AVV再验证候选。",
          "evidence_refs": [
            "sap-nav:pipeline",
            "sap-nav:e1"
          ]
        },
        {
          "variant_id": "I09-2:1",
          "insight_id": "I09-2",
          "claim": "AVV最多三次换位，以最高充分性视图验证；拒绝候选入黑名单。",
          "evidence_refs": [
            "sap-nav:e1",
            "sap-nav:e2"
          ]
        }
      ]
    },
    {
      "method_id": "anwar2025remembr:method",
      "paper_id": "anwar2025remembr",
      "node_kind": "method",
      "title": "ReMEmbR · 方法",
      "aspects": [
        {
          "variant_id": "I02-3:1",
          "insight_id": "I02-3",
          "claim": "VILA片段caption入库，LLM调用时间/空间/文本检索，输出答案及坐标。",
          "evidence_refs": [
            "anwar2025remembr:e1"
          ]
        },
        {
          "variant_id": "I06-4:1",
          "insight_id": "I06-4",
          "claim": "检索文本、时间、位置条件，迭代后输出结构化答案与坐标。",
          "evidence_refs": [
            "anwar2025remembr:e1",
            "anwar2025remembr:e2"
          ]
        }
      ]
    },
    {
      "method_id": "agenticnav-tool-harness:method",
      "paper_id": "agenticnav-tool-harness",
      "node_kind": "method",
      "title": "AgenticNav · 方法",
      "aspects": [
        {
          "variant_id": "I03-1:1",
          "insight_id": "I03-1",
          "claim": "query_depth反投影目标像素，move_to前检查障碍，按需召回视觉历史。",
          "evidence_refs": [
            "agenticnav-tool-harness:e1",
            "agenticnav-tool-harness:pipeline"
          ]
        },
        {
          "variant_id": "I05-1:2",
          "insight_id": "I05-1",
          "claim": "每步重建有界上下文，保留六步理由记录与按需历史图像查询。",
          "evidence_refs": [
            "agenticnav-tool-harness:e1",
            "agenticnav-tool-harness:pipeline",
            "agenticnav-tool-harness:e3"
          ]
        }
      ]
    },
    {
      "method_id": "vlmnav:method",
      "paper_id": "vlmnav",
      "node_kind": "method",
      "title": "VLMnav · 方法",
      "aspects": [
        {
          "variant_id": "I03-1:2",
          "insight_id": "I03-1",
          "claim": "深度与探索体素生成候选，再将空间动作投影到图像让VLM选择。",
          "evidence_refs": [
            "vlmnav:e1",
            "vlmnav:pipeline"
          ]
        },
        {
          "variant_id": "I08-3:1",
          "insight_id": "I08-3",
          "claim": "连续两次STOP才终止，首次STOP后去掉探索偏置。",
          "evidence_refs": [
            "vlmnav:e1",
            "vlmnav:pipeline"
          ]
        }
      ]
    },
    {
      "method_id": "instructnav:method",
      "paper_id": "instructnav",
      "node_kind": "method",
      "title": "InstructNav · 方法",
      "aspects": [
        {
          "variant_id": "I03-2:1",
          "insight_id": "I03-2",
          "claim": "四类value map组合目标，障碍屏蔽、A*规划及低层执行形成反馈回路。",
          "evidence_refs": [
            "instructnav:e1",
            "instructnav:pipeline"
          ]
        },
        {
          "variant_id": "I08-3:2",
          "insight_id": "I08-3",
          "claim": "DCoN Flag或VLM判断可触发停止。",
          "evidence_refs": [
            "instructnav:e1",
            "instructnav:pipeline"
          ]
        },
        {
          "variant_id": "I10-2:1",
          "insight_id": "I10-2",
          "claim": "无可导航点时反馈给视觉模型重预测，同时屏蔽障碍。",
          "evidence_refs": [
            "instructnav:e1",
            "instructnav:pipeline"
          ]
        }
      ]
    },
    {
      "method_id": "rajvanshi2024saynav:method",
      "paper_id": "rajvanshi2024saynav",
      "node_kind": "method",
      "title": "SayNav · 方法",
      "aspects": [
        {
          "variant_id": "I03-3:1",
          "insight_id": "I03-3",
          "claim": "在线层次图支持短期navigate/look计划，并调用PointNav执行。",
          "evidence_refs": [
            "rajvanshi2024saynav:e1",
            "rajvanshi2024saynav:e2"
          ]
        },
        {
          "variant_id": "I10-2:2",
          "insight_id": "I10-2",
          "claim": "navigate/look与PointNav反馈用于更新计划、探索或补观察。",
          "evidence_refs": [
            "rajvanshi2024saynav:e1"
          ]
        }
      ]
    },
    {
      "method_id": "qwen-robotnav:method",
      "paper_id": "qwen-robotnav",
      "node_kind": "method",
      "title": "Qwen-RobotNav · 方法",
      "aspects": [
        {
          "variant_id": "I03-3:3",
          "insight_id": "I03-3",
          "claim": "策略编码任务参数化视觉历史并预测waypoint轨迹，供上层agent配置。",
          "evidence_refs": [
            "qwen-robotnav:pipeline",
            "qwen-robotnav:e1"
          ]
        },
        {
          "variant_id": "I05-2:1",
          "insight_id": "I05-2",
          "claim": "按时间与相机权重分配有上下限的视觉token。",
          "evidence_refs": [
            "qwen-robotnav:e1",
            "qwen-robotnav:e2"
          ]
        }
      ]
    },
    {
      "method_id": "holoagent-0:method",
      "paper_id": "holoagent-0",
      "node_kind": "method",
      "title": "HoloAgent-0 · 方法",
      "aspects": [
        {
          "variant_id": "I03-3:4",
          "insight_id": "I03-3",
          "claim": "技能图调度导航技能，typed接口与ROS2状态反馈连接执行。",
          "evidence_refs": [
            "holoagent-0:e1",
            "holoagent-0:pipeline"
          ]
        },
        {
          "variant_id": "I07-4:1",
          "insight_id": "I07-4",
          "claim": "新观测、物体操作结果或用户纠正触发局部记忆更新。",
          "evidence_refs": [
            "holoagent-0:e1"
          ]
        },
        {
          "variant_id": "I10-3:1",
          "insight_id": "I10-3",
          "claim": "typed技能接口和ROS2状态总线支撑技能调度、反馈及记忆事件更新。",
          "evidence_refs": [
            "holoagent-0:e1",
            "holoagent-0:pipeline",
            "holoagent-0:e2"
          ]
        }
      ]
    },
    {
      "method_id": "harnessvln:method",
      "paper_id": "harnessvln",
      "node_kind": "method",
      "title": "HarnessVLN · 方法",
      "aspects": [
        {
          "variant_id": "I03-4:1",
          "insight_id": "I03-4",
          "claim": "动作派发前检查来源、几何和子目标，执行后更新事件与时空状态。",
          "evidence_refs": [
            "harnessvln:e1"
          ]
        },
        {
          "variant_id": "I08-1:1",
          "insight_id": "I08-1",
          "claim": "停止请求另验语义、几何和进度。",
          "evidence_refs": [
            "harnessvln:e1",
            "harnessvln:e2"
          ]
        }
      ]
    },
    {
      "method_id": "ma2019regretful:method",
      "paper_id": "ma2019regretful",
      "node_kind": "method",
      "title": "Regretful Agent · 方法",
      "aspects": [
        {
          "variant_id": "I04-1:1",
          "insight_id": "I04-1",
          "claim": "Regret Module比较相邻进度，Progress Marker给已访方向附估计。",
          "evidence_refs": [
            "ma2019regretful:e1",
            "ma2019regretful:e2"
          ]
        }
      ]
    },
    {
      "method_id": "mapgpt:method",
      "paper_id": "mapgpt",
      "node_kind": "method",
      "title": "MapGPT · 方法",
      "aspects": [
        {
          "variant_id": "I04-2:1",
          "insight_id": "I04-2",
          "claim": "在线文字拓扑图加上轮多步计划，逐步重规划。",
          "evidence_refs": [
            "mapgpt:pipeline",
            "mapgpt:e1"
          ]
        }
      ]
    },
    {
      "method_id": "navgpt2:method",
      "paper_id": "navgpt2",
      "node_kind": "method",
      "title": "NavGPT-2 · 方法",
      "aspects": [
        {
          "variant_id": "I04-2:2",
          "insight_id": "I04-2",
          "claim": "拓扑图策略全局选节点并沿最短图路径执行，保留已访与相邻未访节点。",
          "evidence_refs": [
            "navgpt2:e1",
            "navgpt2:pipeline"
          ]
        }
      ]
    },
    {
      "method_id": "ham-vln:method",
      "paper_id": "ham-vln",
      "node_kind": "method",
      "title": "HAM-VLN · 方法",
      "aspects": [
        {
          "variant_id": "I04-3:1",
          "insight_id": "I04-3",
          "claim": "回退理由附于放弃地点；到相关位置读取，不直接改变得分或禁止访问。",
          "evidence_refs": [
            "ham-vln:e2",
            "ham-vln:e5",
            "ham-vln:rationale"
          ]
        },
        {
          "variant_id": "I05-3:2",
          "insight_id": "I05-3",
          "claim": "同次规划返回动作与记忆写入，按相关性、时近性、显著性及一跳拓扑读历史。",
          "evidence_refs": [
            "ham-vln:e1",
            "ham-vln:e4",
            "ham-vln:rationale"
          ]
        }
      ]
    },
    {
      "method_id": "navgpt:method",
      "paper_id": "navgpt",
      "node_kind": "method",
      "title": "NavGPT · 方法",
      "aspects": [
        {
          "variant_id": "I05-1:1",
          "insight_id": "I05-1",
          "claim": "prompt manager组织视觉文字化观察、历史轨迹与摘要，交替推理/动作。",
          "evidence_refs": [
            "navgpt:pipeline",
            "navgpt:e1"
          ]
        }
      ]
    },
    {
      "method_id": "li2024memonav:method",
      "paper_id": "li2024memonav",
      "node_kind": "method",
      "title": "MemoNav · 方法",
      "aspects": [
        {
          "variant_id": "I05-3:1",
          "insight_id": "I05-3",
          "claim": "按注意力临时遗忘STM，global node聚合LTM，GATv2构建WM；换目标恢复节点。",
          "evidence_refs": [
            "li2024memonav:e1"
          ]
        }
      ]
    },
    {
      "method_id": "profocus:method",
      "paper_id": "profocus",
      "node_kind": "method",
      "title": "ProFocus · 方法",
      "aspects": [
        {
          "variant_id": "I05-3:3",
          "insight_id": "I05-3",
          "claim": "BD-MCTS筛航点，检索候选路径相关上下文供决策。",
          "evidence_refs": [
            "profocus:e1"
          ]
        },
        {
          "variant_id": "I09-1:1",
          "insight_id": "I09-1",
          "claim": "局部视觉查询循环针对当前全景裁剪，编排代理判断信息是否充分。",
          "evidence_refs": [
            "profocus:e1",
            "profocus:pipeline"
          ]
        }
      ]
    },
    {
      "method_id": "arxiv:2609.39915:method",
      "paper_id": "arxiv:2609.39915",
      "node_kind": "method",
      "title": "NavHarness · Adaptive Goals · 方法",
      "aspects": [
        {
          "variant_id": "I05-4:1",
          "insight_id": "I05-4",
          "claim": "验证完成推进目标并触发完成段压缩，保留关键帧和未完成状态。",
          "evidence_refs": [
            "arxiv:2609.39915:e1",
            "arxiv:2609.39915:e2",
            "arxiv:2609.39915:rationale"
          ]
        },
        {
          "variant_id": "I08-2:1",
          "insight_id": "I08-2",
          "claim": "验证返回未满足条件；修订不算完成，完成后推进并触发压缩。",
          "evidence_refs": [
            "arxiv:2609.39915:e1",
            "arxiv:2609.39915:e2",
            "arxiv:2609.39915:rationale"
          ]
        },
        {
          "variant_id": "I10-2:3",
          "insight_id": "I10-2",
          "claim": "观察验证未完成时继续或修订局部目标，修订不算完成。",
          "evidence_refs": [
            "arxiv:2609.39915:e1"
          ]
        }
      ]
    },
    {
      "method_id": "navmcp:method",
      "paper_id": "navmcp",
      "node_kind": "method",
      "title": "NavMCP · 方法",
      "aspects": [
        {
          "variant_id": "I05-5:1",
          "insight_id": "I05-5",
          "claim": "旅程摘要关联关键帧，账本保留正负证据及未解目标。",
          "evidence_refs": [
            "navmcp:e1",
            "navmcp:e2"
          ]
        },
        {
          "variant_id": "I09-4:1",
          "insight_id": "I09-4",
          "claim": "导航调用带模式、子目标、预算；返回关联关键帧的旅程证据并更新未解目标。",
          "evidence_refs": [
            "navmcp:e1",
            "navmcp:e2"
          ]
        }
      ]
    },
    {
      "method_id": "rana2023sayplan:method",
      "paper_id": "rana2023sayplan",
      "node_kind": "method",
      "title": "SayPlan · 方法",
      "aspects": [
        {
          "variant_id": "I05-6:1",
          "insight_id": "I05-6",
          "claim": "expand/contract操作层级场景图，仅暴露任务相关子图。",
          "evidence_refs": [
            "rana2023sayplan:e1"
          ]
        },
        {
          "variant_id": "I10-4:1",
          "insight_id": "I10-4",
          "claim": "Dijkstra补路径，verify_plan图模拟器返回失败信息，触发重规划。",
          "evidence_refs": [
            "rana2023sayplan:e1",
            "rana2023sayplan:e2"
          ]
        }
      ]
    },
    {
      "method_id": "krantz2023ivln:method",
      "paper_id": "krantz2023ivln",
      "node_kind": "method",
      "title": "IVLN · 方法",
      "aspects": [
        {
          "variant_id": "I06-1:1",
          "insight_id": "I06-1",
          "claim": "MAP-CMA利用tour持久语义/占据地图的自中心裁剪作为导航输入。",
          "evidence_refs": [
            "krantz2023ivln:refresh",
            "krantz2023ivln:e1",
            "krantz2023ivln:e2"
          ]
        }
      ]
    },
    {
      "method_id": "3d-mem:method",
      "paper_id": "3d-mem",
      "node_kind": "method",
      "title": "3D-Mem · 方法",
      "aspects": [
        {
          "variant_id": "I06-1:4",
          "insight_id": "I06-1",
          "claim": "GOAT子任务间保留3D快照记忆，当前目标从已有snapshot或frontier中选择。",
          "evidence_refs": [
            "3d-mem:pipeline",
            "3d-mem:e2",
            "3d-mem:navmesh"
          ]
        },
        {
          "variant_id": "I05-7:1",
          "insight_id": "I05-7",
          "claim": "以共可见对象组织memory snapshots，按相关类别预筛选，另保留frontier snapshots。",
          "evidence_refs": [
            "3d-mem:e1",
            "3d-mem:pipeline",
            "3d-mem:rationale",
            "3d-mem:navmesh"
          ]
        },
        {
          "variant_id": "I09-5:1",
          "insight_id": "I09-5",
          "claim": "VLM从Memory Snapshots与Frontier Snapshots选择已有证据或探索目标。",
          "evidence_refs": [
            "3d-mem:e1",
            "3d-mem:pipeline",
            "3d-mem:e2",
            "3d-mem:rationale",
            "3d-mem:navmesh"
          ]
        }
      ]
    },
    {
      "method_id": "xu2026memoir:method",
      "paper_id": "xu2026memoir",
      "node_kind": "method",
      "title": "Memoir · 方法",
      "aspects": [
        {
          "variant_id": "I06-2:1",
          "insight_id": "I06-2",
          "claim": "想象匹配检索观测与行为历史，扩展DUET的编码分支融合结果。",
          "evidence_refs": [
            "xu2026memoir:e1",
            "xu2026memoir:e2"
          ]
        }
      ]
    },
    {
      "method_id": "wang2026lmee:method",
      "paper_id": "wang2026lmee",
      "node_kind": "method",
      "title": "LMEE / MemoryExplorer · 方法",
      "aspects": [
        {
          "variant_id": "I06-3:1",
          "insight_id": "I06-3",
          "claim": "MemoryExplorer在GRPO中联合动作/frontier/回答/格式奖励，调用CLIP记忆检索。",
          "evidence_refs": [
            "wang2026lmee:e1",
            "wang2026lmee:e2"
          ]
        }
      ]
    },
    {
      "method_id": "navharness:method",
      "paper_id": "navharness",
      "node_kind": "method",
      "title": "NavHarness · 方法",
      "aspects": [
        {
          "variant_id": "I06-5:1",
          "insight_id": "I06-5",
          "claim": "恢复保留剩余任务预算，区分已搜索和有证据排除，原任务记录不可覆写。",
          "evidence_refs": [
            "navharness:e1",
            "navharness:e2",
            "navharness:e3"
          ]
        },
        {
          "variant_id": "I07-2:1",
          "insight_id": "I07-2",
          "claim": "任务交接区分已搜索与有证据排除，后继会话不能覆盖原任务记录。",
          "evidence_refs": [
            "navharness:e1",
            "navharness:e3"
          ]
        }
      ]
    },
    {
      "method_id": "hypothesis-graph-refinement:method",
      "paper_id": "hypothesis-graph-refinement",
      "node_kind": "method",
      "title": "HGR · 方法",
      "aspects": [
        {
          "variant_id": "I07-1:1",
          "insight_id": "I07-1",
          "claim": "验证失败删除该假设及传递依赖节点，避免错误预测持续传播。",
          "evidence_refs": [
            "hypothesis-graph-refinement:e1",
            "hypothesis-graph-refinement:rationale"
          ]
        }
      ]
    },
    {
      "method_id": "trihelper:method",
      "paper_id": "trihelper",
      "node_kind": "method",
      "title": "TriHelper · 方法",
      "aspects": [
        {
          "variant_id": "I07-3:1",
          "insight_id": "I07-3",
          "claim": "误检目标记录被遮蔽；超过阈值未找到目标可回到记录点。",
          "evidence_refs": [
            "trihelper:e1"
          ]
        },
        {
          "variant_id": "I10-1:1",
          "insight_id": "I10-1",
          "claim": "不可达或碰撞改向最大连通区中心；重复近目标使LM暂眠；误检屏蔽后再探索。",
          "evidence_refs": [
            "trihelper:pipeline",
            "trihelper:e1",
            "trihelper:e2",
            "trihelper:rationale"
          ]
        }
      ]
    },
    {
      "method_id": "discussnav:method",
      "paper_id": "discussnav",
      "node_kind": "method",
      "title": "DiscussNav · 方法",
      "aspects": [
        {
          "variant_id": "I08-4:1",
          "insight_id": "I08-4",
          "claim": "轨迹摘要和完成估计反馈进入动作决策，五路候选不一致时交决策检验。",
          "evidence_refs": [
            "discussnav:e1",
            "discussnav:pipeline"
          ]
        }
      ]
    },
    {
      "method_id": "safevantage:method",
      "paper_id": "safevantage",
      "node_kind": "method",
      "title": "SafeVantage · 方法",
      "aspects": [
        {
          "variant_id": "I09-3:1",
          "insight_id": "I09-3",
          "claim": "按预期决策损失下降及路程成本选视点，Yes需来自不同位置的几何一致支持。",
          "evidence_refs": [
            "safevantage:e1",
            "safevantage:e2"
          ]
        }
      ]
    },
    {
      "method_id": "batra2020objectnav:protocol",
      "paper_id": "batra2020objectnav",
      "node_kind": "protocol",
      "title": "ObjectNav Revisited · 评测方案",
      "aspects": [
        {
          "variant_id": "I11-1:1",
          "insight_id": "I11-1",
          "claim": "成功分STOP意图、位置合法、距物体表面与可见性；oracle-visibility作为不同选择。",
          "evidence_refs": [
            "batra2020objectnav:refresh",
            "batra2020objectnav:e2",
            "batra2020objectnav:e3"
          ]
        }
      ]
    },
    {
      "method_id": "krantz2020vlnce:protocol",
      "paper_id": "krantz2020vlnce",
      "node_kind": "protocol",
      "title": "VLN-CE · 评测方案",
      "aspects": [
        {
          "variant_id": "I11-2:1",
          "insight_id": "I11-2",
          "claim": "不提供位置/朝向或导航图、短程oracle；低层前进/转向/STOP决策。",
          "evidence_refs": [
            "krantz2020vlnce:e1",
            "krantz2020vlnce:e2",
            "krantz2020vlnce:e3"
          ]
        }
      ]
    },
    {
      "method_id": "goat:protocol",
      "paper_id": "goat",
      "node_kind": "protocol",
      "title": "GOAT · 评测方案",
      "aspects": [
        {
          "variant_id": "I11-3:2",
          "insight_id": "I11-3",
          "claim": "实机5–10目标序列按每目标成功和SPL报告，并明确STOP及距离阈值。",
          "evidence_refs": [
            "goat:e2",
            "goat:refresh"
          ]
        }
      ]
    },
    {
      "method_id": "krantz2023ivln:protocol",
      "paper_id": "krantz2023ivln",
      "node_kind": "protocol",
      "title": "IVLN · 评测方案",
      "aspects": [
        {
          "variant_id": "I12-1:1",
          "insight_id": "I12-1",
          "claim": "比较episode重置、tour保留与known map，并交叉训练/评测模式。",
          "evidence_refs": [
            "krantz2023ivln:e2",
            "krantz2023ivln:e3",
            "krantz2023ivln:refresh"
          ]
        }
      ]
    },
    {
      "method_id": "wang2026lmee:protocol",
      "paper_id": "wang2026lmee",
      "node_kind": "protocol",
      "title": "LMEE / MemoryExplorer · 评测方案",
      "aspects": [
        {
          "variant_id": "I12-2:1",
          "insight_id": "I12-2",
          "claim": "LMEE联合多目标导航与目标相关记忆QA，MemoryExplorer为其学习基线。",
          "evidence_refs": [
            "wang2026lmee:e1",
            "wang2026lmee:e2"
          ]
        }
      ]
    },
    {
      "method_id": "engineering-outruns-intelligence:protocol",
      "paper_id": "engineering-outruns-intelligence",
      "node_kind": "protocol",
      "title": "Engineering Outruns Intelligence · 评测方案",
      "aspects": [
        {
          "variant_id": "I12-3:1",
          "insight_id": "I12-3",
          "claim": "在同框架改变探索value map，并区分GT语义与GLEE检测条件。",
          "evidence_refs": [
            "engineering-outruns-intelligence:e1",
            "engineering-outruns-intelligence:e2",
            "engineering-outruns-intelligence:pipeline"
          ]
        }
      ]
    },
    {
      "method_id": "ham-vln:protocol",
      "paper_id": "ham-vln",
      "node_kind": "protocol",
      "title": "HAM-VLN · 评测方案",
      "aspects": [
        {
          "variant_id": "I12-3:2",
          "insight_id": "I12-3",
          "claim": "去反思记忆保留回退动作，固定规划/定位/控制器比较。",
          "evidence_refs": [
            "ham-vln:e5"
          ]
        }
      ]
    }
  ],
  "edges": [
    {
      "from": "C01",
      "to": "I01-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C01",
      "to": "I01-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C01",
      "to": "I01-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C01",
      "to": "I01-4",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C02",
      "to": "I02-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C02",
      "to": "I02-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C02",
      "to": "I02-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C03",
      "to": "I03-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C03",
      "to": "I03-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C03",
      "to": "I03-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C03",
      "to": "I03-4",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C04",
      "to": "I04-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C04",
      "to": "I04-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C04",
      "to": "I04-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C05",
      "to": "I05-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C05",
      "to": "I05-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C05",
      "to": "I05-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C05",
      "to": "I05-4",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C05",
      "to": "I05-5",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C05",
      "to": "I05-6",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C05",
      "to": "I05-7",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C06",
      "to": "I06-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C06",
      "to": "I06-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C06",
      "to": "I06-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C06",
      "to": "I06-4",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C06",
      "to": "I06-5",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C07",
      "to": "I07-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C07",
      "to": "I07-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C07",
      "to": "I07-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C07",
      "to": "I07-4",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C08",
      "to": "I08-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C08",
      "to": "I08-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C08",
      "to": "I08-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C08",
      "to": "I08-4",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C09",
      "to": "I09-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C09",
      "to": "I09-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C09",
      "to": "I09-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C09",
      "to": "I09-4",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C09",
      "to": "I09-5",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C10",
      "to": "I10-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C10",
      "to": "I10-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C10",
      "to": "I10-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C10",
      "to": "I10-4",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C11",
      "to": "I11-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C11",
      "to": "I11-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C11",
      "to": "I11-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C12",
      "to": "I12-1",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C12",
      "to": "I12-2",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "C12",
      "to": "I12-3",
      "type": "addressed_by",
      "attribution": "editorial_synthesis"
    },
    {
      "from": "I01-1",
      "to": "esc:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I01-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I01-1",
      "to": "l3mvn:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I01-1:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I01-1",
      "to": "lfg:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I01-1:3",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I01-2",
      "to": "voronav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I01-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I01-3",
      "to": "imaginenav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I01-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I01-4",
      "to": "engineering-outruns-intelligence:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I01-4:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I02-1",
      "to": "goat:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I02-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I02-1",
      "to": "goat-bench:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I02-1:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I02-2",
      "to": "werby2024hovsg:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I02-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I02-2",
      "to": "sap-nav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I02-2:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I02-3",
      "to": "anwar2025remembr:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I02-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I03-1",
      "to": "agenticnav-tool-harness:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I03-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I03-1",
      "to": "vlmnav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I03-1:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I03-2",
      "to": "instructnav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I03-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I03-3",
      "to": "rajvanshi2024saynav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I03-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I03-3",
      "to": "imaginenav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I03-3:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I03-3",
      "to": "qwen-robotnav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I03-3:3",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I03-3",
      "to": "holoagent-0:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I03-3:4",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I03-4",
      "to": "harnessvln:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I03-4:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I04-1",
      "to": "ma2019regretful:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I04-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I04-2",
      "to": "mapgpt:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I04-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I04-2",
      "to": "navgpt2:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I04-2:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I04-3",
      "to": "ham-vln:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I04-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-1",
      "to": "navgpt:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I05-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-1",
      "to": "agenticnav-tool-harness:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I05-1:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-2",
      "to": "qwen-robotnav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I05-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-3",
      "to": "li2024memonav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I05-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-3",
      "to": "ham-vln:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I05-3:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-3",
      "to": "profocus:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I05-3:3",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-4",
      "to": "arxiv:2609.39915:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I05-4:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-5",
      "to": "navmcp:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I05-5:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-6",
      "to": "rana2023sayplan:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I05-6:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I06-1",
      "to": "krantz2023ivln:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I06-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I06-1",
      "to": "goat:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I06-1:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I06-1",
      "to": "goat-bench:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I06-1:3",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I06-1",
      "to": "3d-mem:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I06-1:4",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I06-2",
      "to": "xu2026memoir:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I06-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I06-3",
      "to": "wang2026lmee:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I06-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I06-4",
      "to": "anwar2025remembr:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I06-4:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I06-5",
      "to": "navharness:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I06-5:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I07-1",
      "to": "hypothesis-graph-refinement:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I07-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I07-2",
      "to": "navharness:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I07-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I07-3",
      "to": "trihelper:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I07-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I07-4",
      "to": "holoagent-0:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I07-4:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I08-1",
      "to": "harnessvln:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I08-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I08-2",
      "to": "arxiv:2609.39915:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I08-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I08-3",
      "to": "vlmnav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I08-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I08-3",
      "to": "instructnav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I08-3:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I08-4",
      "to": "discussnav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I08-4:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I09-1",
      "to": "profocus:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I09-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I09-2",
      "to": "sap-nav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I09-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I09-3",
      "to": "safevantage:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I09-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I09-4",
      "to": "navmcp:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I09-4:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I10-1",
      "to": "trihelper:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I10-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I10-2",
      "to": "instructnav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I10-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I10-2",
      "to": "rajvanshi2024saynav:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I10-2:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I10-2",
      "to": "arxiv:2609.39915:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I10-2:3",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I10-3",
      "to": "holoagent-0:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I10-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I10-4",
      "to": "rana2023sayplan:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I10-4:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I11-1",
      "to": "batra2020objectnav:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I11-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I11-2",
      "to": "krantz2020vlnce:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I11-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I11-3",
      "to": "goat-bench:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I11-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I11-3",
      "to": "goat:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I11-3:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I12-1",
      "to": "krantz2023ivln:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I12-1:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I12-1",
      "to": "goat-bench:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I12-1:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I12-2",
      "to": "wang2026lmee:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I12-2:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I12-3",
      "to": "engineering-outruns-intelligence:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I12-3:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I12-3",
      "to": "ham-vln:protocol",
      "type": "operationalized_by",
      "relation_to_challenge": "protocol",
      "variant_id": "I12-3:2",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I05-7",
      "to": "3d-mem:method",
      "type": "instantiated_by",
      "relation_to_challenge": "direct",
      "variant_id": "I05-7:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "I09-5",
      "to": "3d-mem:method",
      "type": "instantiated_by",
      "relation_to_challenge": "adjacent",
      "variant_id": "I09-5:1",
      "attribution": "editorial_mapping"
    },
    {
      "from": "esc:method",
      "to": "esc",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "esc:method",
      "to": "esc:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "esc:method",
      "to": "esc:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "esc:method",
      "to": "esc:rationale",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "l3mvn:method",
      "to": "l3mvn",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "l3mvn:method",
      "to": "l3mvn:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "lfg:method",
      "to": "lfg",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "lfg:method",
      "to": "lfg:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "lfg:method",
      "to": "lfg:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "lfg:method",
      "to": "lfg:rationale",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "voronav:method",
      "to": "voronav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "voronav:method",
      "to": "voronav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "voronav:method",
      "to": "voronav:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "imaginenav:method",
      "to": "imaginenav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "imaginenav:method",
      "to": "imaginenav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "imaginenav:method",
      "to": "imaginenav:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "imaginenav:method",
      "to": "imaginenav:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "imaginenav:method",
      "to": "imaginenav:rationale",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "engineering-outruns-intelligence:method",
      "to": "engineering-outruns-intelligence",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "engineering-outruns-intelligence:method",
      "to": "engineering-outruns-intelligence:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "engineering-outruns-intelligence:method",
      "to": "engineering-outruns-intelligence:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "engineering-outruns-intelligence:method",
      "to": "engineering-outruns-intelligence:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "goat:method",
      "to": "goat",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "goat:method",
      "to": "goat:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "goat:method",
      "to": "goat:refresh",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "goat-bench:protocol",
      "to": "goat-bench",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "goat-bench:protocol",
      "to": "goat-bench:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "goat-bench:protocol",
      "to": "goat-bench:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "goat-bench:protocol",
      "to": "goat-bench:e3",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "goat-bench:protocol",
      "to": "goat-bench:refresh",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "werby2024hovsg:method",
      "to": "werby2024hovsg",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "werby2024hovsg:method",
      "to": "werby2024hovsg:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "sap-nav:method",
      "to": "sap-nav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "sap-nav:method",
      "to": "sap-nav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "sap-nav:method",
      "to": "sap-nav:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "sap-nav:method",
      "to": "sap-nav:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "anwar2025remembr:method",
      "to": "anwar2025remembr",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "anwar2025remembr:method",
      "to": "anwar2025remembr:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "anwar2025remembr:method",
      "to": "anwar2025remembr:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "agenticnav-tool-harness:method",
      "to": "agenticnav-tool-harness",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "agenticnav-tool-harness:method",
      "to": "agenticnav-tool-harness:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "agenticnav-tool-harness:method",
      "to": "agenticnav-tool-harness:e3",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "agenticnav-tool-harness:method",
      "to": "agenticnav-tool-harness:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "vlmnav:method",
      "to": "vlmnav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "vlmnav:method",
      "to": "vlmnav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "vlmnav:method",
      "to": "vlmnav:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "instructnav:method",
      "to": "instructnav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "instructnav:method",
      "to": "instructnav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "instructnav:method",
      "to": "instructnav:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "rajvanshi2024saynav:method",
      "to": "rajvanshi2024saynav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "rajvanshi2024saynav:method",
      "to": "rajvanshi2024saynav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "rajvanshi2024saynav:method",
      "to": "rajvanshi2024saynav:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "qwen-robotnav:method",
      "to": "qwen-robotnav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "qwen-robotnav:method",
      "to": "qwen-robotnav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "qwen-robotnav:method",
      "to": "qwen-robotnav:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "qwen-robotnav:method",
      "to": "qwen-robotnav:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "holoagent-0:method",
      "to": "holoagent-0",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "holoagent-0:method",
      "to": "holoagent-0:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "holoagent-0:method",
      "to": "holoagent-0:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "holoagent-0:method",
      "to": "holoagent-0:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "harnessvln:method",
      "to": "harnessvln",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "harnessvln:method",
      "to": "harnessvln:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "harnessvln:method",
      "to": "harnessvln:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "ma2019regretful:method",
      "to": "ma2019regretful",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "ma2019regretful:method",
      "to": "ma2019regretful:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "ma2019regretful:method",
      "to": "ma2019regretful:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "mapgpt:method",
      "to": "mapgpt",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "mapgpt:method",
      "to": "mapgpt:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "mapgpt:method",
      "to": "mapgpt:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navgpt2:method",
      "to": "navgpt2",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "navgpt2:method",
      "to": "navgpt2:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navgpt2:method",
      "to": "navgpt2:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "ham-vln:method",
      "to": "ham-vln",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "ham-vln:method",
      "to": "ham-vln:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "ham-vln:method",
      "to": "ham-vln:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "ham-vln:method",
      "to": "ham-vln:e4",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "ham-vln:method",
      "to": "ham-vln:e5",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "ham-vln:method",
      "to": "ham-vln:rationale",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navgpt:method",
      "to": "navgpt",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "navgpt:method",
      "to": "navgpt:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navgpt:method",
      "to": "navgpt:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "li2024memonav:method",
      "to": "li2024memonav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "li2024memonav:method",
      "to": "li2024memonav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "profocus:method",
      "to": "profocus",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "profocus:method",
      "to": "profocus:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "profocus:method",
      "to": "profocus:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "arxiv:2609.39915:method",
      "to": "arxiv:2609.39915",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "arxiv:2609.39915:method",
      "to": "arxiv:2609.39915:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "arxiv:2609.39915:method",
      "to": "arxiv:2609.39915:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "arxiv:2609.39915:method",
      "to": "arxiv:2609.39915:rationale",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navmcp:method",
      "to": "navmcp",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "navmcp:method",
      "to": "navmcp:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navmcp:method",
      "to": "navmcp:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "rana2023sayplan:method",
      "to": "rana2023sayplan",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "rana2023sayplan:method",
      "to": "rana2023sayplan:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "rana2023sayplan:method",
      "to": "rana2023sayplan:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2023ivln:method",
      "to": "krantz2023ivln",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "krantz2023ivln:method",
      "to": "krantz2023ivln:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2023ivln:method",
      "to": "krantz2023ivln:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2023ivln:method",
      "to": "krantz2023ivln:refresh",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "3d-mem:method",
      "to": "3d-mem",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "3d-mem:method",
      "to": "3d-mem:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "3d-mem:method",
      "to": "3d-mem:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "3d-mem:method",
      "to": "3d-mem:navmesh",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "3d-mem:method",
      "to": "3d-mem:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "3d-mem:method",
      "to": "3d-mem:rationale",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "xu2026memoir:method",
      "to": "xu2026memoir",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "xu2026memoir:method",
      "to": "xu2026memoir:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "xu2026memoir:method",
      "to": "xu2026memoir:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "wang2026lmee:method",
      "to": "wang2026lmee",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "wang2026lmee:method",
      "to": "wang2026lmee:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "wang2026lmee:method",
      "to": "wang2026lmee:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navharness:method",
      "to": "navharness",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "navharness:method",
      "to": "navharness:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navharness:method",
      "to": "navharness:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "navharness:method",
      "to": "navharness:e3",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "hypothesis-graph-refinement:method",
      "to": "hypothesis-graph-refinement",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "hypothesis-graph-refinement:method",
      "to": "hypothesis-graph-refinement:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "hypothesis-graph-refinement:method",
      "to": "hypothesis-graph-refinement:rationale",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "trihelper:method",
      "to": "trihelper",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "trihelper:method",
      "to": "trihelper:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "trihelper:method",
      "to": "trihelper:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "trihelper:method",
      "to": "trihelper:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "trihelper:method",
      "to": "trihelper:rationale",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "discussnav:method",
      "to": "discussnav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "discussnav:method",
      "to": "discussnav:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "discussnav:method",
      "to": "discussnav:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "safevantage:method",
      "to": "safevantage",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "safevantage:method",
      "to": "safevantage:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "safevantage:method",
      "to": "safevantage:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "batra2020objectnav:protocol",
      "to": "batra2020objectnav",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "batra2020objectnav:protocol",
      "to": "batra2020objectnav:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "batra2020objectnav:protocol",
      "to": "batra2020objectnav:e3",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "batra2020objectnav:protocol",
      "to": "batra2020objectnav:refresh",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2020vlnce:protocol",
      "to": "krantz2020vlnce",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "krantz2020vlnce:protocol",
      "to": "krantz2020vlnce:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2020vlnce:protocol",
      "to": "krantz2020vlnce:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2020vlnce:protocol",
      "to": "krantz2020vlnce:e3",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "goat:protocol",
      "to": "goat",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "goat:protocol",
      "to": "goat:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "goat:protocol",
      "to": "goat:refresh",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2023ivln:protocol",
      "to": "krantz2023ivln",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "krantz2023ivln:protocol",
      "to": "krantz2023ivln:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2023ivln:protocol",
      "to": "krantz2023ivln:e3",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "krantz2023ivln:protocol",
      "to": "krantz2023ivln:refresh",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "wang2026lmee:protocol",
      "to": "wang2026lmee",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "wang2026lmee:protocol",
      "to": "wang2026lmee:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "wang2026lmee:protocol",
      "to": "wang2026lmee:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "engineering-outruns-intelligence:protocol",
      "to": "engineering-outruns-intelligence",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "engineering-outruns-intelligence:protocol",
      "to": "engineering-outruns-intelligence:e1",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "engineering-outruns-intelligence:protocol",
      "to": "engineering-outruns-intelligence:e2",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "engineering-outruns-intelligence:protocol",
      "to": "engineering-outruns-intelligence:pipeline",
      "type": "supported_by",
      "attribution": "source_record"
    },
    {
      "from": "ham-vln:protocol",
      "to": "ham-vln",
      "type": "reported_in",
      "attribution": "bibliographic_identity"
    },
    {
      "from": "ham-vln:protocol",
      "to": "ham-vln:e5",
      "type": "supported_by",
      "attribution": "source_record"
    }
  ],
  "paper_mappings": {
    "harnessvln": [
      {
        "challenge_id": "C03",
        "insight_id": "I03-4",
        "method_id": "harnessvln:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "harnessvln:e1"
        ],
        "boundary": "memory→graph→stop累加消融不能独立归因每个检查项。"
      },
      {
        "challenge_id": "C08",
        "insight_id": "I08-1",
        "method_id": "harnessvln:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "harnessvln:e1",
          "harnessvln:e2"
        ],
        "boundary": "100 episode累加消融不是完整析因；不能隔离所有模块贡献。"
      }
    ],
    "navharness": [
      {
        "challenge_id": "C06",
        "insight_id": "I06-5",
        "method_id": "navharness:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "navharness:e1",
          "navharness:e2",
          "navharness:e3"
        ],
        "boundary": "2609.34276 Lifelong；静态模拟、judge可能误判，占据图回环不自动校正。"
      },
      {
        "challenge_id": "C07",
        "insight_id": "I07-2",
        "method_id": "navharness:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "navharness:e1",
          "navharness:e3"
        ],
        "boundary": "不自动解决SLAM回环导致旧地图坐标不一致。"
      }
    ],
    "agenticnav-tool-harness": [
      {
        "challenge_id": "C03",
        "insight_id": "I03-1",
        "method_id": "agenticnav-tool-harness:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "agenticnav-tool-harness:e1",
          "agenticnav-tool-harness:pipeline"
        ],
        "boundary": "episode内；R2R-CE子集和指定模型条件，未读代码。"
      },
      {
        "challenge_id": "C05",
        "insight_id": "I05-1",
        "method_id": "agenticnav-tool-harness:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "agenticnav-tool-harness:e1",
          "agenticnav-tool-harness:pipeline",
          "agenticnav-tool-harness:e3"
        ],
        "boundary": "进度文本表现差的作者解释不能当已验证一般因果规律。"
      }
    ],
    "qwen-robotnav": [
      {
        "challenge_id": "C03",
        "insight_id": "I03-3",
        "method_id": "qwen-robotnav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "qwen-robotnav:pipeline",
          "qwen-robotnav:e1"
        ],
        "boundary": "这是导航模型接口；不由接口存在推断上层验证或恢复机制。"
      },
      {
        "challenge_id": "C05",
        "insight_id": "I05-2",
        "method_id": "qwen-robotnav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "qwen-robotnav:e1",
          "qwen-robotnav:e2"
        ],
        "boundary": "500条R2R预算扫描收益非严格单调；不可宣称普适最优分配。"
      }
    ],
    "holoagent-0": [
      {
        "challenge_id": "C03",
        "insight_id": "I03-3",
        "method_id": "holoagent-0:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "holoagent-0:e1",
          "holoagent-0:pipeline"
        ],
        "boundary": "导航定量与全技能定性分别解释；仅技能分工不证明所有技能稳健。"
      },
      {
        "challenge_id": "C07",
        "insight_id": "I07-4",
        "method_id": "holoagent-0:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "holoagent-0:e1"
        ],
        "boundary": "静态导航定量与全技能定性分开，未证明长期动态适应。"
      },
      {
        "challenge_id": "C10",
        "insight_id": "I10-3",
        "method_id": "holoagent-0:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "holoagent-0:e1",
          "holoagent-0:pipeline",
          "holoagent-0:e2"
        ],
        "boundary": "全技能演示无统一端到端成功率，不能宣称全栈可靠。"
      }
    ],
    "krantz2023ivln": [
      {
        "challenge_id": "C06",
        "insight_id": "I06-1",
        "method_id": "krantz2023ivln:method",
        "relation_to_challenge": "direct",
        "mapping_status": "primary_method_rechecked",
        "evidence_refs": [
          "krantz2023ivln:refresh",
          "krantz2023ivln:e1",
          "krantz2023ivln:e2"
        ],
        "boundary": "与latent baselines有训练差异，oracle观察需单列。"
      },
      {
        "challenge_id": "C12",
        "insight_id": "I12-1",
        "method_id": "krantz2023ivln:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "krantz2023ivln:e2",
          "krantz2023ivln:e3",
          "krantz2023ivln:refresh"
        ],
        "boundary": "oracle观察及DAgger训练差异需保留，不能说地图单一因果优势。"
      }
    ],
    "goat": [
      {
        "challenge_id": "C02",
        "insight_id": "I02-1",
        "method_id": "goat:method",
        "relation_to_challenge": "direct",
        "mapping_status": "primary_method_rechecked",
        "evidence_refs": [
          "goat:refresh",
          "goat:e1"
        ],
        "boundary": "定量实机测试15类别；探索期阈值匹配与探索后最高分策略不同。"
      },
      {
        "challenge_id": "C06",
        "insight_id": "I06-1",
        "method_id": "goat:method",
        "relation_to_challenge": "direct",
        "mapping_status": "primary_method_rechecked",
        "evidence_refs": [
          "goat:refresh"
        ],
        "boundary": "5–10目标实机序列；类别/描述/图像目标分列。"
      },
      {
        "challenge_id": "C11",
        "insight_id": "I11-3",
        "method_id": "goat:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "goat:e2",
          "goat:refresh"
        ],
        "boundary": "本体控制器不同；实机15类不等同开放词汇任意类别实证。"
      }
    ],
    "goat-bench": [
      {
        "challenge_id": "C02",
        "insight_id": "I02-1",
        "method_id": "goat-bench:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "primary_method_rechecked",
        "evidence_refs": [
          "goat-bench:refresh"
        ],
        "boundary": "这是benchmark内已归因给GOAT的baseline实现说明，不是GOAT-Bench独立发明同一机制。"
      },
      {
        "challenge_id": "C06",
        "insight_id": "I06-1",
        "method_id": "goat-bench:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "primary_method_rechecked",
        "evidence_refs": [
          "goat-bench:refresh",
          "goat-bench:e3"
        ],
        "boundary": "GOAT baseline是已发表机制的评测实例，不重复计为独立发明。"
      },
      {
        "challenge_id": "C11",
        "insight_id": "I11-3",
        "method_id": "goat-bench:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "goat-bench:e1",
          "goat-bench:e2",
          "goat-bench:refresh"
        ],
        "boundary": "Habitat/Stretch模拟，不能与Spot实机协议直接合并。"
      },
      {
        "challenge_id": "C12",
        "insight_id": "I12-1",
        "method_id": "goat-bench:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "goat-bench:refresh",
          "goat-bench:e3"
        ],
        "boundary": "同一干预可同时影响路线复用及实例匹配；不把总收益全归路线记忆。"
      }
    ],
    "krantz2020vlnce": [
      {
        "challenge_id": "C11",
        "insight_id": "I11-2",
        "method_id": "krantz2020vlnce:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "krantz2020vlnce:e1",
          "krantz2020vlnce:e2",
          "krantz2020vlnce:e3"
        ],
        "boundary": "图/连续对比受轨迹筛除和转换误差影响，原始SPL不可直接排名。"
      }
    ],
    "batra2020objectnav": [
      {
        "challenge_id": "C11",
        "insight_id": "I11-1",
        "method_id": "batra2020objectnav:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "primary_protocol_rechecked",
        "evidence_refs": [
          "batra2020objectnav:refresh",
          "batra2020objectnav:e2",
          "batra2020objectnav:e3"
        ],
        "boundary": "论文建议不代表所有后续实现采用完全一致细则。"
      }
    ],
    "navgpt": [
      {
        "challenge_id": "C05",
        "insight_id": "I05-1",
        "method_id": "navgpt:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "navgpt:pipeline",
          "navgpt:e1"
        ],
        "boundary": "作者指出视觉文字化与历史摘要会损失信息；不虚构原图可召回接口。"
      }
    ],
    "mapgpt": [
      {
        "challenge_id": "C04",
        "insight_id": "I04-2",
        "method_id": "mapgpt:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "mapgpt:pipeline",
          "mapgpt:e1"
        ],
        "boundary": "邻接候选来自模拟器；SR增加可伴随更长路径。"
      }
    ],
    "discussnav": [
      {
        "challenge_id": "C08",
        "insight_id": "I08-4",
        "method_id": "discussnav:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "discussnav:e1",
          "discussnav:pipeline"
        ],
        "boundary": "角色不代表独立模型；多次调用成本必须计入。"
      }
    ],
    "instructnav": [
      {
        "challenge_id": "C03",
        "insight_id": "I03-2",
        "method_id": "instructnav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "instructnav:e1",
          "instructnav:pipeline"
        ],
        "boundary": "闭源模型及遮挡影响；不把失败反馈自动升级为独立验证器。"
      },
      {
        "challenge_id": "C08",
        "insight_id": "I08-3",
        "method_id": "instructnav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "instructnav:e1",
          "instructnav:pipeline"
        ],
        "boundary": "OR式触发与两次确认不是相同机制；本次未核独立stop消融。"
      },
      {
        "challenge_id": "C10",
        "insight_id": "I10-2",
        "method_id": "instructnav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "instructnav:e1",
          "instructnav:pipeline"
        ],
        "boundary": "语义图受遮挡影响；不保证每类失败都能恢复。"
      }
    ],
    "esc": [
      {
        "challenge_id": "C01",
        "insight_id": "I01-1",
        "method_id": "esc:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "esc:e1",
          "esc:pipeline",
          "esc:rationale"
        ],
        "boundary": "PSL软约束，不是生成式自由工具调用；GPS等条件需单列。"
      }
    ],
    "l3mvn": [
      {
        "challenge_id": "C01",
        "insight_id": "I01-1",
        "method_id": "l3mvn:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "l3mvn:e1"
        ],
        "boundary": "语言评分/训练embedding head两支有别，非所有模块无训练。"
      }
    ],
    "lfg": [
      {
        "challenge_id": "C01",
        "insight_id": "I01-1",
        "method_id": "lfg:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "lfg:e1",
          "lfg:pipeline",
          "lfg:rationale"
        ],
        "boundary": "模拟baseline采用GT语义，不能当真实检测下的一致比较。"
      }
    ],
    "voronav": [
      {
        "challenge_id": "C01",
        "insight_id": "I01-2",
        "method_id": "voronav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "voronav:e1",
          "voronav:pipeline"
        ],
        "boundary": "在线派生可通行图，不等同模拟器给定VLN导航图。"
      }
    ],
    "trihelper": [
      {
        "challenge_id": "C07",
        "insight_id": "I07-3",
        "method_id": "trihelper:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "trihelper:e1"
        ],
        "boundary": "作者亦报告遮蔽可能引发失败；不能作为可靠负证据保证。"
      },
      {
        "challenge_id": "C10",
        "insight_id": "I10-1",
        "method_id": "trihelper:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "trihelper:pipeline",
          "trihelper:e1",
          "trihelper:e2",
          "trihelper:rationale"
        ],
        "boundary": "三个helper并用时探索失败反增，不能假定组合单调受益。"
      }
    ],
    "imaginenav": [
      {
        "challenge_id": "C01",
        "insight_id": "I01-3",
        "method_id": "imaginenav:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "imaginenav:pipeline",
          "imaginenav:e1",
          "imaginenav:e2",
          "imaginenav:rationale"
        ],
        "boundary": "未来真实图像Oracle与合成视图结果分开；不是frontier分数形式。"
      },
      {
        "challenge_id": "C03",
        "insight_id": "I03-3",
        "method_id": "imaginenav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "imaginenav:pipeline",
          "imaginenav:e1",
          "imaginenav:e2",
          "imaginenav:rationale"
        ],
        "boundary": "动作提案与视图合成有训练，不能据zero-shot称全系统免训练。"
      }
    ],
    "vlmnav": [
      {
        "challenge_id": "C03",
        "insight_id": "I03-1",
        "method_id": "vlmnav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "vlmnav:e1",
          "vlmnav:pipeline"
        ],
        "boundary": "可通行性未计机器人尺寸形状；allow_slide设置极大影响结果。"
      },
      {
        "challenge_id": "C08",
        "insight_id": "I08-3",
        "method_id": "vlmnav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "vlmnav:e1",
          "vlmnav:pipeline"
        ],
        "boundary": "这是重复确认，不是几何充分性证明。"
      }
    ],
    "navgpt2": [
      {
        "challenge_id": "C04",
        "insight_id": "I04-2",
        "method_id": "navgpt2:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "navgpt2:e1",
          "navgpt2:pipeline"
        ],
        "boundary": "Q-former与动作policy经训练并使用DUET图方法，非纯提示法。"
      }
    ],
    "engineering-outruns-intelligence": [
      {
        "challenge_id": "C01",
        "insight_id": "I01-4",
        "method_id": "engineering-outruns-intelligence:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "engineering-outruns-intelligence:pipeline",
          "engineering-outruns-intelligence:e1",
          "engineering-outruns-intelligence:e2"
        ],
        "boundary": "主表GT语义；GLEE子集上FPE SR不胜InstructNav。"
      },
      {
        "challenge_id": "C12",
        "insight_id": "I12-3",
        "method_id": "engineering-outruns-intelligence:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "engineering-outruns-intelligence:e1",
          "engineering-outruns-intelligence:e2",
          "engineering-outruns-intelligence:pipeline"
        ],
        "boundary": "语义检测条件可改变结论，不可概括为LLM无用。"
      }
    ],
    "ma2019regretful": [
      {
        "challenge_id": "C04",
        "insight_id": "I04-1",
        "method_id": "ma2019regretful:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "ma2019regretful:e1",
          "ma2019regretful:e2"
        ],
        "boundary": "R2R离散图；禁用回退不使所有指标下降，不写全面胜出。"
      }
    ],
    "rana2023sayplan": [
      {
        "challenge_id": "C05",
        "insight_id": "I05-6",
        "method_id": "rana2023sayplan:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "rana2023sayplan:e1"
        ],
        "boundary": "预建静态场景图任务规划；不是在线未知ObjectNav。"
      },
      {
        "challenge_id": "C10",
        "insight_id": "I10-4",
        "method_id": "rana2023sayplan:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "rana2023sayplan:e1",
          "rana2023sayplan:e2"
        ],
        "boundary": "图可执行不保证感知真实、物理安全或最终任务正确。"
      }
    ],
    "rajvanshi2024saynav": [
      {
        "challenge_id": "C03",
        "insight_id": "I03-3",
        "method_id": "rajvanshi2024saynav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "rajvanshi2024saynav:e1",
          "rajvanshi2024saynav:e2"
        ],
        "boundary": "ProcTHOR 3目标；GT/视觉图、oracle/学习控制器分列，完整验证仍被列为未来工作。"
      },
      {
        "challenge_id": "C10",
        "insight_id": "I10-2",
        "method_id": "rajvanshi2024saynav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "rajvanshi2024saynav:e1"
        ],
        "boundary": "完整计划验证被作者列为未来工作；可能重复尝试看不到的门状态。"
      }
    ],
    "li2024memonav": [
      {
        "challenge_id": "C05",
        "insight_id": "I05-3",
        "method_id": "li2024memonav:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "li2024memonav:e1"
        ],
        "boundary": "多目标ImageNav学习策略；节点仍留作定位，存储不减少。"
      }
    ],
    "werby2024hovsg": [
      {
        "challenge_id": "C02",
        "insight_id": "I02-2",
        "method_id": "werby2024hovsg:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "werby2024hovsg:e1"
        ],
        "boundary": "依赖先建图及里程计；41试次中检索与导航结果分开，非未知场景统一ObjectNav。"
      }
    ],
    "anwar2025remembr": [
      {
        "challenge_id": "C02",
        "insight_id": "I02-3",
        "method_id": "anwar2025remembr:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "anwar2025remembr:e1"
        ],
        "boundary": "主要评QA及目标定位；15米位置阈值不是近目标导航成功。"
      },
      {
        "challenge_id": "C06",
        "insight_id": "I06-4",
        "method_id": "anwar2025remembr:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "anwar2025remembr:e1",
          "anwar2025remembr:e2"
        ],
        "boundary": "NaVQA视频与实机部署说明；主要统计QA与时空定位。"
      }
    ],
    "xu2026memoir": [
      {
        "challenge_id": "C06",
        "insight_id": "I06-2",
        "method_id": "xu2026memoir:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "xu2026memoir:e1",
          "xu2026memoir:e2"
        ],
        "boundary": "IR2R/GSA-R2R及训练设置分列；不与工具harness作免训练同类比较。"
      }
    ],
    "wang2026lmee": [
      {
        "challenge_id": "C06",
        "insight_id": "I06-3",
        "method_id": "wang2026lmee:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "wang2026lmee:e1",
          "wang2026lmee:e2"
        ],
        "boundary": "LMEE基准与MemoryExplorer模型两角色；推理慢，voxel不支持多层。"
      },
      {
        "challenge_id": "C12",
        "insight_id": "I12-2",
        "method_id": "wang2026lmee:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "wang2026lmee:e1",
          "wang2026lmee:e2"
        ],
        "boundary": "主表58/166任务；GOAT子集对比与全量原论文基线分开。"
      }
    ],
    "navmcp": [
      {
        "challenge_id": "C05",
        "insight_id": "I05-5",
        "method_id": "navmcp:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "navmcp:e1",
          "navmcp:e2"
        ],
        "boundary": "HM-EQA/MT-HM3D/EXPRESS-Bench；EQA答案质量不是ObjectNav SR。"
      },
      {
        "challenge_id": "C09",
        "insight_id": "I09-4",
        "method_id": "navmcp:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "navmcp:e1",
          "navmcp:e2"
        ],
        "boundary": "仅保留终点观察的消融与整套接口消融不同，不当作memory-only因果证据。"
      }
    ],
    "sap-nav": [
      {
        "challenge_id": "C02",
        "insight_id": "I02-2",
        "method_id": "sap-nav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "sap-nav:pipeline",
          "sap-nav:e1"
        ],
        "boundary": "在线查询与主动验证；LangMap单目标/HM3D-OVON协议分列。"
      },
      {
        "challenge_id": "C09",
        "insight_id": "I09-2",
        "method_id": "sap-nav:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "sap-nav:e1",
          "sap-nav:e2"
        ],
        "boundary": "房间约束与实例属性目标；定性实机例不等于量化实机SR。"
      }
    ],
    "hypothesis-graph-refinement": [
      {
        "challenge_id": "C07",
        "insight_id": "I07-1",
        "method_id": "hypothesis-graph-refinement:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "hypothesis-graph-refinement:e1",
          "hypothesis-graph-refinement:rationale"
        ],
        "boundary": "A-EQA/EM-EQA/GOAT不同任务分开；重实现baseline与原版不等价。"
      }
    ],
    "safevantage": [
      {
        "challenge_id": "C09",
        "insight_id": "I09-3",
        "method_id": "safevantage:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "safevantage:e1",
          "safevantage:e2"
        ],
        "boundary": "category-presence macro-F1不是导航SR；连续执行与实机尚属后续评估。"
      }
    ],
    "profocus": [
      {
        "challenge_id": "C05",
        "insight_id": "I05-3",
        "method_id": "profocus:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "profocus:e1"
        ],
        "boundary": "路线图导航；不是持续跨episode经验检索。"
      },
      {
        "challenge_id": "C09",
        "insight_id": "I09-1",
        "method_id": "profocus:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "profocus:e1",
          "profocus:pipeline"
        ],
        "boundary": "REVERIE只评导航不评grounding；不可宣称真实移动主动感知效果。"
      }
    ],
    "arxiv:2609.39915": [
      {
        "challenge_id": "C05",
        "insight_id": "I05-4",
        "method_id": "arxiv:2609.39915:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "arxiv:2609.39915:e1",
          "arxiv:2609.39915:e2",
          "arxiv:2609.39915:rationale"
        ],
        "boundary": "压缩有部分SR/SPL代价；局部输入下降不等于整episode token下降。"
      },
      {
        "challenge_id": "C08",
        "insight_id": "I08-2",
        "method_id": "arxiv:2609.39915:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "arxiv:2609.39915:e1",
          "arxiv:2609.39915:e2",
          "arxiv:2609.39915:rationale"
        ],
        "boundary": "框架消融未分别隔离目标与验证；实机样本较小。"
      },
      {
        "challenge_id": "C10",
        "insight_id": "I10-2",
        "method_id": "arxiv:2609.39915:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "arxiv:2609.39915:e1"
        ],
        "boundary": "局部目标重设与最终成功验证是不同评估环节。"
      }
    ],
    "3d-mem": [
      {
        "challenge_id": "C06",
        "insight_id": "I06-1",
        "method_id": "3d-mem:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "3d-mem:pipeline",
          "3d-mem:e2",
          "3d-mem:navmesh"
        ],
        "boundary": "GOAT主表278子任务子集与全量分开。 实际执行使用global navmesh prior的Habitat pathfinder；替换普通规划器未在本次配置验证。"
      },
      {
        "challenge_id": "C05",
        "insight_id": "I05-7",
        "method_id": "3d-mem:method",
        "relation_to_challenge": "direct",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "3d-mem:e1",
          "3d-mem:pipeline",
          "3d-mem:rationale",
          "3d-mem:navmesh"
        ],
        "boundary": "主动A-EQA、被动EM-EQA与GOAT分开；快照不是所有原始图像。 实际执行使用global navmesh prior的Habitat pathfinder；替换普通规划器未在本次配置验证。"
      },
      {
        "challenge_id": "C09",
        "insight_id": "I09-5",
        "method_id": "3d-mem:method",
        "relation_to_challenge": "adjacent",
        "mapping_status": "candidate_requires_finer_locator",
        "evidence_refs": [
          "3d-mem:e1",
          "3d-mem:pipeline",
          "3d-mem:e2",
          "3d-mem:rationale",
          "3d-mem:navmesh"
        ],
        "boundary": "仅A-EQA/GOAT探索支持此路径；EM-EQA不是主动取景。 实际执行使用global navmesh prior的Habitat pathfinder；替换普通规划器未在本次配置验证。"
      }
    ],
    "ham-vln": [
      {
        "challenge_id": "C04",
        "insight_id": "I04-3",
        "method_id": "ham-vln:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "ham-vln:e2",
          "ham-vln:e5",
          "ham-vln:rationale"
        ],
        "boundary": "去反思记忆时仍保留回退，不能把改进全归为新增回退动作。"
      },
      {
        "challenge_id": "C05",
        "insight_id": "I05-3",
        "method_id": "ham-vln:method",
        "relation_to_challenge": "direct",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "ham-vln:e1",
          "ham-vln:e4",
          "ham-vln:rationale"
        ],
        "boundary": "episode内工作窗K=1；token下降不等同总时延或费用下降。"
      },
      {
        "challenge_id": "C12",
        "insight_id": "I12-3",
        "method_id": "ham-vln:protocol",
        "relation_to_challenge": "protocol",
        "mapping_status": "supported_by_recorded_source_claim",
        "evidence_refs": [
          "ham-vln:e5"
        ],
        "boundary": "100条子集；不能推断所有反思机制或全量benchmark都同效。"
      }
    ]
  },
  "normalization_notes": [
    {
      "paper_id": "navharness",
      "issue": "same_short_name_distinct_work",
      "resolution": "保留2609.34276 Lifelong与2609.39915 Adaptive Goals两个canonical，不因NavHarness同名合并。"
    },
    {
      "paper_id": "li2024memonav",
      "issue": "task_label_correction",
      "resolution": "旧ObjectNav泛标签改为多目标ImageNav；相关记忆机制只作为相邻任务证据。"
    },
    {
      "paper_id": "safevantage",
      "issue": "task_boundary",
      "resolution": "category-presence离散视点判断；不挂入ObjectNav到达成功比较。"
    },
    {
      "paper_id": "navmcp",
      "issue": "benchmark_boundary",
      "resolution": "HM-EQA/MT-HM3D/EXPRESS-Bench；引用OpenEQA不等于采用其评测。"
    },
    {
      "paper_id": "3d-mem",
      "issue": "passive_active_split",
      "resolution": "EM-EQA给定轨迹的记忆问答与A-EQA主动探索拆开；不把被动结果作为探索证据。"
    },
    {
      "paper_id": "hypothesis-graph-refinement",
      "issue": "passive_active_split",
      "resolution": "A-EQA/EM-EQA/GOAT映射按任务解释，子集不可扩全量。"
    },
    {
      "paper_id": "profocus",
      "issue": "action_and_output_boundary",
      "resolution": "裁剪当前全景与移动取景不同；REVERIE此处不评object grounding。"
    },
    {
      "paper_id": "holoagent-0",
      "issue": "evaluation_scope",
      "resolution": "HM3D-ObjNav定量与全技能定性分开；本次不将其标为lifelong benchmark。"
    },
    {
      "paper_id": "vlmnav",
      "issue": "memory_horizon_not_established",
      "resolution": "旧continual任务标签不采纳；现已读证据不能证明跨任务记忆。"
    },
    {
      "paper_id": "ham-vln",
      "issue": "memory_horizon_and_verifier",
      "resolution": "episode内记忆；未核到subset-to-full附录及独立stop验证器，不补推。"
    }
  ],
  "legacy_insight_audit": [
    {
      "paper_id": "krantz2023ivln",
      "legacy_insight": "把“记忆保留周期”和“oracle观察来源”拆成独立开关；用同一已训练模型切换记忆，比跨模型总分更能定位记忆贡献",
      "classification": "editorial_evaluation_advice_not_author_solution_insight",
      "replacement": "作者方法或评测机制已在candidate中按来源单列；建议只出现在challenge诊断及guardrail。"
    },
    {
      "paper_id": "goat",
      "legacy_insight": "把“记住了目标位置”与“探索后匹配策略变了”拆开测；同时记录感知、检索、规划、执行四级失败，避免把总SR归因给单一记忆模块",
      "classification": "editorial_evaluation_advice_not_author_solution_insight",
      "replacement": "作者方法或评测机制已在candidate中按来源单列；建议只出现在challenge诊断及guardrail。"
    },
    {
      "paper_id": "goat-bench",
      "legacy_insight": "至少联合报告SR/SPL、目标模态、子任务序号和是否先前见过目标；单个总分会把识别能力与路线复用混在一起",
      "classification": "editorial_evaluation_advice_not_author_solution_insight",
      "replacement": "作者方法或评测机制已在candidate中按来源单列；建议只出现在challenge诊断及guardrail。"
    },
    {
      "paper_id": "krantz2020vlnce",
      "legacy_insight": "比较两个planner前先固定它们究竟得到哪种拓扑、定位与低层控制帮助；否则harness差异本身就可能解释成绩",
      "classification": "editorial_evaluation_advice_not_author_solution_insight",
      "replacement": "作者方法或评测机制已在candidate中按来源单列；建议只出现在challenge诊断及guardrail。"
    },
    {
      "paper_id": "batra2020objectnav",
      "legacy_insight": "让harness显式记录STOP、目标ID/类别、几何距离、可见性判定与动作成本；用失败原因与部分进展补足二元成功",
      "classification": "editorial_evaluation_advice_not_author_solution_insight",
      "replacement": "作者方法或评测机制已在candidate中按来源单列；建议只出现在challenge诊断及guardrail。"
    }
  ],
  "primary_abstract_rechecks": [
    {
      "paper_id": "voronav",
      "source_url": "https://arxiv.org/html/2401.02695v2",
      "read_locations": "完整Abstract（本轮公开抽取只返回摘要）",
      "claim_summary": "作者用Reduced Voronoi Graph组织探索路径与规划节点，并组合路径与远视描述为LLM提供环境上下文；本轮未新核完整正文。",
      "scope": "本次仅刷新完整摘要，不能称正文补核"
    },
    {
      "paper_id": "arxiv:2609.39915",
      "source_url": "https://arxiv.org/html/2609.39915v1",
      "read_locations": "完整Abstract（本轮公开抽取只返回摘要，正文依据原记录）",
      "claim_summary": "作者指出局部动作看似合理不保证长程路线一致；按目标专属问题核查观察结果，验证完成为历史压缩提供边界。",
      "scope": "本次仅刷新完整摘要，不能称正文补核"
    }
  ],
  "primary_rechecks": [
    {
      "paper_id": "krantz2023ivln",
      "source_url": "https://arxiv.org/html/2210.03087v3",
      "read_locations": "§3; §4.2.1–4.2.2",
      "claim_summary": "IVLN允许tour内跨指令保留经验；MAP-CMA把深度与语义投影为占据/语义栅格，编码自中心局部裁剪用于动作预测；隐状态持久化作为不同对照。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "goat",
      "source_url": "https://arxiv.org/html/2311.06430v1",
      "read_locations": "§2.1–2.2 GOAT Agent / Instance Matching Strategy; §4.1",
      "claim_summary": "按实例保存位置和多视角图像；新目标先检索实例记忆，命中用记忆位置导航，否则探索；语言目标用CLIP、图像目标用SuperGlue匹配。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "goat-bench",
      "source_url": "https://arxiv.org/html/2404.06609v1",
      "read_locations": "§3 Task; §5.1–5.2 Baselines; §7.1–7.2",
      "claim_summary": "同一场景连续给5–10个多模态子目标；比较显式实例地图与GRU持久状态；按模态分项，并用每子任务清空地图/隐状态检验利用以往经验的效果。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "batra2020objectnav",
      "source_url": "https://arxiv.org/html/2006.13171v2",
      "read_locations": "§2 ObjectNav Task Definition; §2.1 Object Finding and Evaluation",
      "claim_summary": "规定类别目标任务，并将成功分成STOP意图、位置合法、目标表面距离和可见性；允许单列oracle-visibility变体，要求明确本体与场景条件。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "lfg",
      "source_url": "https://proceedings.mlr.press/v229/shah23c/shah23c.pdf",
      "read_locations": "§1 Introduction; §2 Related Work; §3 Problem Formulation（本轮公开正式PDF定向复核）",
      "claim_summary": "作者指出语言叙事不掌握当前真实空间，可能错误；因此用其启发专用规划器而非依赖完整好计划，规划器可在预测不适用时覆盖语言建议。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "esc",
      "source_url": "https://proceedings.mlr.press/v202/zhou23r/zhou23r.pdf",
      "read_locations": "§1 Introduction; §2 Problem Definition（本轮公开正式PDF定向复核）",
      "claim_summary": "作者把常识到动作的缺口及物体—房间关系非确定性作为关键困难，用连续值软逻辑谓词约束frontier选择。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "imaginenav",
      "source_url": "https://proceedings.iclr.cc/paper_files/paper/2025/file/eb261df4322a8bd0a73093c4d8a0d02d-Paper-Conference.pdf",
      "read_locations": "Abstract; §1 Introduction（本轮公开正式PDF定向复核）",
      "claim_summary": "作者认为文字化语义地图难充分表达几何和物体细节，VLM也不宜直接产出连续3D航点；把规划转为候选想象视图选择，再由PointNav到达相应位姿。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "trihelper",
      "source_url": "https://arxiv.org/html/2403.15223v1",
      "read_locations": "§I Introduction（本次公开正文定向复核）",
      "claim_summary": "作者按碰撞、低效探索与目标误识别分解零样本导航失败，指出单一整体策略忽略这些具体失败，因而设计按情况触发的专门辅助。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "hypothesis-graph-refinement",
      "source_url": "https://arxiv.org/html/2604.04108v1",
      "read_locations": "Abstract; §1 Introduction（本次公开正文定向复核）",
      "claim_summary": "作者认为错误预测会沿依赖链累积，单纯置信衰减保留错误子图；需要可修订假设与依赖撤回，同时利用预测进行定向探索。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "ham-vln",
      "source_url": "https://arxiv.org/html/2607.29600v1",
      "read_locations": "§1 Introduction（本次公开正文定向复核）",
      "claim_summary": "作者把瓶颈定位为后续决策需要地点、进度与失败经验，但不能无限增加上下文；动作决策同次写入，再按当前子目标检索旧经验。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "3d-mem",
      "source_url": "https://arxiv.org/html/2411.17735v5",
      "read_locations": "§1 Introduction（本次公开正文定向复核）",
      "claim_summary": "作者认为对象图的有限文字关系会丢失细致空间关系，密集3D表示又难扩展且不利于现成VLM读取；快照保留共可见对象、空间关系和背景，并以frontier快照表示未知。",
      "scope": "只补核指定方法/协议段，非全文"
    },
    {
      "paper_id": "3d-mem",
      "source_url": "https://arxiv.org/html/2411.17735v5",
      "read_locations": "Appendix §11（本次公开正文定向复核）",
      "claim_summary": "实际采用Habitat-sim pathfinder，使用global navmesh prior计算最短路径；可换普通基于可导航图规划器只是作者提出的替代可能，非已评测配置。",
      "scope": "只补核指定方法/协议段，非全文"
    }
  ],
  "exclusions": [
    "不以旧四大group或五个route替代领域challenge；不建立一篇一个challenge的一对一树。",
    "不读取私人ReNav材料；来源仅给定39条公开论文记录及公开原文定向补核。",
    "不将pipeline/representation当作同一层challenge；它们是方法结构说明。",
    "不以benchmark文章旧editorial建议冒充其作者方法insight。",
    "不把全文抓取成功等同完成全文阅读；不升级阅读阶段。",
    "不对未收录文献断言没有其他insight；此候选仅覆盖当前39篇。"
  ],
  "validation_policy": {
    "candidate_only": true,
    "repo_modified": false,
    "published": false,
    "citations_fabricated": false,
    "cross_protocol_ranking": false
  },
  "next_checks": [
    "对标candidate_requires_finer_locator的变体及无作者rationale锚点的解释逐条补到精确段落，而不是用摘要代替。",
    "由用户确认challenge粒度和边界后，才迁移公开树；未授权发布。",
    "方法树支持同一canonical论文多父复用，且始终显示任务条件与来源版本。"
  ]
};
