# F2 interface implementation

The F2 presentation layer gives the paper library, reading archive, research radar and submission guides the same readable, neutral visual system. The independent C star map uses a navy exploration column beside the white paper list.

## Shared visual contract

- System sans-serif stack; no externally loaded or proprietary UI font
- Body text: 18 px on desktop, 16 px on narrow screens; line height 1.65
- Metadata: 14 px; controls: 16 px and at least 44 px high
- Spacing: 4, 8, 12, 16, 24, 32, 48 and 64 px
- Black primary actions, white content, neutral secondary surfaces and restrained green accents
- 8 px controls, 12 px panels, mostly divider-based editorial lists
- 160 ms hover and 220 ms disclosure transitions; reduced-motion override
- Visible keyboard focus, real empty/loading states and retained native disclosures

`assets/f2.css` is loaded after the existing page styles. The existing controllers remain responsible for filtering, search, history, reader navigation and submission routes.

## Template coverage

| Approved template | Route / implementation |
| --- | --- |
| Paper library | `index.html`: page introduction, full-width search, category controls and editorial rows |
| Paper overview | `papers/{id}/index.html`: source actions, reading path first, evidence sidebar |
| Reading archive | `reading/index.html`: current stages plus collapsible fixed/history version links |
| Stage 1 | `papers/{id}/reading/stage1.html`: neutral reading surface, chapter navigation, original figures |
| Stage 2 | `papers/{id}/reading/stage2.html`: existing source/analysis comparisons and source-location controls |
| Stage 3 | `papers/{id}/reading/stage3.html`: original math, code, figures and chapter/source controls |
| C star map | `map/index.html`: portrait constellation column, persistent direction selection and explicit problem drill |
| Research overview | `frontier/index.html`: editorial lead, research themes, evidence boundaries and complete observation window |
| Dated brief | `frontier/briefs/{date}/index.html`: preserved dated evidence and historical brief forms |
| Conferences/journals | `submit/index.html#venues`: editorial channel rows with actual status and source-derived summaries |
| Channel details | `submit/index.html#venues/{id}`: source-backed profile, policy snapshot, timeline and evidence |
| Submission experience overview | `submit/index.html#experiences`: synthesis, source boundaries and experience rows |
| Submission experience details | `submit/index.html#experiences/{id}`: full existing narrative and provenance |
| Deadlines | `submit/index.html#deadlines`: readable date rows preserving original time zones and verification status |
| Published examples | `submit/index.html#papers`: existing multi-axis publication filters and evidence-backed example rows |
| About | `about/index.html`: reading/connection/tracking purpose and contribution/source standards |

The concept illustrations are composition references, not data sources. Their placeholder papers, dates, equations, counts and claims are not imported. Actual taxonomy, source labels and missing-state boundaries take priority.

## C star map behavior

The overview is a portrait constellation with all nine canonical directions. Selecting a direction filters the adjacent paper list while retaining the overview and a selected-direction marker. “展开研究问题” enters the existing problem hierarchy. Search, paper selection, keyboard navigation, Back/Forward, resetting, and the optional mobile map preserve the real catalogue. The five additional directions remain available in a native disclosure as well as the scrollable map. Positions are navigation geometry, not citation, importance, time or measured similarity data.

## Reader preservation boundary

The 21 registered fixed report artifacts remain byte-identical. The 12 current reader routes are generated from the same approved artifacts. Only current navigation, provenance wording, a body presentation class and a versioned F2 stylesheet reference change. The original article, images, equations, code, inline scripts and inline styles are retained. On narrow screens, the current reader’s existing is-open/inert/Escape controller drives an inline chapter disclosure; its closed state occupies no layout space. Collapsing the source panel removes its desktop grid track. The F2 stylesheet is loaded after the last fixed stylesheet and before the inline reader runtime measures layout.

## Verification boundary

The implementation includes structural and preservation tests, plus C overview/scroll/history regressions. These are not browser screenshot acceptance. A complete build still requires the repository's pinned math preparation step and full CI. Final desktop/narrow browser comparison, focus/overflow inspection and hosted route checks must be completed against the built candidate before visual sign-off.
