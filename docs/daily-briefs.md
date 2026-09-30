# Daily abstract brief contract

The research brief is a separate editorial layer over the candidate feed. It does not mark any paper as read or reproduced, and is not a literature-wide trend report.

## Bounded source paths

- data/briefs/YYYY-MM-DD.json: one dated public brief; use an ISO UTC date
- data/briefs/index.json: schema_version=1, latest date, summary_automation_enabled boolean, and briefs entries with date/path/title/status/sha256
- A dated path must equal its entry date plus .json; directory traversal and symlinks are rejected
- Preserve earlier dated files. Update the corresponding SHA-256 whenever a brief changes
- The renderer creates frontier/briefs/YYYY-MM-DD/index.html; the frontier home displays the latest indexed brief

## Brief schema 1.0

scripts/briefs.py defines the exact public field allowlist. Required top-level fields include id/date/title/status/generated_at/language, an explicit UTC updated_at window, source_snapshot provenance and SHA-256, counts, overview, new_papers, revised_papers, reading_priority, evidence_note, limitations and candidate_ids.

Select at most five papers. Fewer or zero is valid; do not fill a brief with unsupported recommendations. Keep first submissions separate from revised versions. A revision is not a verified new contribution unless a version comparison was actually performed.

Every selection includes canonical arXiv ID and a pinned version URL, problem, author_proposal, relevance, evidence_limit and evidence scope. author_proposal_attribution must be author_claim; relevance_attribution must be curator_inference. Abstract-only notes require the complete abstract, full_paper_read=false and experiments_independently_verified=false. Full-text or version-comparison scopes require actual supporting work and accurate evidence metadata.

Use short Chinese paraphrases, not copied full abstracts. Distinguish author-reported results from independent verification. Never insert private project details, personal context or account information into this public file.

## Update order

1. Assemble the prior candidate snapshot, collect the authorized window, and export its small public parts as documented in frontier-collector.md
2. Inspect primary-source complete abstracts or explicitly documented stronger evidence; inspect previous briefs to avoid repeating unchanged material
3. Prepare the dated brief and index. Record counts for its own time window, separately from the seven-day feed
4. Run unit tests, build, and static validation before review/publication
5. Only set summary_automation_enabled=true after the summary-updating schedule has actually been configured and verified

Scheduled arXiv collection and scheduled editorial summarization are distinct. The flag describes summarization setup, not proof that a scheduled run has occurred. On source failure preserve the last successful brief and accurately label stale/error state; never invent a fresh digest.

## Validation and failure states

Counts are nonnegative JSON integers (not strings or booleans), and the candidate/version list, selected groups, window duration and coverage must agree. New submissions use v1; revisions use v2 or later. Evidence URLs must identify the selected version. All nested structures use explicit key allowlists. The publisher rejects unindexed archive files and symlinks, then copies only the validated index and its dated files.

- ready: zero to five supported selections, with accurate evidence
- no_material_update: zero selections and no reading-priority recommendations; state why no new summary is warranted
- stale: retain the original successful observation window and source provenance; the UI explicitly identifies preserved older content
- error: zero selections; state the blocker and preserve older dated files

For full_text_checked, the full_paper_read flag must be true and supporting sources plus checked sections are required. A version_comparison needs explicit compared-version sources. Merely changing the evidence label cannot promote an abstract-only note into a full-paper or comparison claim.
