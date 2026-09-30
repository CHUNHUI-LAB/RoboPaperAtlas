# 公开数据契约

## Catalog v1

data/catalog.json 包含 schema_version、updated_at 与 papers 数组。scripts/validate.py 中 FIELDS 是可发布字段的精确白名单；未列出的字段将令构建失败。

- id：独立稳定的公开标识，只允许小写字母、数字和连字符
- title / authors / bibliographic_year：原始记录或已明确核验的增补书目
- original_metadata：原始题名、作者与年份，不包含来源系统标识
- verified_overlay：独立核验的显示题名、作者、年份等；不覆盖原始记录
- citation_verified：增补条目是否完成声明范围内的书目来源检查；不代表全文阅读
- metadata_status / verification_scope / verified_at：原始状态与核验边界
- publication_year / preprint_year / year_basis：分开保留年制，未知为 null
- category：navigation、wbc、vla 或 foundations；tags 为检索标签
- paper_url / pdf_url / pdf_kind / pdf_edition / pdf_note：出版入口、PDF 版本与选用原因
- project_url / code_urls / code_note：官方项目、代码或数据入口及可用性说明
- sources / notes：公开来源 URL 与版本提醒
- stages：stage1、stage2、stage3。没有实际报告时为 status:not_imported 与 artifacts:[]；已导入状态必须与经过内容检查的 data/reports.json 精确匹配

每个 URL 必须使用 HTTPS，禁止用户信息、凭据形查询参数、私有域名、控制字符或非公网 IP。题名与文本输出时进行 HTML 转义；ID 和路径在生成前严格校验。

## 阅读报告导入 v1

本次仅允许 UMI-on-Legs（rpa-0062）的三个已审核HTML。版本目录为 artifacts/rpa-0062/v1/，三个原始文件名并列，以保留阶段互链。网站公开版仅增加返回书目链接；公开SHA与离线原始SHA分别记录。其他研究材料和论文PDF不进入产物。

源文件按UTF-8边界切成不超过48,000字节的小片段。scripts/reports.py 校验精确字段白名单、固定身份与路径、顺序、大小、SHA、HTML标签/属性、图片数据与链接，再重建生成目录。构建仅复制清单内的三个产物，拒绝符号链接和额外文件。Git不提交生成后的整份HTML。

目录中的每个已导入产物包含 kind、version、path、sha256、source_edition、created_at、review_status，必须与审核清单一致。已导入表示实际报告已公开，不表示独立实验复现、完整代码审计或作者认可。详见 report-artifacts.md。

## Frontier v1

候选数据独立于正式目录。schema_version、抓取时间、最近成功/失败、status、coverage 与 collection 解释快照来源。papers 按规范 arXiv ID 去重，保留 arxiv_version、first_submitted_at、updated_at、change_type、observation、matched_topics、relevance_reasons、source_url、version_url 与 candidate_not_reviewed 状态。

摘要仅发布短摘录，并标记截断；匹配发生在公开标题与摘要中，不是模型评估或质量排名。自动计划未启用时界面必须明确说明。
