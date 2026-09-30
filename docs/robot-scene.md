# RoboPaperAtlas robot vignette

Original, dependency-free SVG illustration. The 14-second conceptual sequence is: approach → target recognition → reach and light gripper movement → retract → step back. No actual robot, paper, experiment, simulator, telemetry, or research result is represented.

## Production assets

- `hero-robot.svg`: inline inside the root; contains the useful static reach pose, accessible title/description, and original artwork
- `hero-robot.css`: all selectors scoped to `.robot-vignette`
- `hero-robot.js`: deferred, classic vanilla JavaScript; creates one real pause/play button
- `hero-robot.html`: optional ready-to-insert markup, including the inline SVG and caption

Load the CSS and deferred JS once, and insert `hero-robot.html` in the hero's right column. The HTML is a fragment, not a complete document. Content-hashed CSS/JS asset URLs are safe; the SVG should be inlined, not loaded with an `img` element if motion is wanted.

Minimal integration structure:

```html
<figure class="robot-vignette">
  <!-- Insert the complete contents of hero-robot.svg here. -->
  <figcaption class="robot-vignette__caption">
    <span>概念示意，非实验演示</span>
  </figcaption>
</figure>
```

The component fills its own column. Suggested desktop column width: 44–48% of a two-column hero. Keep the text and figure in separate grid columns; do not overlay the SVG across the heading. The SVG uses `viewBox="0 40 700 460"`; its artwork is transparent and designed for `#0b0d12`. The complete motion has a minimum painted Y of 89.75 (the elbow disk including its stroke); the viewBox starts at Y=40, leaving at least 49.75 SVG units of top clearance. Do not crop this viewBox or place it in an overflow-hidden fixed-height frame.

On phones, a normal-flow figure beneath the title is appropriate. CSS caps the component at 540px; a narrower parent is safe. At viewport widths of 767px or less, or whenever reduced motion is requested, the component uses a static, extended-arm state and hides the unnecessary motion control. No JavaScript also leaves a useful static illustration and the supplied caption.

## Lifecycle and motion

The script auto-initializes on DOM ready. For markup added after initial load, call `window.RoboPaperAtlasRobot.init(container)`; initialization is idempotent. Before deliberately removing a live component in a client-side router, call `figure.robotVignetteDestroy()`. Removed active components also self-clean on their next animation frame.

The scene pauses when hidden or offscreen and resumes from its saved time, without advancing while suspended. Manual pause is independent and persists through visibility changes. The button is keyboard-operable, has changing accessible labels and pressed state, and has a visible focus style. No pointer tracking or mouse capture is used. Media-query changes are respected live.

During approach and retreat, one foot lifts at a time and the remaining feet stay planted in world coordinates. A two-link geometric solve keeps each leg and arm segment length fixed. This supports a coherent illustration; it is not a physical simulation. The target itself remains in place.

Multiple initialized instances receive unique SVG IDs. This component uses no external fonts, network requests, packages, image assets, or framework runtime.

## Validation and limits

SVG screenshots of the folded, walking, recognition, reaching, returning, and mobile poses were rendered with Inkscape and visually inspected. JavaScript syntax and a DOM-mock test covering two full animation loops, constant segment lengths, pause/play, visibility, offscreen suspension, mobile/reduced-motion switching, and initialization lifecycle passed.

A real-browser end-to-end test remains necessary in the host page. Inkscape is a static SVG renderer, and the DOM mock does not establish browser CSS layout, actual IntersectionObserver delivery, keyboard focus, or assistive-technology output. Check the integrated hero at desktop and phone widths and with reduced motion enabled.
