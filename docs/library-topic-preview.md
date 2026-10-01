# Isolated library search preview

`library-topic-preview/` is a search-first presentation proposal. It does not replace the main catalog, Atlas, Radar or reader routes. The full site is built by `scripts/build_previews.py`: it validates the four preview files, runs the unchanged `scripts/build.py` once, then appends this route. No publishing is performed by these commands.

## Reader contract

- Start with all 95 unique catalog papers. No category selection is required
- The two common searches, 导航 and 移动操作, are ordinary query shortcuts
- Methods, platforms and resource types appear only under More filters
- Multiple values in one filter group use OR; different groups use AND
- Recognized task and method queries use evidence-backed relations and exact normalized labels. `RL` cannot match a substring of `world`
- A task's direct research, execution evaluation and qualitative demonstration appear in the main list. Data/component/tool-only associations and unconfirmed task relations are separately counted in closed disclosures
- Mobile manipulation can match a broader manipulation search. This does not establish separate fixed-base execution
- Every card explains its match. Details preserve task strength, simulation versus hardware boundaries, method-versus-contribution distinctions and links to supporting sources
- Metadata, aliases and all-library text retrieval remain available even where a facet is unknown. Partial evidence indexing is not a claim of complete 95-paper full-text review
- Resource types do not certify current download or code availability

The public `topics.json` file is a strict field projection containing bibliography, research statements, partial coverage, supported facets and public source links. It excludes private provenance and operational notes. It does not replace the scientific source records or modify bibliography/reading status elsewhere.

## State and access

The query and selected facets are encoded in the route URL. Paper details use a native modal dialog and a `paper` URL parameter. Close, Escape, Back and Forward retain the list query and facets; closing restores focus to the corresponding paper and list scroll position. `/` and Ctrl/⌘K focus search; submitting search focuses the result region. Filters can be removed individually or reset together.

Body and reasons use 16–18px text, metadata is at least 14px, and interactive controls have 44px targets. The layout uses the existing site's typography and spacing with no new animation. Full author lists remain available in detail; long lists are shortened on cards.

## Reproducible checks

Run the repository's complete workflow, using `python3 scripts/build_previews.py` for the final site build. Focused checks are:

- `python3 -m unittest discover -s tests -p test_library_topic_preview.py -v`
- `node tests/test_library_topic_preview.cjs`
- `python3 scripts/build_previews.py`
- `python3 scripts/validate.py`

Checks cover strict nested field allowlists, approved HTTPS source hosts, exact catalog metadata, source-reference integrity, partial/unknown states, source/output symlink rejection, HTML escaping, 190 frozen semantic-reference cases, all-title/alias retrieval, query-dependent reasons, independent filter operations, URL state type-size floors, and seven actual-controller model scenarios including repeated Close/Escape and history restoration.

Only the four existing files under `dist/library-topic-preview/` may differ from the accepted baseline. All other generated files, including verified relationships and the latest reader quotations, must remain byte-identical.

Real-browser desktop/mobile, focus, keyboard and visual acceptance remain separate from the Node controller models and static checks. No visual or real-browser pass is claimed by the unit tests.
