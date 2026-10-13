/* Shared navigation enhancement, including readers with preserved inline scripts. */
(() => {
  'use strict';
  const header = document.querySelector('.site-header');
  if (!header || header.dataset.chromeReady) return;
  header.dataset.chromeReady = 'true';
  const groups = [...header.querySelectorAll('details.nav-group')];
  for (const group of groups) {
    group.addEventListener('toggle', () => {
      if (group.open) groups.filter(other => other !== group).forEach(other => { other.open = false; });
    });
  }
  document.addEventListener('click', event => {
    for (const group of groups) if (!group.contains(event.target) || event.target.closest('a')) group.open = false;
  });
  header.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const open = groups.find(group => group.open);
    if (open) {
      event.preventDefault(); event.stopPropagation(); open.open = false;
      open.querySelector('summary').focus({preventScroll: true});
    }
  }, true);
  // Current immutable readers retain their reviewed search implementation.
  // Retrying through its public trigger avoids installing a second search handler.
  const status = document.querySelector('#global-search-status');
  const retry = document.querySelector('#global-search-retry');
  if (status && retry) {
    let failed = false;
    const sync = () => {
      const message = status.textContent;
      if (/无法载入|载入失败/.test(message)) failed = true;
      else if (/找到 \d+ 篇|没有匹配论文|试试 HarnessVLN/.test(message)) failed = false;
      retry.hidden = !failed;
      // Old fixed-reader search scripts replace a failure with a loading label
      // on input, although they do not start another request. Retain the failure.
      if (failed && message === '正在载入目录…') status.textContent = '搜索索引暂时无法载入，请重试或进入完整目录';
    };
    document.querySelectorAll('.global-search-trigger').forEach(trigger => trigger.addEventListener('click', () => { failed = false; retry.hidden = true; }, true));
    new MutationObserver(sync).observe(status, {childList: true, subtree: true, characterData: true});
    retry.addEventListener('click', () => document.querySelector('.global-search-trigger')?.click());
    sync();
  }
  // Keep the primary destination in view, also for immutable reader scripts
  // which still append it to the drawer body.
  const drawerBody = document.querySelector('#drawer-body');
  const drawerFooter = document.querySelector('#drawer-footer');
  if (drawerBody && drawerFooter) {
    const syncAction = () => {
      const action = drawerBody.querySelector(':scope > .primary-link');
      if (action) { drawerFooter.replaceChildren(action); drawerFooter.hidden = false; }
      else if (drawerBody.children.length <= 1) { drawerFooter.replaceChildren(); drawerFooter.hidden = true; }
    };
    new MutationObserver(syncAction).observe(drawerBody, {childList: true});
    syncAction();
  }
  if ('ResizeObserver' in window) {
    new ResizeObserver(() => {
      document.documentElement.style.setProperty('--site-header-offset', `${Math.ceil(header.getBoundingClientRect().height)}px`);
    }).observe(header);
  }
})();
