/* Original RoboPaperAtlas concept illustration. No simulation or experiment data. */
(() => {
  'use strict';
  const clamp = (n, a = 0, b = 1) => Math.max(a, Math.min(b, n));
  const ease = n => { n = clamp(n); return n * n * (3 - 2 * n); };
  const mix = (a, b, t) => a + (b - a) * t;
  const polarIK = (hip, foot, upper, lower) => {
    const dx = foot[0] - hip[0], dy = foot[1] - hip[1];
    const distance = clamp(Math.hypot(dx, dy), .01, upper + lower - .01);
    const angle = Math.atan2(dy, dx) - Math.acos(clamp(
      (upper * upper + distance * distance - lower * lower) / (2 * upper * distance), -1, 1));
    return [hip[0] + upper * Math.cos(angle), hip[1] + upper * Math.sin(angle)];
  };
  const line = (el, a, b) => {
    el.setAttribute('x1', a[0].toFixed(3)); el.setAttribute('y1', a[1].toFixed(3));
    el.setAttribute('x2', b[0].toFixed(3)); el.setAttribute('y2', b[1].toFixed(3));
  };
  const point = (el, p) => {
    el.setAttribute('cx', p[0].toFixed(3)); el.setAttribute('cy', p[1].toFixed(3));
  };
  const definitions = [
    ['back-far', [252, 237], [237, 332], 56, 56, .50],
    ['front-far', [385, 226], [374, 327], 57, 57, .25],
    ['back-near', [304, 270], [283, 373], 60, 60, .00],
    ['front-near', [405, 254], [418, 358], 59, 60, .75]
  ];
  let instance = 0;
  function initialize(root) {
    if (root.dataset.robotInitialized) return;
    const svg = root.querySelector('.robot-vignette__scene');
    if (!svg) return;
    root.dataset.robotInitialized = 'true';
    // Inline SVG paint-server and accessible IDs must be unique per instance.
    const prefix = `rv-${++instance}-`;
    const previousLabels = (svg.getAttribute('aria-labelledby') || '').split(/\s+/);
    const ids = new Map();
    svg.querySelectorAll('[id]').forEach(el => {
      const old = el.id; ids.set(old, prefix + old); el.id = prefix + old;
    });
    svg.querySelectorAll('*').forEach(el => {
      for (const attribute of [...el.attributes]) {
        const value = attribute.value.replace(/url\(#([^)]+)\)/g, (match, id) => ids.has(id) ? `url(#${ids.get(id)})` : match);
        if (value !== attribute.value) el.setAttribute(attribute.name, value);
      }
    });
    svg.setAttribute('aria-labelledby', previousLabels.map(id => ids.get(id) || id).join(' '));
    const robot = svg.querySelector('[data-robot]');
    const shadow = svg.querySelector('[data-robot-shadow]');
    const recognition = svg.querySelector('[data-recognition]');
    const lock = svg.querySelector('[data-target-lock]');
    const arm = Object.fromEntries([...svg.querySelectorAll('[data-arm]')].map(el => [el.dataset.arm, el]));
    const grip = svg.querySelector('[data-gripper]');
    const topFinger = svg.querySelector('[data-finger="top"]');
    const bottomFinger = svg.querySelector('[data-finger="bottom"]');
    const legs = definitions.map(([name, hip, rest, upper, lower, offset]) => {
      const el = svg.querySelector(`[data-leg="${name}"]`);
      return {hip, rest, upper, lower, offset,
        bones: Object.fromEntries([...el.querySelectorAll('[data-bone]')].map(n => [n.dataset.bone, n])),
        knee: el.querySelector('[data-joint="knee"]'), core: el.querySelector('[data-joint="knee-core"]'), foot: el.querySelector('[data-foot]')};
    });
    let caption = root.querySelector('.robot-vignette__caption');
    if (!caption) {
      caption = document.createElement(root.tagName === 'FIGURE' ? 'figcaption' : 'div');
      caption.className = 'robot-vignette__caption';
      const text = document.createElement('span'); text.textContent = '概念示意，非实验演示';
      caption.append(text); root.append(caption);
    }
    const toggle = document.createElement('button');
    toggle.type = 'button'; toggle.className = 'robot-vignette__toggle';
    const icon = document.createElement('span'); icon.className = 'robot-vignette__toggle-icon'; icon.setAttribute('aria-hidden', 'true');
    const label = document.createElement('span'); toggle.append(icon, label); caption.append(toggle);
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const compact = window.matchMedia('(max-width: 767px)');
    let userPaused = false, inView = !('IntersectionObserver' in window), elapsed = 0, previous = null, frame = 0, disposed = false;
    const isStatic = () => reduced.matches || compact.matches;
    const canRun = () => !disposed && !userPaused && inView && !document.hidden && !isStatic();
    function controls() {
      toggle.hidden = isStatic();
      toggle.setAttribute('aria-pressed', String(userPaused));
      toggle.setAttribute('aria-label', userPaused ? '播放机器人概念动画' : '暂停机器人概念动画');
      icon.textContent = userPaused ? '▷' : 'Ⅱ';
      label.textContent = userPaused ? '播放动画' : '暂停动画';
      root.dataset.static = String(isStatic());
      root.dataset.paused = String(!canRun());
    }
    function draw(seconds, staticPose = false) {
      const t = staticPose ? 7.6 : seconds % 14;
      let dx = 0, gait = null, reach = 0, phase = 'approach';
      if (t < 3) { dx = mix(-36, 0, ease(t / 3)); gait = {p: t / 3, start: -36, delta: 36, reverse: false}; }
      else if (t < 5) { phase = 'recognize'; }
      else if (t < 7) { reach = ease((t - 5) / 2); phase = 'reach'; }
      else if (t < 8) { reach = 1; phase = 'reach'; }
      else if (t < 10) { reach = 1 - ease((t - 8) / 2); phase = 'reach'; }
      else if (t < 13) { dx = mix(0, -36, ease((t - 10) / 3)); gait = {p: (t - 10) / 3, start: 0, delta: -36, reverse: true}; }
      else { dx = -36; }
      root.dataset.phase = phase;
      robot.setAttribute('transform', `translate(${dx.toFixed(3)} 0)`);
      shadow.setAttribute('transform', `translate(${dx.toFixed(3)} 0)`);
      for (const leg of legs) {
        const foot = [...leg.rest];
        if (gait) {
          const offset = gait.reverse ? .75 - leg.offset : leg.offset;
          const p = clamp((gait.p - offset) / .25);
          // One foot swings at a time; the other three feet remain planted in world space.
          foot[0] += gait.start + gait.delta * ease(p) - dx;
          foot[1] -= Math.sin(Math.PI * p) * 8;
        }
        const knee = polarIK(leg.hip, foot, leg.upper, leg.lower);
        line(leg.bones.upper, leg.hip, knee); line(leg.bones['upper-inset'], leg.hip, knee);
        line(leg.bones.lower, knee, foot); line(leg.bones['lower-inset'], knee, foot);
        point(leg.knee, knee); point(leg.core, knee);
        leg.foot.setAttribute('d', `M ${(foot[0] - 7).toFixed(3)} ${(foot[1] + 1).toFixed(3)} l 14 -2`);
      }
      const shoulder = [346, 193], wrist = [mix(407, 507, reach), mix(174, 245, reach)];
      const elbow = polarIK(shoulder, wrist, 91, 105);
      line(arm.upper, shoulder, elbow); line(arm['upper-inset'], shoulder, elbow);
      line(arm.lower, elbow, wrist); line(arm['lower-inset'], elbow, wrist);
      point(arm.elbow, elbow); point(arm['elbow-core'], elbow);
      grip.setAttribute('transform', `translate(${wrist[0].toFixed(3)} ${wrist[1].toFixed(3)}) rotate(34)`);
      const pinch = t >= 7 && t < 8 ? Math.sin((t - 7) * Math.PI) : 0;
      const gap = 8 - 3 * pinch, tip = 4 - 2 * pinch;
      topFinger.setAttribute('d', `M 8 -5 L 23 ${-gap} L 30 ${-tip}`);
      bottomFinger.setAttribute('d', `M 8 5 L 23 ${gap} L 30 ${tip}`);
      const acquisition = t >= 3 && t < 5 ? Math.sin(((t - 3) / 2) * Math.PI) : 0;
      recognition.setAttribute('opacity', staticPose ? '.12' : String(.04 + .85 * acquisition));
      lock.setAttribute('opacity', staticPose ? '.7' : String(t >= 3 && t < 10 ? .5 + .35 * acquisition : .16));
    }
    function tick(now) {
      frame = 0;
      if (!root.isConnected) { destroy(); return; }
      if (!canRun()) { previous = null; return; }
      if (previous !== null) elapsed += Math.min((now - previous) / 1000, .1);
      previous = now; draw(elapsed);
      frame = requestAnimationFrame(tick);
    }
    function reconcile() {
      if (frame) cancelAnimationFrame(frame); frame = 0; previous = null;
      controls();
      if (isStatic()) draw(0, true);
      else if (canRun()) { draw(elapsed); frame = requestAnimationFrame(tick); }
    }
    function onToggle() { userPaused = !userPaused; reconcile(); }
    toggle.addEventListener('click', onToggle);
    document.addEventListener('visibilitychange', reconcile);
    reduced.addEventListener('change', reconcile); compact.addEventListener('change', reconcile);
    const observer = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
      inView = entries[0].isIntersecting; reconcile();
    }, {threshold: 0}) : null;
    if (observer) observer.observe(root);
    function destroy() {
      disposed = true;
      if (frame) cancelAnimationFrame(frame);
      observer?.disconnect();
      document.removeEventListener('visibilitychange', reconcile);
      reduced.removeEventListener('change', reconcile); compact.removeEventListener('change', reconcile);
      toggle.removeEventListener('click', onToggle); toggle.remove();
      delete root.dataset.robotInitialized;
    }
    // Optional lifecycle hook for a client-side router. Initialization is idempotent.
    root.robotVignetteDestroy = destroy;
    draw(0, true); reconcile();
  }
  window.RoboPaperAtlasRobot = {init(scope = document) {
    if (scope.matches?.('.robot-vignette')) initialize(scope);
    scope.querySelectorAll('.robot-vignette').forEach(initialize);
  }};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => window.RoboPaperAtlasRobot.init(), {once: true});
  else window.RoboPaperAtlasRobot.init();
})();
