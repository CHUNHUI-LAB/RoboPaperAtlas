/* Static artwork with bounded topic focus. No animation loop, sensors, or network. */
(() => {
  'use strict';
  const root = document.querySelector('.library-main');
  if (!root) return;
  const controls = [...root.querySelectorAll('.topic-filter')];
  const status = root.querySelector('[data-galaxy-status]');
  const regions = {'navigation-space':['68%','27%'], 'motion-manipulation':['82%','37%'], 'robot-learning':['72%','45%'], 'methods-resources':['88%','21%']};
  const overview = '按研究问题探索 · 星系为抽象视觉，不表示论文引用关系';
  let hovered = null;
  function show(button) {
    const topic = button?.dataset.topic || 'all';
    root.dataset.galaxyTopic = topic;
    const point = regions[topic] || ['76%','32%'];
    root.style.setProperty('--focus-x', point[0]);
    root.style.setProperty('--focus-y', point[1]);
    status.textContent = topic === 'all' ? overview : `${button.querySelector('span').textContent} · ${button.querySelector('b').textContent} 篇相关书目，点击筛选 · 抽象星域`;
  }
  for (const button of controls) {
    button.addEventListener('pointerenter', () => { hovered = button; show(button); });
    button.addEventListener('pointerleave', () => { hovered = null; show(controls.includes(document.activeElement) ? document.activeElement : null); });
    button.addEventListener('focus', () => show(button));
    button.addEventListener('blur', () => show(hovered));
    button.addEventListener('keydown', event => { if (event.key === 'Escape') { hovered = null; show(null); } });
  }
  root.querySelector('.library-search')?.addEventListener('submit', () => {
    root.querySelector('#catalog-results')?.scrollIntoView({block:'start', behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
  });
  show(null);
})();
