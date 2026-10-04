# Weekly Radar contract (weekly-1.0)

Weekly is an independent editorial product, not seven daily briefs concatenated. It preserves a seven-day inclusive UTC updated_at observation window and groups shared research questions, method differences, and evidence gaps. Daily 1.0/1.1 fields and validation remain unchanged.

## Bounded archive and reproducibility

`data/weekly/index.json` uses `weekly-index-1.0`, latest end date, verified automation boolean and entries containing date/path/title/status/SHA-256 plus candidate manifest SHA-256. Each date maps to `YYYY-MM-DD.json` and `YYYY-MM-DD/manifest.json`. Preserve old dates and windows. The renderer creates `frontier/weekly/index.html` and `frontier/weekly/YYYY-MM-DD/index.html`; the Radar home links explicitly to daily and weekly.

Weekly payloads whitelist window, source snapshot provenance, counts and abstract-evidence research overview. No raw abstracts, private research, user plans, catalog/Stage changes or unpublished research details belong here. Candidates retain only ID/version, title, first submission/update, new/revision and existing keyword topics. Candidate records are frozen in ordered JSON blobs <=60,000 bytes. Each blob has byte count, row count and SHA-256. A canonical UTF-8 JSON array digest (`ensure_ascii=False,separators=(',',':')`) fixes the assembled list; the index pins the manifest. Unindexed files, traversal, symlinks, unknown fields, unsupported URLs/versions, count mismatches and incorrect evidence unions fail closed.

This duplicates bounded candidate metadata to preserve old observation windows after frontier.json rolls forward. Two initial blobs avoid large connector writes; weekly editorial JSON remains a single small file. The source_snapshot SHA records exact frontier bytes used at preparation. It is a provenance claim, while frozen candidate list integrity is independently checked on every build. Before freezing a new issue compare each retained row against the matching source snapshot; do not silently reconstruct historical lists from newer feeds.

Complete-abstract source fingerprints use whitespace-collapsed retrieved official abstract text, Unicode character count and SHA-256 of UTF-8. Do not hash a paraphrase or 600-character excerpt. Raw retrieval text is kept outside the repository and is not copied by the build. Page typography may differ from API characters. Every source has a pinned version URL and actual checked_at. All weekly-1.0 evidence is complete-abstract-only: no full text, experiments, code or version diff is implied. Revisions are counted independently from verified contribution changes. Topic distributions remain the existing multi-label keyword heuristic, not popularity or curated classification.

## State semantics

- ready: supported nonempty themes; partial source coverage must remain explicit
- no_material_update: no themes; zero or nonzero candidate metadata can remain, never fabricate themes to fill space
- error: no themes; failure is not zero new papers; preserve earlier dated successful issues
- stale: preserve the original observation window, candidate manifest and provenance with the earlier content; only the publication/update timestamp may advance

A complete source cannot also be truncated. Failed/stale source status cannot create a fresh ready issue. Coverage must encompass the full displayed seven-day window. Source failure alone never rewrites a previous week as an empty fresh success.

## Preparation and checks

Read official sources and create an issue separately from daily production. Verify counts, new/revision, source digest, all evidence text fingerprints, pinned URLs, public field allowlists and absence of private context. Run `python3 -m unittest discover -s tests -v`, the repository Node suite, `python3 scripts/build_previews.py` and `python3 scripts/validate.py`. The weekly archive is loaded and validated by the build; CI's full build enforces it. Browser QA is distinct from static tests.

`summary_automation_enabled` stays false until a separately configured weekly schedule is verified. This module changes no collector query, daily automation prompt or schedule.

## Scheduled editorial update scope

For a routine weekly run, the only source writes are `data/weekly/index.json`, one `data/weekly/YYYY-MM-DD.json`, and its `data/weekly/YYYY-MM-DD/{manifest.json,000.json,...}` bounded candidate parts. Do not modify catalog, Stage/report data, classification, daily briefs, collector code/query, workflows or daily automation. Do not copy private source ledgers or raw abstracts. Do not enable the automation boolean until the actual weekly task has been verified. Module/schema changes require a separate reviewed implementation change.

1. Read the latest successful candidate snapshot and collection status; compute its exact byte SHA, preserve its query/rule version and observed window. A weekly observation window must be exactly 168 hours. Do not relabel stale source content with today's window.
2. Check official complete abstracts, pin the exact versions, and identify shared problems, meaningful method differences and remaining evidence gaps. Keep author claims distinct from editorial synthesis. New/revision derives from the pinned version; version change alone is no evidence of a changed contribution.
3. Project only the candidate allowlist, verify it equals the source snapshot's matching window, freeze its parts and checksums, then compose the public weekly JSON and matching index entry. Preserve every earlier dated issue. The validator compares candidate coverage, counts, version URLs, theme-to-source coverage and all archive hashes.
4. Validate the independent archive (`PYTHONPATH=scripts python3 -c "from weekly_briefs import load_archive; load_archive('.')"`), then run the README and CI commands: `npm run prepare:math`, `python3 scripts/assemble_frontier.py`, `python3 scripts/reports.py`, `python3 -m unittest discover -s tests -v`, the workflow's Node tests, `python3 scripts/build_previews.py`, `python3 scripts/validate.py`. Use the pinned existing dependency installation; do not work around installation or environment restrictions.
5. Publish only after review using the current main baseline and verified public-file allowlist. Confirm exact commit CI and deployed routes. Scheduled run output should distinguish unpublished candidate, merged data and live verified deployment.

On failed collection, incomplete abstract retrieval or failed validation, leave the latest successful issue and index bytes unchanged and report the blocker. A partial query may support a clearly labelled partial issue if its evidence and actual window are sound; it must never claim complete coverage. If a separately reviewed stale/error publication is needed, keep old provenance/window and distinguish the failed attempt from the successful archive. An empty recent day does not mean an empty week. No-material requires a genuine weekly editorial judgment and no fabricated or repeated themes.

### Failed attempts without rewriting history

The optional index-only `last_attempt` allowlist is status=`error`, attempted_at, window_start, window_end and a short public-safe message. `record_failed_attempt` validates a seven-day attempted window, adds this note to the index, and leaves every successful dated issue/manifest/part unchanged. The renderer shows the failure separately above the last successful week's original window. Tests compare all archived file hashes before and after failure. A later successful update should remove the resolved note. `ready` and `no_material_update` require a successful (`ok` or explicitly partial `limited`) source; failed or stale source data cannot masquerade as no new material. Source generated/fetched timestamps and abstract checked timestamps cannot exceed report generation.

### Radar landing page and daily entry

The Radar home leads with the latest usable ready/stale weekly synthesis and its original date/window; today's daily state is a compact notice with a direct dated-daily link. `frontier/daily/index.html` remains the explicit latest daily entry, including no-material days. Do not copy weekly themes into the daily JSON or label weekly/historical work as today's discoveries. If a later weekly attempt fails or has no material themes, retain the latest usable old weekly window with a clear preservation notice. If there is no usable weekly content yet, show an explicitly dated historical ready daily; if neither exists, state the gap and retain the observed candidate queue. Failed/stale daily states say failure/preservation rather than claiming zero papers.
