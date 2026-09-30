# RoboPaperAtlas arXiv candidate collector

A Python 3.10+ standard-library collector for a public, metadata-only discovery feed. It makes no LLM calls, uses no API key, downloads no PDFs, and installs nothing. It does not schedule, commit, or deploy anything.

## Run and test

```sh
python3 scripts/assemble_frontier.py
python3 -m unittest discover -s tests -v
python3 scripts/collect_arxiv.py --output data/frontier.json --days 7 --max-papers 300
python3 scripts/assemble_frontier.py --split
```

For a reproducible window use `--as-of 2026-09-30T06:18:30Z`. Defaults scan the preceding seven days in UTC, inclusive at both ends. Date windows are limited to 31 days. Successful results are reused for 23 hours when the same configuration is requested; `--cache-hours 0` explicitly refreshes. Synthetic test data stay under `tests/fixtures/` and must never be displayed as actual papers.

The collector exits 0 for `ok`, `limited`, or a cached successful result; 1 for fetch error/stale retained results; 2 for invalid arguments or an incompatible/unreadable previous file. A limited feed is a valid bounded result, not a promise of complete coverage.

## First-party sources and acquisition

- API manual: https://info.arxiv.org/help/api/user-manual.html
- API terms/rate limits: https://info.arxiv.org/help/api/tou.html
- RSS/Atom alternatives: https://info.arxiv.org/help/rss.html
- Endpoint: https://export.arxiv.org/api/query

The official API returns Atom with OpenSearch paging metadata. Only `submittedDate` is documented as a range filter. Restricting that field would miss recently revised older papers. Instead this collector sorts `lastUpdatedDate` descending and pages until the first entry older than the UTC window, all query results are exhausted, or the configured page bound is reached. It does not send an undocumented update-date range filter.

The client uses one connection at a time and at least 3.1 seconds between request starts, including retries. Default bounds: 100 entries/page, 12 pages, 3 attempts/request, 35-second timeout. Retries cover connection/timeout failures and HTTP 429/500/502/503/504. Backoff honors a bounded Retry-After; a request to wait more than 120 seconds stops the run instead of retrying early. HTTP 4xx other than 429 is not retried. Production calls for the same query should be no more than daily; the rate limit applies across all machines controlled by the project. Use one updater, not concurrent collectors.

A failure never replaces a prior successful paper list or its original fetched/success timestamps. It emits `stale`, records the failed attempt separately, and atomically replaces the JSON status wrapper. With no previous success, it emits `error` and an empty list; that is explicitly different from a successful empty search. A malformed existing JSON file is not overwritten. Ordering, repeated pages, unexpected short pages, and changing API totals are treated as inconsistent snapshots, not successful coverage.

## Selection is deliberately heuristic

Retrieval is limited to `cs.RO`, `cs.CV`, `cs.AI`, `cs.LG`, and `cs.CL` plus the explicit query in `collection.search_query`. Local selection uses only normalized title and abstract text. No citation, quality, acceptance, full-paper reading, or model judgment is implied.

Topics: VLN/ObjectNav; navigation agents/harnesses; spatial/episodic memory and feedback; mobile/quadruped-arm manipulation; whole-body control; end-effector trajectories; robot VLA; robot MoE; robot world models.

Digital-only web/GUI/code/cybersecurity/game-map agent papers are excluded using explicit title phrases unless the title also has a robot term. Generic navigation or embodied-AI wording alone is not enough for a robot world model. World-model matches additionally need a task-specific robot-context phrase, a physical-robot title term, or multiple explicit physical-robot mentions. These are transparent string rules, not semantic understanding.

For VLA/MoE and memory, domain context must occur in the title or first 600 normalized abstract characters. Navigation agents require navigation in that same focus text. World models require both direct robot/navigation context and a world-model term in the focus text. This rejects many generic AI papers with an incidental robotics example, but intentionally favors precision over recall and can miss relevant work. Quadruped locomotion alone does not qualify as mobile manipulation. World-model discovery includes the synonymous world-action-model phrase. Remaining false positives are still possible.

Every match exposes the matched phrase and whether it came from the title or abstract. `matched_topics` contains stable IDs, with labels in `topic_labels`. `review_status` remains `candidate_not_reviewed`; `deep_read` is false. A candidate must go through separate deliberate review to enter the curated catalog. The curated reading path should prefer an available formally published version. DOI and journal-reference strings are merely author-supplied arXiv metadata, not independently verified publication status.

## JSON contract (schema 1.0)

- `generated_at`: when this JSON status document was generated
- `fetched_at`: time the last page contributing to the current successful feed was fetched; stays unchanged on a later failure
- `last_successful_fetch_at`: successful bounded scan completion, even if limited by page/display bounds
- `last_failed_fetch_at`, `fetch_error`: null after a successful run; describe the most recent failed attempt otherwise
- `status`: `ok`, `limited`, `stale`, or `error` (`pending` may be used by the UI before any run)
- `coverage.window_start/window_end/date_field`: exact UTC update window and `updated_at`
- `coverage.complete`: the declared query was scanned far enough to cover the requested window; does not mean all relevant literature was found
- `coverage.truncated`: a page or display cap was hit; `complete:true,truncated:true` means the scan covered the query window but not all matches are displayed
- `api_total_results`: API count for the whole query over all time, not the seven-day result count
- `fetched_entries`, `window_entries`, `matched_entries`, `displayed_entries`, `pages_fetched`, `stopped_at`: distinct counts and stopping reason
- `attempted_coverage/attempted_collection`: only on stale failures; old successful `coverage/collection` still describe the retained papers
- Each paper: `canonical_id`/`id`, optional integer `arxiv_version`, `versioned_id`, canonical `source_url`, pinned `version_url`, title, ordered author names, an `abstract_excerpt` of at most 600 source-text characters, `abstract_truncated`, `abstract_original_chars`, first-submitted/update/fetch dates, categories, DOI/journal reference if present, match evidence, and review status
- `change_type:new|revision`: current version is the first submission vs a revision; based on published/updated timestamps and version metadata, not the first appearance in this feed
- `observation:first_seen|version_updated|unchanged`: separate comparison with the previous displayed snapshot; it is not a lifetime event log
- `first_seen_at`: first observed within retained snapshots. A paper dropped due to a display cap or window expiry can later be seen anew

The full abstract is used only while matching and is omitted from published JSON. `abstract_excerpt_method:verbatim_prefix_whitespace_normalized` records that the excerpt is a source-text prefix, not an AI-generated summary. Follow the canonical arXiv link for the full abstract and version history.

All public URLs are canonical arxiv.org URLs. No private data, user source IDs, authentication, or internal notes are included. The site is an independent project, not endorsed by arXiv. arXiv's terms allow sharing descriptive metadata under CC0, including titles, authors, and abstracts; this is not permission to redistribute all paper PDFs.

## 手动更新与发布

在命令行运行采集器只更新本地 JSON，不创建定时计划、提交或部署。检查结果后按仓库的 PR 审查与 main 发布流程处理。未来若加入计划更新，必须独立验证执行与发布结果；不能假定由 GITHUB_TOKEN 产生的 push 会触发另一条工作流。

## Small-file source transport

The committed source uses data/frontier-parts/ raw UTF-8 fragments. Each is at most 60 KB and has an ordered name, byte count and SHA-256; the manifest also records the entire original snapshot hash. Assembly reconstructs the exact original bytes, with no paper removal or metadata normalization. data/frontier.json is generated and ignored by Git. Run assembly before tests/build; after collecting a reviewed new snapshot, run --split and commit the parts plus their manifest. The builder auto-assembles only when the full file is missing. CI always assembles first.
