# 投稿导航有界核验 · 2026-10-06

基线为 main `0de9c5e943238d79c12ba8a525226707d5082850`；公开数据 blob 为 `c95c68096cd14208acf250d995efc6cd5104173e`。这是未发布候选，核验日不等于政策发布日期。未发现本轮已核实的临近论文截止延期。

## 本轮最小增量：NeurIPS 2026 主会

- [主会 CFP](https://neurips.cc/Conferences/2026/CallForPapers)确认历史作者通知日 2026-09-24 AoE，补入决定节点；原摘要、全文节点完整保留。全文截止已包括补充材料，不另造较晚窗口。
- [Dates](https://neurips.cc/Conferences/2026/Dates)的会址分配通知是 2026-10-06 17:00 UTC，Attendee 早鸟截止为 2026-10-30 AoE。前者不是提交截止，后者不是论文注册或作者强制注册截止，二者只写入说明，不进入论文 deadline 数组。不推测 AoE 日期的时刻。
- [主会手册 V2026.3](https://neurips.cc/Conferences/2026/MainTrackHandbook)说明初稿/终稿正文为 9/10 页，附录、参考文献、checklist 另计；回复是 OpenReview 逐条讨论，并非上传新版稿件。终稿须会前完成，但本轮核读的三页没有具体终稿日。至少一位作者须注册，Virtual Only Pass 不足；论文须在官方会址展示，严重特殊情况可由他人代为展示。
- 只新增两份带本次读取范围的官方来源记录；原来源和旧 NeurIPS 整条快照均保留。模板链接读取失败，未下载、解包或编译，不提升模板状态。

## 实际覆盖与未变边界

以下均为公开网页文本的有界复读，不是全站变更或所有评论的穷尽监控。

- [CoRL 2026 作者指南](https://2026.corl.org/contributions/instruction-for-authors)：10 月 12 日 23:59 AoE 终稿仍在，初稿/终稿正文 8/9 页不变；模板未重新下载。
- [RSS 2027 CFP](https://roboticsconference.org/information/cfp/index.html)：八个日期未变，所有时间保持 23:59 AoE。12 月初是 extended abstract，4 月全文仍依赖前置阶段与邀请；不升级为开放首轮。
- [ICLR 2027 CFP](https://iclr.cc/Conferences/2027/CallForPapers)：9 月首轮已过、11 月 5–18 日作者讨论与 12 月 16 日决定未变；原 AoE 和日期精度不变。
- [CVPR 2027 CFP](https://cvpr.thecvf.com/Conferences/2027/CallForPapers)：六个已有日期未变，范围仍包括 embodied robotics、VLA 与 planning。2027 AuthorGuidelines 实际返回 404；不借用旧届模板，不新增视觉渠道。
- [IROS 2027 首页](https://2027.ieee-iros.org/)读取时跳转至 IROS 2023。没有据此建立 2027 截止。
- [ICRA 2027 终稿页](https://2027.ieee-icra.org/contribute/final-paper-submission-instructions/)仍明确含 2025 与 2025-03-06；[注册页](https://2027.ieee-icra.org/attend/registration-information/)仍称作者注册详细安排待公布。不更改既有冲突/未知边界，PST 不转换为推测的 UTC 时刻。
- [RA-L 首页](https://www.ieee-ras.org/publications/ra-l/)已读展示窗口与资格段，既有 ICRA/IROS 2027 窗口、非综述、270 天和单会议条件不变。
- T-RO 作者页首次读取及官方首页链接重试均失败，已读取[官方首页](https://www.ieee-ras.org/publications/t-ro/)的展示/投稿入口部分；这不足以重新认证全部投稿政策。IJRR、JFR、Autonomous Robots 作者页可读取；本轮仅核读模板/初稿格式段，未重验全套政策、专题或模板文件，不刷新其整条快照。
- [RA-L 可变形物体操作专题](https://www.ieee-ras.org/publications/ra-l/special-issues/current-special-issues/robot-manipulation-of-deformable-objects/)的时间表已读取，11 月 15 日开放、12 月 1 日截止、2027 年 5 月 30 日计划出版与既有记录相同；不添加未知时刻或时区。
- 其他届次、专题与渠道未全面重读，不能据此宣称全部无变化。

## 公开经验：只核读，不扩增

实际读取了 [JFR SciRev](https://scirev.org/reviews/journal-of-field-robotics/)三份可见匿名评价及 [RSS 2026 Reddit 讨论](https://www.reddit.com/r/robotics/comments/1rznoyh/rss_robotics_sciences_and_systems_2026_discussion/)正文和可见部分评论。前者没有可靠投稿年份；后者包含不同账号对评审、回复入口、等待与结果的自述，不能拼接成同一论文时间线。未展开全部更多回复或核验匿名作者身份，没有足够新证据改写经验。

19 条经验、19 份总览、8 条编辑归纳均与基线相同，日期不刷新；个人经历不提升为官方规则或成功概率。阅读状态与发表身份无改动。

## 验证与发布边界

- 投稿 Python 44/44、Node 38/38 通过，包括生成入口数据哈希、筛选、返回、重试及新旧日期边界。
- 新增严格逆向投影：验证新增版 NeurIPS、来源和历史记录的固定指纹，再重建完整 `0de9c5e` 数据指纹。旧 10 月 4 日经验与维护快照测试继续串接原有固定指纹；未删改旧安全断言。
- 历史测试定位 10 月 4 日记录改为按日期定位，避免后续追加误读 `history[-1]`；负例仍检测旧来源篡改，并新增新来源/历史删除、经验/发表身份丢失等反例。
- 完整基线 963 个 blob 已逐个校验，无缺失；本轮 5 个既有文件修改、3 个新增文件，958 个原文件字节不变，无删除。
- 在独立候选中，锁文件约束的离线 npm ci 成功，准备 48 个公式、重建 253 条 frontier 与 21 份报告；build_previews 与 validate 通过（95 条目录、165 个 HTML）。两次构建的 255 个输出文件哈希一致。全量 Python 568/568 通过；31 个正式静态 Node 测试文件运行成功，Node runner 303/303 通过。
- 独立只读复核确认日期/历史边界，并修正严重特殊情况可由他人代为展示的例外。未改 UI、生产脚本或其他业务数据。可选 map_browser_qa 曾尝试启动 Chromium，但在页面加载前被云沙箱 socket 权限阻止；未修改脚本、未绕过限制，不声称浏览器验收通过。远端精确提交 CI 和部署尚未执行。

## 合并后 main 的独立再验证

随后将候选三方整合到 `385c28927865bf73e488ef8b953d9246dc915171`（Git tree `85d7fc2e550c8fba321821c96d0e2bebc81c6102`）。该 main 的 1060 个 blob 全量校验；上游 105 个改动/新增路径与本候选 8 路径无交集，全部保留。投稿源 JSON 本身未被上游改变，原固定历史指纹仍有效。

在新 main 的独立候选重新完成锁定依赖安装、公式准备、frontier/报告重建、构建及 validate：95 条目录、253 条 frontier、21 份报告、172 个 HTML；两次构建的 262 个产物哈希一致。新 main 候选的全量 Python 585/585 通过；32 个正式静态 Node 文件运行成功，Node runner 306/306 通过。这里不借用旧 main 的测试结果。独立复核另验证 25 项定向测试与 10 个篡改反例，确认上游 105 路径、Radar、正式目录及阅读状态完整保留。
