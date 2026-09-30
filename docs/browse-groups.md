# Browsing groups and researched classifications

The Library front page has All plus four broad Chinese browsing shortcuts:
导航与空间理解、运动与操作、机器人学习、基础方法与研究资源.
They overlap. Counts describe matching entries and cannot be summed into the95 unique papers.

The shortcut adapter does not edit the catalog or its separately audited scientific classifications. Detailed primary question, secondary directions, problem label, methods, resource kinds, uncertainty and evidence remain available in the advanced filters and paper details. Whole-body control is a method; it does not force ODYSSEY or UMI-on-Legs into a primary WBC category.

`scripts/discovery_facets.py` derives membership only from existing reviewed fields:

- Navigation/spatial understanding: primary or secondary navigation/spatial-representation directions
- Motion/manipulation: primary or secondary mobile manipulation, whole-body motion/control or locomotion
- Robot learning: policy-learning direction or explicitly recorded learning methods, excluding general-ML primary records
- Foundations/resources: general-ML direction, recorded dataset/benchmark/data collection/generator/simulator/software kinds, or the explicit cross-domain resource state

The four general-ML foundation papers stay in foundations/resources. Their usefulness for robotics does not by itself make them robot-learning papers. A released model is not automatically treated as a general research resource. HoloAgent-0 can be found through its reviewed secondary directions while retaining its cross-domain scientific placement.

Every one of95 entries must have at least one evidence-derived shortcut; there is no unknown-title fallback. Current overlapping counts are29/46/48/29. Membership reasons are retained in the shared projection. The global-star preview consumes the same projection while preserving the original primary classification and relation evidence.

The main toolbar exposes only four groups. Common method choices are inside More filters, followed by optional complete method, detailed-direction, resource, year and source-status controls. Old `?topic=<detailed-direction>` links restore that exact direction as an advanced constraint; they are not silently broadened. New group links use `?topic=<browse-group>`; exact advanced direction constraints use `?direction=<detailed-direction>`.

The global-star route is an isolated interaction preview. It keeps all95 real paper nodes visible, dims nonmatches, and shows only11 checked relation records across8 directed pairs. A missing edge is an indexing limit, not evidence that papers are unrelated. It does not replace the current Atlas route.
