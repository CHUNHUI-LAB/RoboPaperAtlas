'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { fixture } = require('./map_dom_fixture.cjs');
const rows = f => f.$$('[data-map-row]').filter(row => !row.hidden).map(row => row.dataset.mapRow);
const camera = f => f.$('.map-world').getAttribute('transform');

test('search selection, related exploration, close and browser history retain source results and camera', () => {
  const f = fixture({reduced:true});
  f.input('whole-body');
  f.click('[data-camera="in"]');
  const sourceRows = rows(f), sourceCamera = camera(f);
  const input = f.$('#map-search');
  input.emit('keydown', {key:'Enter'});
  const selectedTitle = f.$('#map-selected-title').textContent;
  assert.equal(input.value, 'whole-body');
  assert.deepEqual(rows(f), sourceRows);
  assert.match(f.location.search, /q=whole-body/);
  assert.equal(f.$('#atlas-breadcrumbs').children.at(-1).getAttribute('aria-current'), 'location');
  assert(f.$('.map-panel-quicklook').dataset.preview);
  const selectedCamera = camera(f);
  f.click('[data-related-paper]');
  assert.equal(input.value, 'whole-body');
  assert.deepEqual(rows(f), sourceRows);
  f.goBack();
  assert.equal(f.$('#map-selected-title').textContent, selectedTitle);
  assert.equal(camera(f), selectedCamera);
  f.click('#map-panel-close');
  assert.equal(input.value, 'whole-body');
  assert.deepEqual(rows(f), sourceRows);
  assert.equal(camera(f), sourceCamera);
  f.goBack();
  assert.equal(f.$('#map-selected-title').textContent, selectedTitle);
  assert.equal(camera(f), selectedCamera);
  f.goBack();
  assert.equal(f.$('#map-selected-title'), null);
  assert.equal(camera(f), sourceCamera);
  assert.deepEqual(rows(f), sourceRows);
});

test('selecting a paper from a direction does not silently drill or narrow its source result set', () => {
  const f = fixture({reduced:true});
  f.click('[data-map-topic="navigation"]');
  f.click('[data-camera="in"]');
  const sourceRows = rows(f), sourceCamera = camera(f);
  const link = f.$(`[data-map-paper="${sourceRows[0]}"]`); link.focus(); link.emit('click', {button:0});
  assert.equal(rows(f).length, 18);
  assert.equal(f.$('[data-map-topic="navigation"]').getAttribute('aria-pressed'), 'true');
  assert(!f.location.search.includes('problem='));
  f.click('#map-panel-close');
  assert.equal(f.$('#paper-map').dataset.level, 'galaxy');
  assert.equal(camera(f), sourceCamera);
  assert.deepEqual(rows(f), sourceRows);
  assert.equal(f.document.activeElement, link);
});

test('direct filtered paper URLs preserve filters and bare paper URLs retain legacy exact-problem routing', () => {
  const filtered = fixture({url:'https://example.org/RoboPaperAtlas/map/?q=whole-body&paper=rpa-0012',reduced:true});
  assert.equal(filtered.$('#map-search').value, 'whole-body');
  assert(rows(filtered).length > 1);
  const bare = fixture({url:'https://example.org/RoboPaperAtlas/map/?paper=rpa-0012',reduced:true});
  assert(bare.location.search.includes('problem='));
  assert.match(bare.$('#atlas-breadcrumbs').textContent, /全身运动规划与控制/);
});

test('Chinese IME composition leaves results stable until committed and cannot select by Enter mid-composition', () => {
  const f = fixture({reduced:true});
  const input = f.$('#map-search');
  input.emit('compositionstart'); input.value = '强化学习'; input.emit('input', {isComposing:true});
  assert.equal(rows(f).length, 95);
  input.emit('keydown', {key:'Enter',isComposing:true});
  assert.equal(f.$('#map-selected-title'), null);
  input.emit('compositionend');
  assert(rows(f).length > 0 && rows(f).length < 95);
  assert.equal(f.$('#map-search').value, '强化学习');
});

test('mobile list selection survives enabling the optional map and closes to a valid overview', () => {
  const f = fixture({mobile:true,reduced:true});
  f.click('[data-map-paper="rpa-0012"]');
  f.click('[data-map-view="map"]');
  f.click('#map-panel-close');
  assert.equal(rows(f).length, 95);
  assert.equal(f.$('#paper-map').dataset.level, 'galaxy');
  assert(!camera(f).includes('NaN'));
  assert.equal(f.raf.size, 0);
});


test('mobile related paper outside the search returns focus to its visible source input', () => {
  const f = fixture({mobile:true,reduced:true});
  f.input('whole-body');
  const input = f.$('#map-search'); input.emit('keydown', {key:'Enter'});
  const related = f.$$('[data-related-paper]').find(button => f.$(`[data-map-row="${button.dataset.relatedPaper}"]`).hidden);
  assert(related, 'fixture must explore a paper outside the originating search');
  related.focus(); related.emit('click', {button:0});
  f.click('#map-panel-close');
  assert.equal(f.document.activeElement, input);
  assert(f.document.activeElement.isConnected);
  assert.equal(f.document.activeElement.closest('[hidden]'), null);
  assert.equal(input.value, 'whole-body');
  f.goBack(); f.goForward();
  assert(f.document.activeElement.isConnected);
  assert.equal(f.document.activeElement.closest('[hidden]'), null);
});
