/* Progressive enhancement only: content, sources, and navigation are static. */
(function () {
  'use strict';
  function revealHash() {
    var id;
    try { id = decodeURIComponent(window.location.hash.slice(1)); } catch (_) { return; }
    if (!id) return;
    var target = document.getElementById(id);
    if (!target) return;
    var parent = target.parentElement;
    while (parent) {
      if (parent.tagName === 'DETAILS') parent.open = true;
      parent = parent.parentElement;
    }
    if (target.tagName === 'DETAILS') target.open = true;
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({preventScroll: true});
    target.scrollIntoView({block: 'start', behavior: 'auto'});
  }
  window.addEventListener('hashchange', revealHash);
  window.addEventListener('pageshow', function (event) {
    if (!event.persisted) revealHash();
  });
  document.addEventListener('click', function (event) {
    var anchor = event.target.closest && event.target.closest('a[href^="#"]');
    if (anchor && anchor.getAttribute('href') === window.location.hash) revealHash();
  });
  revealHash();
}());
