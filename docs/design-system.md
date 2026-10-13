# RoboPaperAtlas interface system

The live site uses a light, quiet reading surface with a separate dark research constellation. The shared production stylesheet is `assets/site.css`; it replaces the earlier stack of `styles.css`, `experience.css`, `library.css`, `library-editorial.css`, and `f2.css` on current routes. Those historical files remain available to frozen previews. Fixed-version reading reports keep their original content and styles.

## Ownership and structure

`site.css` is organized into four readable sections: tokens, base, shared components, and page layouts. Responsive rules are collected after the page layouts. Add a component to its owning section; avoid appending a second theme or a late override stylesheet.

| Module | Responsibility |
| --- | --- |
| `site.css` | Shared navigation, controls, search, preview drawer, footer, catalogue, paper details, reading archive, Radar, submission guide, About |
| `home-hero.css` | Home headline, constellation preview and brand motion |
| `paper-map.css` | Research-map visualization and results workspace |
| `reader-current.css` | Current reader layout and article controls; frozen artifacts are unchanged |
| Navigation product styles | Three-tree workspace and its own controls, scoped to its product root |

The `atlas-theme`, `f2-theme`, and existing semantic component classes remain compatible. The transitional `--f2-*` variable aliases point to the current tokens, and do not constitute a second theme.

## Visual values

| Role | Value |
| --- | --- |
| Page / content | `#FAFAF8` / `#FFFFFF` |
| Primary / body / secondary text | `#171A19` / `#38423D` / `#626B67` |
| Border / strong border | `#E2E6E2` / `#C0CCC3` |
| Accent / hover | `#315C4B` / `#234735` |
| Soft accent / neutral fill | `#EAF1EB` / `#F0F3EF` |
| Reading / warning accents | `#67557E` / `#856326` |
| Dark constellation | `#0C1418` |
| Corner radii | 8px controls, 12px panels, 20px home constellation |

Use the local system sans-serif stack; code uses a monospace stack. Body size is 18px, or 17px below 760px. Titles, research questions, authors and provenance have distinct levels. Secondary metadata may use 13–14px, but essential reading text must not be reduced to metadata size.

Ordinary content is at most 1280px wide, excluding horizontal page padding. Padding is 40px by default, 32px below 1200px, 20px below 760px, and 16px below 380px. Current-reader article measure and research-workspace widths belong to their respective modules.

Desktop navigation is 64px high. Below 980px it wraps to a mobile menu with a 68px minimum closed height. The `--site-header-height` variable controls intrinsic height. The measured `--site-header-offset` controls sticky positions and anchor clearance, with intrinsic height as its fallback; measuring must never change intrinsic height. Fixed-height workspaces that require exactly 64px should scope their own header variable.

## Behavior and accessibility

- Primary controls have at least 44px targets and visible keyboard focus. Selected filters use `aria-pressed`; selected navigation uses `aria-current`. Selection does not depend on color alone.
- `hidden` remains authoritative for all dynamic and loading states. Closed native dialogs stay closed; do not give `dialog` a universal `display` rule.
- The global-search button and mobile-menu button are available after `body.js-ready`. Without JavaScript, mobile navigation remains visible, paper titles remain ordinary links, and the full static catalogue remains usable.
- The preview drawer is 560px on desktop and full width on small screens. It scrolls independently; its heading and close control stay visible. Closing, focus restoration and catalogue state are owned by the existing JavaScript controllers.
- Filtering is a native dialog when enhanced, with the original `details` panel as fallback. Active filters, method chips, reset and retry retain their existing state hooks.
- The reading archive uses three stage columns, collapsing to one below 760px. Missing stages keep their explicit “尚未导入” state. Current reading, fixed reports and historical versions remain distinct links.
- Radar retains separate historical, no-update and error states, source counts, observation windows and denominators. Its enhanced focus layout and no-script `details` are both styled.
- Submission-guide disclosure states (`when-open`, `when-closed`) and route-specific profile/case/deadline layouts remain part of the shared stylesheet.

## Motion and maintenance

Controls use 160ms transitions. Search, filters and drawers use 260ms entry motion with `cubic-bezier(.22,1,.36,1)`. Filter-result feedback uses a short opacity transition. Content is present before animation starts, and page scrolling remains native.

`prefers-reduced-motion: reduce` removes animation and transitions. Print styles remove navigation, controls, dialogs and decorative surfaces, and display digest panels in document order. Home and research-workspace animation lifecycle is managed by their own scripts.

When reviewing a change, follow a complete interaction: search → filter → preview → detail → reading → back. Check the 360/390/768px and 1024/1280/1440px layouts, native dialog focus, keyboard selection, reduced motion, failed loading/retry, and a JavaScript-disabled page. A stylesheet parse or static markup check alone is not evidence that these user flows work.
