'use strict';
/*
 * Controller regression harness. No browser, DOM/layout engine, server, network,
 * or third-party dependency is used. It executes the unmodified preview.js in a
 * Node VM with explicit DOM and asynchronous History API test doubles.
 *
 * Run here: node test_library_preview_controller.cjs /path/to/repository
 * Once copied to repository/tests/, the repository argument is optional.
 * Passing these tests does NOT establish native focus trapping, real browser
 * history scheduling, keyboard-to-cancel dispatch, layout, or accessibility.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(process.argv[2] || path.join(__dirname, '..'));
const source = fs.readFileSync(path.join(root, 'previews/library-topic-preview/preview.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'previews/library-topic-preview/topics.json'), 'utf8'));

async function controller(initialSearch = '', initialScroll = 0, sourceOverride = source) {
  const elements = new Map(), classes = new Set(), documentEvents = {}, windowEvents = {};
  const calls = {back: 0, forward: 0, push: 0, replace: 0, scroll: []};
  let activeElement = null;
  function element(id) {
    if (elements.has(id)) return elements.get(id);
    const e = {
      id, hidden: false, open: false, value: '', checked: false, disabled: false,
      children: [], dataset: {}, attrs: {}, listeners: {}, innerHTML: '',
      textContent: '', tagName: 'DIV', isContentEditable: false,
      setAttribute(k, v) { this.attrs[k] = String(v); },
      getAttribute(k) { return this.attrs[k]; },
      addEventListener(k, f) { this.listeners[k] = f; },
      focus() { activeElement = this; }, select() { this.selected = true; },
      showModal() { this.open = true; }, close() { this.open = false; },
      scrollIntoView() { this.scrolledIntoView = true; },
      querySelectorAll(selector) {
        if (this.id === 'library' && selector === '[data-open]') {
          return ['results', 'weak-results', 'uncertain-results'].flatMap(container =>
            [...element(container).innerHTML.matchAll(/data-open="([^"]+)"/g)].map((m, i) => {
              const button = element(container + ':' + m[1] + ':' + i);
              button.dataset.open = m[1]; button.tagName = 'BUTTON'; return button;
            }));
        }
        if (this.id === 'filter-groups' && selector === 'input[type=checkbox]') {
          return [...this.innerHTML.matchAll(/type="checkbox" data-dimension="([^"]+)" value="([^"]+)"/g)].map(m => {
            const input = element('facet:' + m[1] + ':' + m[2]);
            input.dataset.dimension = m[1]; input.value = m[2]; input.tagName = 'INPUT'; return input;
          });
        }
        return [];
      }
    };
    elements.set(id, e); return e;
  }
  element('q').tagName = 'INPUT';
  element('more-filters').setAttribute('aria-expanded', 'false');
  element('filter-panel').hidden = true;
  const location = {pathname: '/library-topic-preview/', search: initialSearch};
  const stack = [{url: location.pathname + initialSearch, state: null}], pending = [];
  let position = 0;
  function setLocation(url) {
    const parsed = new URL(url, 'https://preview.invalid');
    location.pathname = parsed.pathname; location.search = parsed.search;
  }
  const history = {
    get state() { return stack[position].state; },
    replaceState(state, unused, url) {
      calls.replace++; stack[position] = {state, url}; setLocation(url);
    },
    pushState(state, unused, url) {
      calls.push++; stack.splice(position + 1); stack.push({state, url}); position++; setLocation(url);
    },
    back() { calls.back++; pending.push(-1); },
    forward() { calls.forward++; pending.push(1); }
  };
  const window = {
    scrollY: initialScroll,
    scrollTo(options) { calls.scroll.push(options); this.scrollY = options.top; },
    addEventListener(k, f) { windowEvents[k] = f; }
  };
  const context = {
    console, URL, URLSearchParams, location, history, window, module: {exports: {}},
    fetch: url => {
      assert.equal(url, 'topics.json');
      return Promise.resolve({ok: true, json: () => Promise.resolve(data)});
    },
    document: {
      getElementById: element,
      body: {classList: {add: c => classes.add(c), remove: c => classes.delete(c)}},
      addEventListener(k, f) { documentEvents[k] = f; }
    }
  };
  vm.createContext(context);
  vm.runInContext(sourceOverride, context, {filename: 'preview.js'});
  await new Promise(resolve => setImmediate(resolve));
  assert.notEqual(element('count').textContent, '论文暂时未能载入', 'controller startup failed');
  assert.equal(typeof element('close-detail').listeners.click, 'function');
  function event(extra = {}) {
    return {defaultPrevented: false, preventDefault() { this.defaultPrevented = true; }, ...extra};
  }
  return {
    element, calls, history, location, window, classes,
    get activeElement() { return activeElement; },
    get pendingTraversals() { return pending.length; },
    open(id) {
      const button = {dataset: {open: id}};
      element('library').listeners.click(event({target: {closest: selector => selector === '[data-open]' ? button : null}}));
    },
    close() { element('close-detail').listeners.click(event()); },
    cancel() { const e = event(); element('paper-dialog').listeners.cancel(e); return e; },
    key(key, target = {tagName: 'BODY', isContentEditable: false}, modifiers = {}) {
      const e = event({key, target, ctrlKey: false, metaKey: false, ...modifiers});
      documentEvents.keydown(e); return e;
    },
    flushTraversal() {
      assert(pending.length, 'no traversal queued');
      const target = position + pending.shift();
      assert(target >= 0 && target < stack.length, 'unexpected navigation beyond preview history');
      position = target; setLocation(stack[position].url); windowEvents.popstate(event());
    }
  };
}

(async () => {
  let checks = 0;
  async function test(name, fn) { await fn(); checks++; console.log('PASS:', name); }
  await test('repeated Close and cancel consume one pending traversal; restore query, facets, focus and scroll', async () => {
    const search = '?q=%E7%A7%BB%E5%8A%A8%E6%93%8D%E4%BD%9C&method=rl&platform=quadruped';
    const c = await controller(search, 531);
    c.open('rpa-0062');
    assert(c.element('paper-dialog').open); assert(c.classes.has('detail-open'));
    assert.equal(c.activeElement.id, 'detail-title'); assert.equal(c.calls.push, 1);
    c.close(); c.close(); assert(c.cancel().defaultPrevented); c.cancel();
    assert.equal(c.calls.back, 1); assert.equal(c.pendingTraversals, 1);
    assert(c.element('paper-dialog').open, 'dialog remains until asynchronous traversal');
    c.flushTraversal();
    assert(!c.element('paper-dialog').open); assert(!c.classes.has('detail-open'));
    assert.equal(c.element('q').value, '移动操作');
    assert.equal(new URLSearchParams(c.location.search).get('method'), 'rl');
    assert.equal(new URLSearchParams(c.location.search).get('platform'), 'quadruped');
    assert(!new URLSearchParams(c.location.search).has('paper'));
    assert.equal(c.activeElement.dataset.open, 'rpa-0062'); assert.equal(c.window.scrollY, 531);
    c.close(); c.cancel(); assert.equal(c.calls.back, 1, 'closed dialog ignores stale requests');
  });
  await test('cancel-first repetition is idempotent and guard clears after close/reopen', async () => {
    const c = await controller(); c.open('rpa-0062');
    assert(c.cancel().defaultPrevented); c.cancel(); c.close();
    assert.equal(c.calls.back, 1); c.flushTraversal();
    c.open('rpa-0016'); c.close(); c.close();
    assert.equal(c.calls.back, 2); c.flushTraversal(); assert(!c.element('paper-dialog').open);
  });
  await test('Back then Forward restores detail; subsequent Close still works', async () => {
    const c = await controller('?q=FAST', 200); c.open('rpa-0016');
    c.history.back(); c.flushTraversal(); assert(!c.element('paper-dialog').open);
    c.history.forward(); c.flushTraversal(); assert(c.element('paper-dialog').open);
    assert.equal(new URLSearchParams(c.location.search).get('paper'), 'rpa-0016');
    assert.equal(c.element('q').value, 'FAST'); assert.equal(c.activeElement.id, 'detail-title');
    c.close(); c.cancel(); assert.equal(c.calls.back, 2); c.flushTraversal();
    assert(!c.element('paper-dialog').open); assert.equal(c.window.scrollY, 200);
  });
  await test('direct detail link closes by replacement without leaving preview', async () => {
    const c = await controller('?q=FAST&paper=rpa-0016');
    assert(c.element('paper-dialog').open); c.close(); c.close(); c.cancel();
    assert.equal(c.calls.back, 0); assert.equal(c.calls.replace, 1);
    assert.equal(new URLSearchParams(c.location.search).get('q'), 'FAST');
    assert(!new URLSearchParams(c.location.search).has('paper')); assert(!c.element('paper-dialog').open);
  });
  await test('expanded weak-result section survives detail return', async () => {
    const c = await controller('?q=%E7%A7%BB%E5%8A%A8%E6%93%8D%E4%BD%9C');
    assert(!c.element('weak-section').hidden); c.element('weak-section').open = true;
    c.open('rpa-0016'); c.close(); c.flushTraversal();
    assert(c.element('weak-section').open); assert.equal(c.activeElement.dataset.open, 'rpa-0016');
    assert(c.activeElement.id.startsWith('weak-results:'));
  });
  await test('search shortcuts respect editing and modal state; Escape dismisses filters', async () => {
    const c = await controller();
    assert(c.key('/').defaultPrevented); assert.equal(c.activeElement.id, 'q');
    c.element('more-filters').focus();
    assert(!c.key('/', {tagName: 'INPUT', isContentEditable: false}).defaultPrevented);
    assert.equal(c.activeElement.id, 'more-filters');
    assert(c.key('k', {tagName: 'INPUT'}, {ctrlKey: true}).defaultPrevented);
    assert.equal(c.activeElement.id, 'q');
    c.element('more-filters').listeners.click(); assert(!c.element('filter-panel').hidden);
    c.key('Escape'); assert(c.element('filter-panel').hidden);
    assert.equal(c.element('more-filters').getAttribute('aria-expanded'), 'false');
    assert.equal(c.activeElement.id, 'more-filters');
    c.open('rpa-0016');
    assert(!c.key('k', {tagName: 'BUTTON'}, {metaKey: true}).defaultPrevented);
    assert.equal(c.activeElement.id, 'detail-title');
  });
  await test('regression sensitivity: removing the close guard queues duplicate traversals', async () => {
    const oldBehavior = source.replace('if(closing||!dialog.open)return;', '');
    assert.notEqual(oldBehavior, source, 'update this mutation when close guard implementation changes');
    const c = await controller('', 0, oldBehavior); c.open('rpa-0016'); c.close(); c.close(); c.cancel();
    assert.equal(c.calls.back, 3);
  });
  console.log(`PASS: ${checks} controller-model regressions. No real-browser QA was performed.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
