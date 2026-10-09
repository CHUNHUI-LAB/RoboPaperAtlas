# Navigation research workspace

Entry: `research/navigation/`, linked from `map/`.

Three expandable hierarchical trees share exact task, benchmark/protocol, canonical paper, source version and evidence context. The outline uses the same placements. Cross-tree return and browser history preserve selection, expansion, tree/detail/page scroll. Unknown identities, mixed versions and altered input data fail closed.

## Content boundaries

The frozen model contains 89 paper identities and 63 mixed task/setting/protocol reading entries. Of 56 entries for which independent method coverage applies, 42 have selected method evidence and 40 have challenge–insight evidence. Remaining gaps stay explicit. Only three paper versions have imported analyses. The original template contains 59 nodes, including the root, chapters and groups, with 40 leaves. An explicit reference-template view for other versions has zero answers and does not change reading coverage.

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

## Bounded fixed-version evidence update

The language-described-object scope gains only condition-level CI evidence for VLMaps v2, ConceptGraphs v1 and HOV-SG v2. Existing unpinned recipe sources remain unpinned; fixed-version cards supplement them without counting duplicate methods. The other two scoped additions are Portable ObjectNav TAP v5 and the official CVPR2025 LH-VLN/MGDM paper. Their old unbound same-document version IDs remain explicit aliases, so the registry still has 274 source versions rather than counting either document twice. The unpinned Portable arXiv abstract source remains separate.

The model now contains 436 claims and 1641 placements. Fourteen method gaps and sixteen CI gaps remain among the 56 applicable reading entries. Existing 413 claims and all 1557 prior placement IDs are retained. Source statements and editorial synthesis are separately attributed; fixed-version cards retain assumptions, observation privileges, retrieval provenance and unverified limits. TAP-RL's global object-count snapshot is not local-only perception; MGDM's dataset retrieval is not evidence of personal lifelong memory or solved long-chain success.

This adds selected-section evidence, not new full-paper analyses, code verification or experiments. All three imported analysis contexts and the original 59-node template remain unchanged. Updating the input requires reviewed exact decoded/compressed hash and byte-length pin changes together; editing a manifest alone cannot authorize altered science. Preserve the current navigation controller and its share/history/workspace-jump safeguards when updating evidence. No dist output is a maintained source.
