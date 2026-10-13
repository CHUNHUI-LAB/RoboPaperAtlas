'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const { JSDOM, VirtualConsole } = require('jsdom');
const root = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root, 'assets', name), 'utf8');
const chrome = read('chrome.js');
const currentInterface = read('interface.js');
// Exercise the actual preserved runtime that a current UMI reader still runs.
const fixedReport = fs.readFileSync(path.join(root, 'artifacts/rpa-0062/v3/first-pass.html'), 'utf8');
const legacyInterface = fixedReport.match(/<script data-report-script="interface\.js">([\s\S]*?)<\/script>/)[1];
const shell = cp.execFileSync('python3', ['-c', [
  'import json, sys',
  'sys.path.insert(0, "scripts")',
  'from site_chrome import render_header, render_dialogs',
  'print(json.dumps({"header": render_header("../../../", page="reading", compact=True), "dialogs": render_dialogs("../../../")}))',
].join('\n')], { cwd: root, encoding: 'utf8' });
const markup = JSON.parse(shell);
const paper = JSON.parse(fs.readFileSync(path.join(root, 'data/catalog.json'), 'utf8')).papers.find(p => p.id === 'rpa-0062');
const searchIndex = [{ id: paper.id, title: paper.title, authors: Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors, category: paper.category, text: paper.title.toLowerCase() }];
const flush = () => new Promise(resolve => setImmediate(resolve));

function setup(t, runtime = currentInterface) {
  const errors = [], measurements = [], requests = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM('<!doctype html><body data-root="../../../">' + markup.header + '<main id="main"></main>' + markup.dialogs + '</body>', {
    url: 'https://example.org/RoboPaperAtlas/papers/rpa-0062/reading/stage1.html',
    runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole,
  });
  t.after(() => { assert.deepEqual(errors, [], 'the shared scripts must not throw'); dom.window.close(); });
  const w = dom.window, d = w.document;
  w.matchMedia = () => ({ matches: true });
  // JSDOM does not implement native dialog presentation or layout measurement.
  w.HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
  w.HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); this.dispatchEvent(new w.Event('close')); };
  w.ResizeObserver = class {
    constructor(callback) { this.callback = callback; }
    observe(target) { measurements.push(() => this.callback([{ target }])); }
  };
  w.fetch = url => new Promise((resolve, reject) => requests.push({ url, resolve, reject }));
  w.eval(read('catalog-navigation.js'));
  w.eval(runtime);
  w.eval(chrome);
  return { w, d, measurements, requests };
}

for (const [name, runtime] of [['current interface', currentInterface], ['immutable UMI inline interface', legacyInterface]]) {
  test(name + ': failed search stays recoverable while editing and retries to real results', async t => {
    const { w, d, requests } = setup(t, runtime);
    const trigger = d.querySelector('.global-search-trigger');
    const dialog = d.querySelector('#search-dialog');
    const input = d.querySelector('#global-search-input');
    const status = d.querySelector('#global-search-status');
    const retry = d.querySelector('#global-search-retry');
    trigger.focus(); trigger.click();
    assert.equal(dialog.open, true);
    assert.equal(requests.length, 1);
    assert.equal(new URL(requests[0].url, w.location.href).pathname, '/RoboPaperAtlas/data/search-index.json');
    requests[0].reject(new Error('temporary offline'));
    await flush();
    assert.match(status.textContent, /无法载入/);
    assert.equal(retry.hidden, false);

    input.value = 'UMI'; input.dispatchEvent(new w.Event('input', { bubbles: true }));
    await flush();
    assert.equal(requests.length, 1, 'editing a failed query must not masquerade as another fetch');
    assert.match(status.textContent, /无法载入/);
    assert.equal(retry.hidden, false, 'retry remains reachable after the original failure');
    assert.equal(new URL(d.querySelector('#global-all-results').href).searchParams.get('q'), 'UMI');

    retry.click();
    await flush();
    assert.equal(requests.length, 2);
    assert.equal(retry.hidden, true);
    assert.match(status.textContent, /正在载入/);
    requests[1].resolve({ ok: true, json: async () => searchIndex });
    await flush();
    assert.match(status.textContent, /找到 1 篇论文/);
    assert.equal(retry.hidden, true);
    const result = d.querySelector('#global-search-results a');
    assert.equal(result.querySelector('strong').textContent, paper.title);
    assert.equal(new URL(result.href).pathname, '/RoboPaperAtlas/papers/rpa-0062/index.html');
    input.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true, cancelable: true }));
    assert.equal(d.activeElement, result);
    result.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
    assert.equal(dialog.open, false);
  });

  test(name + ': Escape closes the current navigation disclosure before the mobile menu', async t => {
    const { w, d } = setup(t, runtime);
    const menu = d.querySelector('.mobile-menu'), nav = d.querySelector('#main-nav');
    const groups = [...d.querySelectorAll('details.nav-group')];
    menu.click();
    assert.equal(menu.getAttribute('aria-expanded'), 'true');
    groups[1].open = true; groups[1].dispatchEvent(new w.Event('toggle'));
    groups[0].open = true; groups[0].dispatchEvent(new w.Event('toggle'));
    assert.equal(groups[1].open, false, 'only one navigation disclosure remains open');
    const link = groups[0].querySelector('a'); link.focus();
    const escape = new w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true });
    link.dispatchEvent(escape);
    assert.equal(escape.defaultPrevented, true);
    assert.equal(groups[0].open, false);
    assert.equal(d.activeElement, groups[0].querySelector('summary'));
    assert.equal(nav.classList.contains('open'), true);
    assert.equal(menu.getAttribute('aria-expanded'), 'true');
    d.activeElement.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
    assert.equal(nav.classList.contains('open'), false);
    assert.equal(menu.getAttribute('aria-expanded'), 'false');
    assert.equal(d.activeElement, menu);
    await flush();
  });
}

test('header measurement updates anchor offset without feeding back into the layout height', t => {
  const { w, d, measurements } = setup(t);
  const header = d.querySelector('.site-header'), styles = d.documentElement.style;
  // The normal header is its configured inner height plus its border.
  styles.setProperty('--site-header-height', '76px');
  header.getBoundingClientRect = () => ({ height: parseFloat(styles.getPropertyValue('--site-header-height')) + 1 });
  assert.equal(measurements.length, 1);
  for (let i = 0; i < 5; i++) measurements[0]();
  assert.equal(styles.getPropertyValue('--site-header-height'), '76px');
  assert.equal(styles.getPropertyValue('--site-header-offset'), '77px');
  header.getBoundingClientRect = () => ({ height: 184.25 });
  measurements[0]();
  assert.equal(styles.getPropertyValue('--site-header-offset'), '185px', 'expanded mobile navigation has an independent offset');
  assert.equal(styles.getPropertyValue('--site-header-height'), '76px');
  w.eval(chrome);
  assert.equal(measurements.length, 1, 're-evaluating chrome must not register another observer');
});
