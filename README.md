# RoboPaperAtlas

中文机器人论文目录与阅读档案，面向具身导航、全身控制与移动操作、视觉语言动作，以及基础方法、数据和评测。

## 当前边界

- 95 条论文目录：73 条原始书目与 22 条主来源核验增补
- 原始记录按提供信息保留，核验结果独立保存在 verified_overlay；原始 citation_verified 始终为 false，不把部分字段核验称作整条书目已核验
- 元数据核验、阅读完成和独立复现是不同状态。三个阅读阶段当前均为 not_imported，没有虚构报告
- 正式出版方 PDF 优先；预印本替代版本、原因与代码可用性分别说明。只链接第三方 PDF，不重新分发
- 前沿动态是独立的 arXiv 启发式发现队列，不代表人工推荐、同行评审或精读完成。当前没有自动刷新计划

## 本地构建

Python 3.10+，无第三方构建依赖：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/validate.py
python3 -m http.server 8000 --directory dist
```

输出为 dist/。所有目录与详情页以相对 URL 连接，适用于 GitHub Pages 的 /RoboPaperAtlas/ 子路径。404 页回到该固定站点根。浏览器搜索在本地运行；不需要账户、模型 API、数据库或外部字体。

## 目录

- data/catalog.json：经过公开字段投影的目录源数据
- data/frontier.json：真实抓取的 arXiv 候选快照与抓取状态
- scripts/build.py、frontier_page.py：确定性静态生成器
- scripts/validate.py：公开字段、URL、ID、年份、阶段状态和本地链接检查
- assets/：无第三方运行时依赖的页面样式和交互
- docs/schema.md：公开数据契约与将来的报告导入约定
- CONTRIBUTING.md：来源与版权检查

## GitHub Pages

在仓库 Settings → Pages 将 Source 设为 GitHub Actions 后，pages.yml 仅发布 main 上经测试的 dist/。PR 工作流仅执行读取权限的测试，不部署；不使用 pull_request_target、仓库写凭据或跨仓库凭据。手动部署同样限制 main。

这里提供部署配置，不声称任何仓库设置、环境保护或分支保护已经启用。维护者应为 main 配置审查与必要检查，尤其审查 workflow、脚本和公开数据变更。

## 内容与许可

本库不授予第三方论文、数据、图表或代码的任何新许可。公开访问不等于转载许可。贡献原创报告时必须说明有权公开；引用应适量并链接来源。详见 [贡献指南](CONTRIBUTING.md)。
