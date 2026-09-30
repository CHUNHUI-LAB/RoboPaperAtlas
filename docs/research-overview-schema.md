# Daily research overview, schema 1.1

The accepted overview is the production Radar view for schema1.1. Existing version1.0 brief files and rendering remain valid. Deployment of this renderer does not itself change the existing scheduled task; its migration is verified separately after the production page check.

## Paths and publication boundaries

- Existing future publication scope: data/briefs/YYYY-MM-DD.json plus data/briefs/index.json, with the index's exact dated-file SHA-256 updated
- Accepted design sample: data/radar-preview/2026-09-30.json remains available at /radar-preview/
- Production: the current data/briefs/YYYY-MM-DD.json renders at /frontier/ and its dated /frontier/briefs/YYYY-MM-DD/ route
- Initial1.0 snapshot is preserved exactly at data/brief-history/2026-09-30-v1.0.json and /frontier/briefs/2026-09-30/v1/; it is immutable and outside scheduled write paths
- Source snapshot: data/frontier.json, regenerated from its existing public parts. The overview does not change raw heuristic labels
- Full captured abstracts are not published. Public evidence stores canonical/pinned source links, capture time, normalized character count and SHA-256
- Preserve the single existing scheduled update. Migrating it to1.1 is a separate activation step after source and actual production UI review; this code adds no automation or cron

Version1.1 keeps all1.0 required fields and adds exactly one required top-level object, research_overview. Original selection counts remain historical provenance: complete_abstracts_checked_for_selection=6 is distinct from the overview's14 complete abstracts. Selection still has at most five papers; themes synthesize a broader source set.

## Exact research_overview fields

headline, executive_summary, coverage, topic_distribution, themes, evidence_sources, revision_note, limitations, candidate_records, keyword_caveats.

coverage contains nonnegative integer counts for candidate_metadata_screened, complete_abstracts_checked, full_papers_read, revision_diffs_checked, count_denominator; comparison_window_available is a boolean; topic_count_method is existing_title_abstract_keyword_heuristic_multilabel. This initial1.1 contract requires0 full-paper reads,0 version diffs and no temporal comparison. A later richer evidence contract needs its own validation.

candidate_records retains only versioned_id, title, first_submitted_at, updated_at, change_type, matched_topics for every candidate in the declared observation window. IDs exactly equal the parent candidate_ids. Retention is necessary so archive distributions remain reproducible after the current frontier snapshot advances.

topic_distribution includes all nine current query-label IDs. Each row has topic, label, count, new, revisions, candidate_ids. IDs are unique per row and exactly match retained keyword tags; count equals membership size and new+revisions. Multi-label counts overlap. Zero matches do not establish the absence of research.

themes has at most five rows. Each contains id, title, summary, shared_problem, method_routes, open_question, evidence_ids, related_topics, attribution and comparison_scope. Each route has text and nonempty evidence_ids. Theme IDs equal the union of route evidence IDs. Attribution is curator_synthesis; comparison_scope is within_window_no_temporal_trend. Ready briefs need a theme; error/no_material_update briefs cannot repeat themes.

evidence_sources rows contain versioned_id, version_url, source_url, title, level, source_type, checked_at, abstract_complete, full_paper_read, experiments_independently_verified, version_comparison_performed, abstract_chars, abstract_sha256. IDs must be within the window. Version links are pinned arXiv URLs. Source type is arxiv_api_atom or arxiv_abstract_page; level is primary_complete_abstract. The complete-abstract flag is true; the other three evidence flags are false. SHA-256 uses UTF-8 after collapsing Unicode whitespace to single ASCII spaces and trimming ends. No hash of a summary may stand in for the full abstract hash.

keyword_caveats has at most ten rows: versioned_id, topic, issue, explanation, evidence_basis. A false_positive must refer to an actually present keyword tag; a missed_match must refer to an absent tag. Evidence basis is snapshot_excerpt or complete_abstract; the latter must resolve to a full-abstract evidence source. Caveats are window-specific rather than hardcoded into future pages.

## Validation and UI

The loader rejects extra fields, boolean counts, duplicate/unresolved/out-of-window IDs, malformed URLs, missing source hashes, contradictory flags, distribution mismatches and unsupported comparison claims. Whenever the brief's source hash matches the current snapshot, retained metadata is also compared to actual frontier bytes. Archived1.1 briefs retain their bounded metadata for validation after that snapshot changes.

The production view leads with an editorial finding, then a small window count. Research themes expose their synthesis before optional method/source details. Original selected summaries follow as a secondary section. All window records remain searchable; the seven-day feed follows as a separate candidate queue. The initial approved window has42 records, while its source feed has253. Coverage and known tag false positives/false negatives stay visible. A stale/error banner precedes the editorial lead. Native details and separate source links preserve keyboard access; narrow views simplify rather than adding a sticky multi-row toolbar.
