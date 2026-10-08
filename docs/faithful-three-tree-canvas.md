# Original-image faithful canvas: rebuilt local candidate

This is a new reconstruction after the cloud workspace was replaced. Earlier
source identities and test results are historical only. This candidate has not
been published or tested in a real browser.

## Structure and scientific boundaries

The dual-tree example preserves 60 visible nodes and 59 original parent edges,
including Literature_tree → General goal → Literature tree / Challenge-insight
tree, variable depth, nested challenges, NeILF → NeILF++, pipeline-level Eclipse,
indoor pipeline / uncategorized siblings, annotations and unknown text.
The independent paper-analysis template retains its exact 59 nodes / 58 edges,
multiline leaves, asymmetric contributions and three ellipses.

The inverse-rendering example remains inside the corresponding trees in a
separate display namespace, never a fourth tree or a navigation paper.
Navigation keeps original occurrence IDs, source paths, parent edges, types,
39 paper IDs and 19 protocol IDs. Milestone, first-work and development
relationships are explicitly unmapped rather than invented. The 2 filled and
37 pending analyses, frontier records, evidence and formal reading states are
unchanged.

## Interactions

The #mindmap entry provides one viewport-sized canvas and one progressive
detail panel. Original #state and #analysis routes remain available. Nodes open
one original layer; normal expansion and selection maintain at least 1× camera
scale. Explicit whole/branch fit can zoom out without changing expansion.
Mobile skeleton geometry, breadcrumbs, exact direct-child links and the global
minimap preserve context. Drag, anchored zoom, Escape, Back/Forward, restored
camera/selection/detail scroll and fullscreen with fallback/visible exit are
covered by new deterministic regressions. Outdated fullscreen promises cannot
override the latest intent.

The detail panel retains complete original labels, uncertainty, paper-local
answers/gaps, evidence locations, ledgers and reading-scope boundaries. NavGPT
can follow literature → C05/I05-1 → its own pending analysis and return without
borrowing answers from HarnessVLN or NavHarness.

## Recovered original images

Both freshly reattached PNGs were materialized by the official Library route to
the conversation workspace and actually inspected. The 2048×1421 dual-tree PNG
has SHA-256 c69e3c4cbd47a74b7a98b7b26c02e0b4ff8df49584fffafb26c0c2f6a8791e64;
it is the newly supplied image identity, not falsely labelled as the earlier
JPEG bytes. The 1225×2048 analysis PNG retains SHA-256
60b1b2e8e38d912de02c18873e1c9b261fb6625564330d454c28326ef4b4aee6.
Both exact byte streams are embedded in the existing c2.js runtime asset.
The full-resolution modal supports scrolling and scaling. A mandatory separate
image gate rejects missing data or wrong hashes; the defensive unavailable
message does not waive this gate. Original-image bytes are now recovered;
actual-browser visual acceptance remains pending.

## Validation

Run the complete repository workflow and tests/test_faithful_tree_canvas.cjs,
which Python discovery also invokes. No old test is deleted. The old blanket
scale() prohibition is limited to the unchanged legacy renderer, preserving its
assertions while the requested new zoom behavior has direct camera tests.
The original 14-file public runtime allowlist remains unchanged.

These model/DOM tests do not establish actual font layout, mobile/touch usability,
native browser fullscreen behavior or browser history. Those remain separate
acceptance gates for the final source identity. The mandatory image-byte gate is independent of the defensive unavailable-state
regression and must pass before completion is claimed.


## Viewport obstruction correction (local candidate, 2026-10-07)

This candidate starts at deployed main `70daf7e68bcf13ad1000dc44e31872a874d7f3f2`
and fixes the subsequently observed 1180 × 757 browser defects. It is not a
claim that the changed bytes have passed deployed-browser acceptance.

- The minimap reserves space in an independently collapsible sidebar. The hint
  reserves its own row. Neither overlays selectable canvas nodes, including
  the root and General goal after fit. The narrow-screen detail rail also
  reserves layout space instead of covering the canvas.
- The independent analysis root and five unchanged original main branches use
  tighter card spacing at normal 14 px label size. No branches are omitted.
- A shallow high-fanout branch uses screen-dependent sibling columns with
  direct original-parent connectors routed through card gutters. These are
  geometric columns, not new research groups. All 19 protocol positioning
  controls remain available in a separate sibling strip. The full source
  graph, minimap identities, and scientific parent relationships are unchanged.
- Focus mode compacts the header and initially hides details and minimap. It
  is labelled “页内专注” unless the browser actually enters native fullscreen.
  The mode never invokes fit automatically. Exiting an unchanged branch
  restores its exact pre-entry camera; deliberate in-focus selection and
  expansion remain intact. Both panels can be opened in focus mode.
- Explicit fit remains an overview, with a visible small-text explanation and
  a “放大阅读” action. Ordinary selected-node navigation stays at least 1×.

Run `tests/test_tree_viewport_obstructions.cjs` as well as the existing faithful
canvas/image-byte suites and complete official workflow. The new regression
uses the observed viewport dimensions and asserts the absence of overlay nodes,
complete five-branch geometry, 19-sibling visibility, connector/card separation,
page-focus/native-fullscreen distinctions, preserved/restored cameras, side
panels, image scale, history, and Escape. DOM geometry models cannot establish
CSS font layout or actual native fullscreen behavior. The exact two PNG hashes,
39 papers, 19 protocols, 2 filled and 37 pending analyses remain protected by
the original independent gates. Only reviewed UI release hashes are resealed;
scientific, image and historical baseline hashes are not changed.
