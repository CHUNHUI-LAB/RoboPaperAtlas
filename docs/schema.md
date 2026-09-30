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
- stages：stage1、stage2、stage3，各为 status:not_imported 与 artifacts:[]

每个 URL 必须使用 HTTPS，禁止用户信息、凭据形查询参数、私有域名、控制字符或非公网 IP。题名与文本输出时进行 HTML 转义；ID 和路径在生成前严格校验。

## 报告导入约定（未实现、未启用）

未来报告导入应作为单独审查的功能变更。建议每个实际产物包含 kind、version、path、sha256、source_edition、created_at、rights_note 和 review_status；使用 artifacts/{paper-id}/{stage}/{version}/ 的不可变路径。先验证文件存在、校验值、来源版本、公开权利与 HTML 安全，再把阶段状态改为已导入。当前生成器拒绝非空 artifacts，避免在尚未支持时声称有报告。

## Frontier v1

候选数据独立于正式目录。schema_version、抓取时间、最近成功/失败、status、coverage 与 collection 解释快照来源。papers 按规范 arXiv ID 去重，保留 arxiv_version、first_submitted_at、updated_at、change_type、observation、matched_topics、relevance_reasons、source_url、version_url 与 candidate_not_reviewed 状态。

摘要仅发布短摘录，并标记截断；匹配发生在公开标题与摘要中，不是模型评估或质量排名。自动计划未启用时界面必须明确说明。
