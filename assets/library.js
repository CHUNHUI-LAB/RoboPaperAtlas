'use strict';
// Progressive enhancement stays scoped to the Library landing page.
(() => {
  if (!document.querySelector('.library-main')) return;
  const disclosure = document.querySelector('.filter-disclosure');
  const summary = disclosure.querySelector('summary');
  const panel = disclosure.querySelector('.filter-panel');
  const filterDialog = document.createElement('dialog');
  filterDialog.id = 'catalog-filter-dialog';
  filterDialog.className = 'library-filter-dialog';
  filterDialog.setAttribute('aria-labelledby', 'catalog-filter-title');
  filterDialog.append(panel);
  document.body.append(filterDialog);
  summary.setAttribute('aria-haspopup', 'dialog');
  summary.setAttribute('aria-controls', filterDialog.id);
  summary.setAttribute('aria-expanded', 'false');
  summary.addEventListener('click', event => {
    event.preventDefault();
    if (filterDialog.open) return;
    filterDialog.showModal();
    summary.setAttribute('aria-expanded', 'true');
    panel.querySelector('[data-filter-close]').focus();
  });
  const close = () => { if (filterDialog.open) filterDialog.close(); };
  panel.querySelectorAll('[data-filter-close]').forEach(button => button.addEventListener('click', close));
  filterDialog.addEventListener('close', () => {
    if (filterDialog.open) return;
    disclosure.open = false;
    summary.setAttribute('aria-expanded', 'false');
    summary.focus({preventScroll: true});
  });
  filterDialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
  filterDialog.addEventListener('click', event => {
    if (event.target !== filterDialog) return;
    const rect = filterDialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) close();
  });
  document.querySelectorAll('[data-catalog-jump]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    const input = document.querySelector('#search');
    input.focus({preventScroll: true});
    document.querySelector('#catalog').scrollIntoView({block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
  }));
})();
