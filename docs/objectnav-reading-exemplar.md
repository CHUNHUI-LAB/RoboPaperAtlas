# ObjectNav isolated reading example v1

Route: `review/objectnav-reading-v1/`. This route is additive; no default tree entry changes.

The default page shows task identity, a concrete example, benchmark/method conditions, SemExp/PONI/VLFM interface comparisons, and what PONI retains/replaces with evidence. Challenge–insight and the original five-chapter template expand on demand. Direct hashes reveal their containing details and focus the target; native links preserve browser history. External papers open separately. The page remains readable without script.

## Evidence and scope

- ObjectNav task freeze SHA-256 `9de490edcc03a8ebc7e3dfe5f1dcec64f1edeecb2b928c882aeb8b46b409f1ba`.
- SemExp/PONI method freeze SHA-256 `1ce8f9d0725b5006c8017979590c1490d47684a19d84f605124878d07aafd77a`.
- Existing original 59 template nodes and PONI's 22 scoped answers are unchanged in the projection. Unfilled nodes stay unfilled. Original structural notes are visible, with the explicit caveat that preserving the Limitation note does not endorse concealing genuine limitations.
- New-page-only VLFM source check: arXiv:2312.03275v1, 2023-12-06, selected sections III, IV-B–D, VI-C, VII. This is a pinned preprint, not a claim of camera-ready/full reading/code review/reproduction. The original tree's prior source records remain unchanged.
- No cross-paper performance ranking, global-first claim, expanded literature taxonomy, formal reading-stage promotion, or experiment execution.

## Build and validation

The existing CI command `python3 scripts/build_previews.py` includes this isolated route after the original three-tree preview. Normal `build.py` remains unchanged. Source hashes and exact file allowlists are checked before output cleanup. Missing, tampered, resealed science or unsafe paths fail closed. Only generated HTML, CSS and JS are copied publicly, not raw research inputs.

Focused checks:

```
python3 -m unittest discover -s tests -p test_objectnav_reading.py -v
node tests/test_objectnav_reading.cjs
```

Also run the full current repository CI command sequence before release. The JS test is a deterministic DOM fixture, not a real-browser claim. Real narrow-screen, keyboard, focus, Back/Forward and external-source acceptance remain deployment-gated; no local browser denial may be bypassed. Do not promote the manifest's candidate status merely because unit tests pass.
