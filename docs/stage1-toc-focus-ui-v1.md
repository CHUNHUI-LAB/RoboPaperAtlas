# Stage 1 v2 preview: TOC focus UI patch v1

Scope: only the three generated `reader-integration-preview/navigation-stage1-v2-20261005/*/stage1.html` views. No canonical promotion, frozen report edits, paper-content changes, or v1 history rewrites. The new `assets/reader-toc-focus-v1.js` is an explicit, cache-hashed presentation layer appended by the v2 preview builder. The fixed report's inline scripts remain byte-identical.

## Defect and minimal correction

At actual Chromium 200% zoom (590×378 CSS viewport; client width 582), opening the in-flow F2 TOC focuses section 01, but the legacy runtime centers the link's `offsetTop` as if it were TOC-local. For HoloAgent-0 and NavHarness the measured focus rect was y103.1875–147.1875 while the TOC began at y239.59375 (clientHeight207, scrollTop190.5, scrollHeight598). HarnessVLN also reproduced.

The additive layer saves TOC scrollTop only while open (scroll events and capture before button/link closure), then after the unchanged existing handler restores that scroll and uses link/TOC bounding rectangles to reveal only a clipped focused link. The visible bounds also intersect the viewport, because the in-flow TOC can extend below a short zoomed viewport. The open panel height is capped to the remaining viewport so the last item can also be reached; resize recomputes that cap and removes it for closed/desktop layouts. Already-visible positions are preserved; there is no always-scroll-to-top behavior. Only TOC scrollTop is changed. No focus, history, page-scroll, link-navigation, Escape, or propagation behavior is overridden.

## Verification

`node tests/test_reader_toc_focus_v1.cjs` executes the original open handler extracted from all three exact frozen reports before the compatibility layer. It covers measured 200% geometry, later sections, old scroll retention, close/reopen, stale deep scroll, the final TOC row, resize/desktop restoration, and 100% geometry. Python preview tests require unchanged article sections, unchanged inline scripts, exact fixed raw bytes, untouched v1, unchanged registry, and one hash-pinned layer per generated view.

DOM models are not actual-browser acceptance. Re-run the three HTTPS preview routes in normal Chromium at 100% and 200% after authorized preview deployment. At 200%, open TOC with keyboard Enter and verify the focused first/current link is visible both inside the TOC and viewport; use late sections, Escape/reopen, Tab, anchor navigation and Back/Forward. Preserve expected table-local horizontal scroll and no whole-page overflow.

Current frozen `first-pass.html` remains historical bytes and retains the legacy behavior. This patch intentionally does not silently repair historical downloads or broaden to canonical readers.

Boundary: the compact stagebar/button is itself in normal document flow. This layer fixes normal button activation with the TOC in the viewport. Synthetic activation of a fully offscreen TOC is not claimed to expose it; adding a fixed overlay or moving page scroll is deliberately out of scope. Test real late-section/button-return flows on HTTPS before acceptance. All close paths restore the temporary inline height through the existing aria-expanded state, without replacing the original handlers.

The DOM model implements display:none scrollTop reads as zero. It runs the unchanged original opening handler and simulates other close paths through the same expanded-state change; it is not a full browser event/scroll-anchoring test.
