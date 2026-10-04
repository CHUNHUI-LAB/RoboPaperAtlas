'use strict';
// Read-only controller checks. Does not establish browser layout or native focus.
// Run from the candidate repository: node --test tests/test_library_galaxy.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const code = fs.readFileSync(path.resolve('assets/library-galaxy.js'), 'utf8');
const topics = [
  ['all', '全部', '95'],
  ['navigation-space', '导航与空间理解', '29'],
  ['motion-manipulation', '运动与操作', '46'],
  ['robot-learning', '机器人学习', '50'],
  ['methods-resources', '方法与资源', '29'],
];
function make(reduced = false) {
  const buttons = topics.map(([topic, label, count]) => ({
    dataset: {topic}, events: {},
    getAttribute(name) {return name === 'aria-pressed' ? String(this.pressed || false) : null;},
    querySelector(selector) {
      if (selector === 'span') return {textContent: label};
      if (selector === 'b') return {textContent: count};
      return null;
    },
    addEventListener(type, callback) {this.events[type] = callback;},
  }));
  const status = {textContent: ''};
  const form = {events: {}, addEventListener(type, callback) {this.events[type] = callback;}};
  const scrolls = [];
  const results = {scrollIntoView(options) {scrolls.push(options);}};
  const root = {
    dataset: {},
    style: {setProperty(key, value) {this[key] = value;}},
    querySelectorAll(selector) {return selector === '.topic-filter' ? buttons : [];},
    querySelector(selector) {
      return {'[data-galaxy-status]': status, '.library-search': form, '#catalog-results': results}[selector] || null;
    },
  };
  const document = {events: {}, addEventListener(type, callback) {this.events[type] = callback;}, activeElement: null, querySelector(selector) {return selector === '.library-main' ? root : null;}};
  const window = {matchMedia(query) {assert.equal(query, '(prefers-reduced-motion: reduce)'); return {matches: reduced};}};
  vm.runInNewContext(code, {document, window});
  return {buttons, root, status, document, form, scrolls};
}
test('safe no-op outside the Library landing page', () => {
  vm.runInNewContext(code, {document: {querySelector: () => null}});
});
test('initial overview has no selected abstract region and explicitly disclaims citation relationships', () => {
  const f = make();
  assert.equal(f.root.dataset.galaxyTopic, 'all');
  assert.match(f.status.textContent, /不表示论文引用关系/);
  assert.equal(f.scrolls.length, 0);
});
test('all four topic hover descriptions use real topic labels and counts', () => {
  const f = make();
  for (let i = 1; i < f.buttons.length; i++) {
    const button = f.buttons[i];
    button.events.pointerenter();
    assert.equal(f.root.dataset.galaxyTopic, topics[i][0]);
    assert.match(f.status.textContent, new RegExp(topics[i][1]));
    assert.match(f.status.textContent, new RegExp(topics[i][2] + ' 篇相关书目'));
    assert.match(f.status.textContent, /抽象星域/);
    button.events.pointerleave();
    assert.equal(f.root.dataset.galaxyTopic, 'all');
  }
});
test('keyboard focus exposes the same topic information and Escape restores overview', () => {
  const f = make();
  for (const button of f.buttons.slice(1)) {
    f.document.activeElement = button;
    button.events.focus();
    assert.equal(f.root.dataset.galaxyTopic, button.dataset.topic);
    assert.match(f.status.textContent, /相关书目/);
    button.events.keydown({key: 'Escape'});
    assert.equal(f.root.dataset.galaxyTopic, 'all');
    f.document.activeElement = null;
    button.events.blur();
    assert.equal(f.root.dataset.galaxyTopic, 'all');
  }
});
test('pointer exit returns to the keyboard-focused topic', () => {
  const f = make(), focused = f.buttons[1], hovered = f.buttons[2];
  f.document.activeElement = focused;
  focused.events.focus();
  hovered.events.pointerenter();
  assert.equal(f.root.dataset.galaxyTopic, hovered.dataset.topic);
  hovered.events.pointerleave();
  assert.equal(f.root.dataset.galaxyTopic, focused.dataset.topic);
});
test('explicit search submit scrolls to results and obeys reduced motion', () => {
  for (const reduced of [false, true]) {
    const f = make(reduced);
    assert.deepEqual(Object.keys(f.form.events), ['submit']);
    assert.equal(f.scrolls.length, 0);
    f.form.events.submit();
    assert.equal(f.scrolls.length, 1);
    assert.equal(f.scrolls[0].block, 'start');
    assert.equal(f.scrolls[0].behavior, reduced ? 'auto' : 'smooth');
  }
});
test('enhancement leaves real filtering and history ownership to existing controllers', () => {
  const f = make();
  for (const button of f.buttons) assert.equal(button.events.click, undefined);
  assert.equal(f.form.events.input, undefined);
});
