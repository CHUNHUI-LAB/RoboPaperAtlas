# Atlas

`/map/index.html` explores the 95 canonical papers as a stable hierarchy: galaxy → research direction → problem subsystem → paper. The route remains stable. The product name is RoboPaperAtlas and this feature is Atlas.

## Classification and evidence

`data/catalog.json` is unchanged. The additive `data/classification.json` overlay explicitly places all 95 IDs and preserves their original category, title, links, citation-verification status and reading stages. `scripts/atlas_taxonomy.py` rejects missing, extra or duplicate IDs and unknown placements; it never classifies by keyword fallback.

The source review covers official abstracts and project/contribution text for all 95 entries. It does not claim 95 full-paper readings or bibliographic verification. Four overlap cases remain visibly provisional, with reasons and source links. Method components and resource types appear separately from the primary research problem; an evidenced component does not necessarily represent the paper's novelty.

The current primary counts are Embodied Nav 18, Mobile Manip. 19, Motion & Control 20, Locomotion 2, Policy Learning 21, Spatial Repr. 3 and General ML 4. Resources has 7 cross-domain resource entries; Cross-domain contains one research entry with no unique primary direction. These nine placements sum to 95. Secondary directions, method tags and resource kinds may overlap and are not additional stars. Policy Learning includes simulated-character policy research as well as robot policies.

Taxonomy revision 3 applies two reviewed consistency corrections to revision 2: the badminton paper exposes Motion & Control as its supported secondary direction, and RoboDuet joins the existing Coordinated Motion subsystem rather than creating a duplicate same-name subsystem. Source scope, pending flags and canonical data remain unchanged.

## Interaction

- The galaxy has distinct direction colors and labeled systems. Select a system to see problem subsystems; select a problem to see named paper stars. Search can jump directly to any of the 95 papers from any level
- Positions are deterministic. Drill navigation changes the camera without running a physics simulation or random spin. Decorative navigation orbits, background glow, distance, order and star size do not encode citation, chronology, scientific similarity or importance
- Every paper has one star. A system's central navigation symbol is a labeled control, not another paper. Default paper marks have equal sizes within the current view
- Breadcrumbs, Back, Escape and browser Back/Forward restore hierarchy and visible focus. New navigation cancels old camera animations and captured pointer clicks
- Desktop dragging is immediate. Ordinary wheel scrolls the page; Ctrl/Command plus wheel zooms. Zoom buttons, fit, arrows, Enter/Space, Home/0 and +/- are provided. Paper targets remain 44px; system controls are at least 54px
- Mobile defaults to the complete server-rendered paper list. The optional map uses simple controls and labeled direction buttons; physical-device touch testing is not claimed
- The non-modal side panel shows classification support, unresolved boundaries, methods, resource types, original metadata, PDF/code links and actual Stage availability. Only rpa-0062 has three imported reports; the other 94 entries remain disabled
- The panel's Library link searches for the exact displayed title, so it does not silently equate an older Library facet with a new primary direction
- There are no verified citation edges. At most six dashed shared-tag inference links are drawn for the current selection and visible scope; each actual shared tag is listed. Missing shared tags produce a same-primary-group navigation list with no edges
- Reduced motion, hidden documents, offscreen views, resize, close, search and view changes cancel ongoing animation. No ambient animation, network requests, API/model calls or tracking are used

## Integration and checks

The map renderer returns a `<main>` fragment for the existing shell and accepts hashed CSS/JS URLs plus `report_records`. Integrate only the changed map files, additive taxonomy and tests. Preserve concurrent reader work and canonical data. A separate shared-nav patch can rename the map's shell title to Atlas without replacing build.py.

```sh
python3 scripts/assemble_frontier.py
python3 -m unittest discover -s tests -q
node tests/test_hero_atlas.cjs
node tests/test_brief_reader.cjs
python3 scripts/build.py
node --test tests/test_map_core.cjs tests/test_map_dom.cjs tests/test_atlas_hierarchy.cjs tests/test_catalog_facets.cjs
python3 scripts/validate.py
```

The DOM fixture executes the real production script on generated markup. It is not a rendering engine. The hierarchy suite checks all 95 search targets, unique deterministic placement, narrow fit, correct drill/back/history focus, pending evidence, and interrupted pointer cancellation. The optional `tests/map_browser_qa.cjs` requires an allowed browser and preview; browser appearance and physical touch remain separate acceptance gates.
