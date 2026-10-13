# Atlas experience upgrade

This presentation update is based on `c26f035` and keeps the Python static publisher, native JavaScript controllers, public data contracts and GitHub Pages subpath. It adds no account system, tracking or model dependency.

## Main changes

- The homepage combines a research introduction, a bounded interactive constellation and the existing library. Counts and eight example links derive from canonical records and their browse memberships. The bounded decorative star field is explicitly abstract; its stars are not additional paper records.
- A shared `site_chrome.py` renders navigation, search, dialogs and footer. Production uses `site.css`, with narrowly scoped styles for the homepage, map, current reader and research workspace. Previous F2/editorial theme files remain only for retained design/history consumers.
- Library rows expose title, research description, metadata and one quick-view action. The quick view retains source distinctions, resources, report stages and classification details, and keeps its detail action accessible at the bottom. Search failure remains actionable while editing the query and can be retried.
- The research map uses a nine-direction overview with results alongside it. A selected paper and its related-paper chain preserve the source filter, camera and visible return target.
- The navigation workspace retains its four existing views and exact state model; a persistent identity strip and narrow-screen tree/reader switch improve orientation. Its inline research startup does not wait for optional shared presentation resources. Native task/directory pages retain all static content and use the same chrome.
- The reading archive presents a three-stage matrix. Current readers reuse the shared header and add figure expansion, readable columns, chapter controls and meaningful browser titles. The original inline reader scripts remain intact; old UMI search scripts receive only separate chrome enhancement, without duplicate handlers.

## Preserved boundaries

All 95 catalog IDs, classifications, sources, statuses and canonical data files are unchanged. All 21 registered fixed report artifacts remain identical to their SHA-256 registry; 12 current reading routes preserve the original article, formula, image, code, inline-style and original script bytes. Presentation scripts are independently allowlisted and versioned in regression checks. Current routes, original fixed-report links, catalog parameters and research hashes remain compatible.

## Verification

Use the pinned Node 24 toolchain and the existing build/validation commands in README. New targeted JavaScript tests run in both PR validation and Pages build workflows. They cover shared navigation/search retry, reader figures, map selection-origin restoration and research-workspace mobile states. Structural/unit results establish controller and preservation behavior; rendered screenshots and manual browser journeys remain separate evidence.

The sealed historical C2 portable fixture calls `python`, while the current build uses `python3`. On systems without `python`, provide a test-local alias to Python 3 in PATH; do not rewrite that sealed historical fixture.
