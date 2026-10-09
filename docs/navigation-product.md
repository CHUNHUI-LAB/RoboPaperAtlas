# Navigation research workspace

Entry: `research/navigation/`, linked from `map/`.

Three expandable hierarchical trees share exact task, benchmark/protocol, canonical paper, source version and evidence context. The outline uses the same placements. Cross-tree return and browser history preserve selection, expansion, tree/detail/page scroll. Unknown identities, mixed versions and altered input data fail closed.

## Content boundaries

The frozen model contains 87 paper identities and 63 mixed task/setting/protocol reading entries. Of 56 entries for which independent method coverage applies, 40 have selected method evidence and 37 have challenge–insight evidence. Remaining gaps stay explicit. Only three paper versions have imported analyses. The original template contains 59 nodes, including the root, chapters and groups, with 40 leaves. An explicit reference-template view for other versions has zero answers and does not change reading coverage.

Input `data/navigation-product/model.json.gz` losslessly stores the independently reviewed JSON. Build pins both compressed SHA-256 and the exact decoded scientific SHA-256. The generated JSON retains those original bytes; runtime checks its SHA-256 before rendering. Source pointers, evidence corrections, relation roles, metric warnings and version boundaries remain in the model. No internal review notes or raw research files are published.

## Reproduce

```
npm ci --ignore-scripts --no-audit --no-fund
npm run prepare:math
python3 -m unittest discover -s tests -v
node --test tests/test_navigation_product.cjs
python3 scripts/build_previews.py
```

JSDOM exercises actual DOM/controller behavior, not visual browser layout or assistive-technology compatibility. Real browser acceptance is required after the authorized deployment. Original tree and ObjectNav archive routes remain available.
