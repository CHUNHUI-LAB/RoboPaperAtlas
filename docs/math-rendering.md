# Static LaTeX rendering

The UMI Stage 3 preview uses KaTeX 0.18.9 at build time. Exact section hashes bind 48 reviewed LaTeX records to 54 mathematical occurrences in the existing report. Paper expressions, explanatory transforms and code-equivalent rewards keep separate provenance. In particular, the unexpanded paper error and the code's squared norm/weight 4 are not merged, and the printed curriculum value 0.1 is retained.

## Build

Use Node24 and Python3. Run `npm ci --ignore-scripts --no-audit --no-fund`, then `npm run prepare:math`, followed by the repository's report assembly/test/build commands. The npm lock pins source integrity. KaTeX executes only in the trusted build, with strict parsing, trust disabled and bounded macro expansion. Parse failures stop the build.

The published preview contains static HTML and accessible MathML; it does not load a browser math renderer or a CDN. KaTeX's local CSS, WOFF2 fonts and MIT software license are copied from the pinned package to the generated site. The three display equations also expose their LaTeX source as a static fallback. Font-specific SIL Open Font License1.1 notices and the original embedded font metadata are retained, without renaming or modifying the font binaries. Data and code in the original three report artifacts are unchanged.

Generated vendor assets, node_modules and rendered caches are excluded from Git transport. CI recreates them from the lockfile. The existing standalone v1 downloads are preserved; this preview does not claim that their equations were updated or that a new offline report version has been published.
