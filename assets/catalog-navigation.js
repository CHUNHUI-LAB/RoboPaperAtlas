/* Retain bounded catalogue state, never a caller-provided return destination. */
(function (scope) {
  'use strict';
  const KEYS = ['q', 'topic', 'direction', 'method', 'resource', 'year', 'status', 'sort', 'view'];
  function cleanQuery(value) {
    if (typeof value !== 'string' || value.length > 4096) return '';
    const source = new URLSearchParams(value), result = new URLSearchParams();
    for (const key of KEYS) {
      const value = source.get(key)?.trim();
      if (!value || value.length > (key === 'q' ? 512 : 64) || /[\u0000-\u001f\u007f]/.test(value)) continue;
      if (key !== 'q' && !/^[\w -]+$/.test(value)) continue;
      if (key === 'sort' && !['curated', 'newest', 'title'].includes(value)) continue;
      if (key === 'view' && !['cards', 'list'].includes(value)) continue;
      result.set(key, value);
    }
    return result.toString();
  }
  function paperHref(href, query) {
    // Deliberately accept only generated relative detail paths, not arbitrary URLs.
    const match = /^(?:\.\.\/)*papers\/[a-z0-9-]+\/index\.html(?:\?[^#]*)?(#[\w-]+)?$/.exec(href);
    if (!match) return href;
    const clean = cleanQuery(query), base = href.split(/[?#]/)[0];
    return base + (clean ? '?catalog=' + encodeURIComponent(clean) : '') + (match[1] || '');
  }
  function backHref(prefix, search) {
    const clean = cleanQuery(new URLSearchParams(search).get('catalog') || '');
    return prefix + 'index.html' + (clean ? '?' + clean : '') + '#catalog';
  }
  const api = { cleanQuery, paperHref, backHref };
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }
  scope.RoboCatalogNavigation = api;
  const back = document.querySelector('[data-catalog-back]');
  if (back) back.setAttribute('href', backHref(document.body.dataset.root || '', window.location.search));
  function updateLinks() {
    const grid = document.querySelector('#paper-grid');
    if (!grid) return;
    grid.querySelectorAll('a').forEach(a => a.setAttribute('href', paperHref(a.getAttribute('href') || '', window.location.search)));
  }
  document.addEventListener('catalog:updated', updateLinks);
  updateLinks();
})(globalThis);
