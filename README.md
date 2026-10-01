# RoboPaperAtlas

机器人研究的 Library、Atlas 与 Radar：按研究问题探索论文，分别查看方法、资源和阅读档案。

## 当前边界

- 95 条论文目录：73 条原始书目与 22 条主来源核验增补
- 原始记录按提供信息保留，核验结果独立保存在 verified_overlay；原始 citation_verified 始终为 false，不把部分字段核验称作整条书目已核验
- 元数据核验、阅读完成和独立复现是不同状态。UMI-on-Legs 与 Deep Whole-Body Control 各有3个阅读阶段，RoboDuet 有1个已审阅初读；其余92条尚未导入阅读报告
- 正式出版方 PDF 优先；预印本替代版本、原因与代码可用性分别说明。只链接第三方 PDF，不重新分发
- 前沿动态是独立的 arXiv 启发式发现队列，不代表人工推荐、同行评审或精读完成。已安排每日更新（约 08:00 UTC），首次计划为 2026-10-01；页面展示最后发布快照，实际抓取状态以页面记录为准

## 本地构建

Python 3.10+ 与 Node24；仅公式预渲染使用锁定版本的 KaTeX：

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run prepare:math
python3 scripts/assemble_frontier.py
python3 scripts/reports.py
python3 -m unittest discover -s tests -v
node tests/test_hero_atlas.cjs
node tests/test_brief_reader.cjs
python3 scripts/build.py
python3 scripts/validate.py
python3 -m http.server 8000 --directory dist
```

输出为 dist/。所有目录与详情页以相对 URL 连接，适用于 GitHub Pages 的 /RoboPaperAtlas/ 子路径。404 页回到该固定站点根。全局搜索使用浏览器加载静态书目索引，支持 /、Ctrl/⌘K、方向键与 Escape；默认编辑式列表，卡片/列表视图与筛选保存在当前 URL。论文速览保留目录上下文，完整详情保持独立地址。移动端菜单、详情页目录和复制链接均为实际交互。首页标题使用分组配色与局部字形反馈，右侧原创星系式知识星图为抽象视觉，不代表论文引用关系；四个主题入口支持局部星域放大与真实论文示例，点击仍跳转到真实目录筛选；悬停和键盘选择等效，↓进入论文、↑返回方向、Esc恢复总览。桌面动画可暂停，离屏/隐藏时暂停；手机与减少动态效果模式使用静态状态。目录、摘要速览与候选页共享交互和视觉规范；独立设计预览仍保留。CSS/JS 使用内容哈希版本 URL，避免混用缓存资源。浏览器搜索在本地运行；不需要账户、模型 API、数据库或外部字体。

## 目录

- data/catalog.json：经过公开字段投影的目录源数据
- data/frontier-parts/：公开候选快照的无损 UTF-8 小片段，每片不超过 60 KB；manifest 保留原始字节数与 SHA-256
- data/frontier.json：构建时精确重组的真实 arXiv 候选快照，不直接提交
- data/reports.json 与 data/report-parts/：审核通过报告的元数据和无损UTF-8片段；生成 artifacts/ 时逐一核对大小、SHA与HTML安全
- scripts/reports.py：重建三个版本固定的阅读HTML；只按清单发布，不复制邻近研究资料
- scripts/assemble_frontier.py：验证片段顺序、字节数与 SHA-256，再原子重组；--split 将采集器的新快照重新导出为片段
- scripts/build.py、frontier_page.py：确定性静态生成器
- scripts/validate.py：公开字段、URL、ID、年份、阶段状态和本地链接检查
- assets/：无第三方运行时依赖的页面样式和交互
- docs/schema.md：公开数据契约与将来的报告导入约定
- data/briefs/：按日期保存的摘要速览与索引，证据与作者陈述/编辑推断分开
- docs/daily-briefs.md：每日简报更新契约；摘要自动化状态由实际配置验证后记录
- CONTRIBUTING.md：来源与版权检查

## GitHub Pages

在仓库 Settings → Pages 将 Source 设为 GitHub Actions 后，pages.yml 仅发布 main 上经测试的 dist/。PR 工作流仅执行读取权限的测试，不部署；不使用 pull_request_target、仓库写凭据或跨仓库凭据。手动部署同样限制 main。

这里提供部署配置，不声称任何仓库设置、环境保护或分支保护已经启用。维护者应为 main 配置审查与必要检查，尤其审查 workflow、脚本和公开数据变更。

## 内容与许可

本库不授予第三方论文、数据、图表或代码的任何新许可。公开访问不等于转载许可。贡献原创报告时必须说明有权公开；引用应适量并链接来源。详见 [贡献指南](CONTRIBUTING.md)。

## 单页阅读器预览

`reader-preview/umi-on-legs/` 提供一页完整的Stage3阅读器设计预览，复用站点导航与基础样式，并用已审核原文生成代码语法颜色、原文件行号和可操作目录。此预览不替换三份已发布v1报告。详见 `docs/reader-preview.md`。

## 分类与浏览

Library、首页与 Atlas 共用已核查来源的研究问题分类。方法标签和资源类型单独筛选；四条分类边界记录保持待复核。详见 [classification](docs/classification.md)。原始书目与阅读状态不因分类检查而改变。

The reader preview typesets reviewed equations with pinned build-time KaTeX and serves local fonts. See [math rendering](docs/math-rendering.md). Node24 is required for the pinned build toolchain.

Current UMI-on-Legs reports use the accepted shared reader in v3: Stage 1 expanded figure/table analysis, Stage 2 official-source locations, and Stage 3 colored code plus offline LaTeX math. Immutable v1/v2 links remain available. UMI-on-Legs and Deep Whole-Body Control each have three imported reading stages; RoboDuet has one content-reviewed first reading. See [report artifacts](docs/report-artifacts.md) for exact version/security rules.

Radar now leads with a source-backed research overview and all records in its observation window; individual selected summaries are secondary. Schema1.1 keeps1.0 compatibility, and the original2026-09-30 five-summary snapshot remains in the history route. The separate daily task must be updated and verified after deployment; this repository adds no scheduled workflow.
