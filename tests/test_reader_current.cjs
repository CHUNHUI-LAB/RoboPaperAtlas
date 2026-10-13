'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { JSDOM } = require('jsdom');
const runtime = fs.readFileSync(__dirname + '/../assets/reader-current.js', 'utf8');

function setup() {
  const dom = new JSDOM('<body class="atlas-current-reader"><header class="site-header"></header><main class="reader-page"><div class="reader-stagebar"></div><article class="reader-article"><figure id="plain"><img src="data:image/png;base64,abc" alt="方法框架"><figcaption>Fig. 1 · 正式论文第 2 页</figcaption></figure><figure id="native"><input class="figure-zoom" type="checkbox"><img src="data:image/png;base64,def" alt="原尺寸图"></figure><figure id="diagram"><svg viewBox="0 0 800 400" aria-labelledby="flow-title"><title id="flow-title">数据流</title><defs><marker id="arrow"></marker></defs><path marker-end="url(#arrow)"></path></svg><figcaption>整理者示意图</figcaption></figure></article></main></body>', { runScripts: 'outside-only', pretendToBeVisual: true });
  const { window } = dom;
  window.HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  window.HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new window.Event('close')); };
  window.document.querySelector('.site-header').getBoundingClientRect = () => ({ height: 64 });
  window.document.querySelector('.reader-stagebar').getBoundingClientRect = () => ({ height: 100 });
  window.eval(runtime);
  return dom;
}

test('expanding a figure preserves its source and restores the reading focus on close', () => {
  const dom = setup(), { document, Event } = dom.window;
  const button = document.querySelector('#plain .reader-figure-open');
  button.focus(); button.click();
  const dialog = document.querySelector('.reader-figure-dialog');
  assert(dialog.open);
  assert.equal(document.activeElement, dialog.querySelector('[data-figure-close]'));
  assert.equal(dialog.querySelector('img').getAttribute('src'), document.querySelector('#plain img').getAttribute('src'));
  assert.equal(dialog.querySelector('.reader-figure-caption').textContent, 'Fig. 1 · 正式论文第 2 页');
  const size = dialog.querySelector('[data-figure-size]'); size.click();
  assert.equal(size.getAttribute('aria-pressed'), 'true');
  assert(dialog.querySelector('.reader-figure-viewport').classList.contains('is-natural'));
  dialog.dispatchEvent(new Event('cancel', { cancelable: true }));
  assert.equal(dialog.open, false);
  assert.equal(document.activeElement, button);
  assert(document.querySelector('#plain img'));
  assert.equal(document.querySelector('#native .reader-figure-open'), null, 'existing original-size controls are retained');
  dom.window.close();
});

test('SVG expansion preserves diagram references without duplicating fixed figure IDs', () => {
  const dom = setup(), { document } = dom.window;
  document.querySelector('#diagram .reader-figure-open').click();
  const clone = document.querySelector('.reader-figure-viewport svg');
  assert.equal(clone.getAttribute('aria-labelledby'), 'reader-zoom-flow-title');
  assert.equal(clone.querySelector('path').getAttribute('marker-end'), 'url(#reader-zoom-arrow)');
  assert.equal(document.querySelectorAll('#arrow').length, 1);
  assert.equal(document.querySelectorAll('#reader-zoom-arrow').length, 1);
  assert.equal(document.documentElement.style.getPropertyValue('--reader-anchor-offset'), '180px');
  dom.window.close();
});

test('without native dialogs the report remains readable without inert expansion buttons', () => {
  const dom = new JSDOM('<body class="atlas-current-reader"><main class="reader-page"><article class="reader-article"><figure><img alt="A"></figure></article></main></body>', { runScripts: 'outside-only' });
  dom.window.eval(runtime);
  assert.equal(dom.window.document.querySelector('.reader-figure-open'), null);
  assert(dom.window.document.querySelector('figure img'));
  dom.window.close();
});
