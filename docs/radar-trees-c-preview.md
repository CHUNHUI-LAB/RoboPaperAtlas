# Radar C 双树隔离预览

入口为 `review/radar-trees-c/index.html`。它是待浏览器验收的导航领域研究双树候选，仅有独立链接；没有替换 Radar、Atlas、Library 或阅读档案入口。

## 正常构建

`python3 scripts/build.py` 与现有 CI 的 `python3 scripts/build_previews.py` 均在清理 dist 后生成该路线。源位于 `previews/radar-trees-c/`，包含精确9文件；`scripts/radar_tree_preview_manifest.json` 逐文件固定 SHA-256。多余、缺失、被改动文件或 symlink 会使构建失败，不会直接发布相邻文件。

常规构建复制已审核公开快照，不进行新文献推断。内容更新先在独立 research-tree / radar-tree-overlay 管线中验证来源范围、节点身份与候选关系，再审查9文件及 manifest 的变化。不得仅改 manifest 绕过审核。正常日报自动化不更新此冻结快照。

## 固定范围

基础来源 main e141b9de1e9cdce5cf371b2aa4ac969fc3aa9956。日报2026-10-05为0候选、0映射；周报2026-10-04窗口238候选、11官方完整摘要，其中6篇本轮重新核查形成20位置候选，5篇未映射。新增学术边0；本轮全文、代码、复现、版本差分均0。基础树核心10篇指定正文范围另列，不因本期映射提升阅读状态。

数据继续显示原日期与来源范围，后续日报发布不会把该快照称为当天发现。候选缺分支不代表研究空白；同一论文跨树连线只是编辑组织关系。

## 验收与发布范围

本地静态与DOM检查不能代替浏览器验收。先发布获准的隔离HTTPS预览，然后用1774×887真实截图对照用户选择的C，检查390×844窄屏、缩放、选中路径、搜索、展开、键盘与文字替代。通过后另行决定是否增加正式 Radar 导航入口；当前改动没有这样的入口。

ResearchVoyager链接仅指向公共方法站预览。此源目录不包含私有项目overlay、私有skill或研究工作区文件。
