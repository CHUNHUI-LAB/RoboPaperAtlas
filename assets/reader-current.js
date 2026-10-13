/* Progressive controls for current readers; historical report bytes are untouched. */
(() => {
  'use strict';
  const page = document.querySelector('.atlas-current-reader .reader-page');
  if (!page) return;
  const header = document.querySelector('.site-header'), stagebar = page.querySelector('.reader-stagebar');
  function syncChrome() {
    if (!header || !stagebar) return;
    const headerHeight = header.getBoundingClientRect().height;
    const barHeight = stagebar.getBoundingClientRect().height;
    if (!(headerHeight > 0 && barHeight > 0)) return;
    document.documentElement.style.setProperty('--atlas-header-height', `${headerHeight}px`);
    document.documentElement.style.setProperty('--reader-chrome-bottom', `${headerHeight + barHeight}px`);
    document.documentElement.style.setProperty('--reader-anchor-offset', `${headerHeight + barHeight + 16}px`);
  }
  syncChrome();
  window.addEventListener('resize', syncChrome);
  window.addEventListener('pageshow', syncChrome);
  if (typeof ResizeObserver === 'function' && header && stagebar) {
    const observer = new ResizeObserver(syncChrome);
    observer.observe(header);
    observer.observe(stagebar);
  }

  if (typeof HTMLDialogElement === 'undefined' || !HTMLDialogElement.prototype.showModal) return;
  const figures = [...page.querySelectorAll('.reader-article figure')]
    .filter(figure => !figure.querySelector('.figure-zoom') && figure.querySelector('img, svg'));
  if (!figures.length) return;
  const dialog = document.createElement('dialog');
  dialog.className = 'reader-figure-dialog';
  dialog.setAttribute('aria-labelledby', 'reader-figure-title');
  dialog.innerHTML = '<div class="reader-figure-toolbar"><h2 id="reader-figure-title">图表预览</h2><div><button type="button" class="reader-control" data-figure-size aria-pressed="false">查看原尺寸</button><button type="button" class="reader-control" data-figure-close aria-label="关闭图表预览">关闭 <span aria-hidden="true">×</span></button></div></div><div class="reader-figure-viewport" tabindex="0" role="region" aria-label="图表，可滚动查看"></div><p class="reader-figure-caption"></p>';
  document.body.append(dialog);
  const viewport = dialog.querySelector('.reader-figure-viewport');
  const caption = dialog.querySelector('.reader-figure-caption');
  const close = dialog.querySelector('[data-figure-close]');
  const size = dialog.querySelector('[data-figure-size]');
  let opener = null;
  const dismiss = () => dialog.close();
  close.addEventListener('click', dismiss);
  dialog.addEventListener('cancel', event => { event.preventDefault(); dismiss(); });
  dialog.addEventListener('close', () => {
    viewport.replaceChildren();
    opener?.focus({ preventScroll: true });
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dismiss();
  });
  size.addEventListener('click', () => {
    const natural = viewport.classList.toggle('is-natural');
    size.setAttribute('aria-pressed', String(natural));
    size.textContent = natural ? '适应窗口' : '查看原尺寸';
  });
  function cloneGraphic(source) {
    const clone = source.cloneNode(true);
    clone.removeAttribute('id');
    clone.removeAttribute('loading');
    // Keep SVG markers, title and description local to the expanded copy.
    const ids = new Map();
    clone.querySelectorAll('[id]').forEach(element => {
      const id = element.id;
      ids.set(id, 'reader-zoom-' + id);
      element.id = ids.get(id);
    });
    for (const element of [clone, ...clone.querySelectorAll('*')]) {
      for (const attribute of [...element.attributes]) {
        let value = attribute.value;
        for (const [id, replacement] of ids) {
          value = value.replaceAll(`url(#${id})`, `url(#${replacement})`);
          if (value === '#' + id) value = '#' + replacement;
          if (['aria-labelledby', 'aria-describedby'].includes(attribute.name)) value = value.split(' ').map(token => token === id ? replacement : token).join(' ');
        }
        if (value !== attribute.value) element.setAttribute(attribute.name, value);
      }
    }
    return clone;
  }
  for (const figure of figures) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'reader-figure-open';
    button.textContent = '展开图表 ↗';
    button.setAttribute('aria-haspopup', 'dialog');
    figure.append(button);
    button.addEventListener('click', () => {
      opener = button;
      viewport.classList.remove('is-natural');
      size.setAttribute('aria-pressed', 'false');
      size.textContent = '查看原尺寸';
      viewport.replaceChildren(cloneGraphic(figure.querySelector('img, svg')));
      caption.textContent = figure.querySelector('figcaption')?.textContent || '';
      dialog.showModal();
      close.focus({ preventScroll: true });
    });
  }
})();
