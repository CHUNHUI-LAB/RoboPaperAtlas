/* Optional real-browser QA. Requires an allowed local browser process and preview.
 * MAP_URL defaults to the isolated local preview. Does not deploy or change data.
 */
'use strict';
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const url = process.env.MAP_URL || 'http://127.0.0.1:8129/map/index.html';
const browserPath = process.env.CHROMIUM_PATH || '/usr/bin/chromium';
const output = path.join(__dirname, '..', 'qa-artifacts');
require('node:fs').mkdirSync(output, { recursive: true });
const pause = page => page.waitForTimeout(430);
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: browserPath });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url); await pause(page);
    assert.equal(await page.locator('#paper-map').getAttribute('data-view'), 'map');
    assert.equal(await page.locator('.map-node:visible').count(), 95);
    assert.equal(await page.locator('.map-edges path').count(), 0);
    const stable = await page.locator('.map-world').getAttribute('transform');
    await pause(page); assert.equal(await page.locator('.map-world').getAttribute('transform'), stable);
    await page.screenshot({ path: path.join(output, 'desktop-map.png'), fullPage: true });

    // Search -> focus -> real links -> disabled reports, with all metadata unmodified.
    const input = page.locator('#map-search');
    await input.fill('Deep Whole-Body Control'); await input.press('ArrowDown'); await input.press('Enter'); await pause(page);
    assert.match(await page.locator('#map-selected-title').innerText(), /Deep Whole-Body Control/);
    assert.equal(await page.locator('.map-stage-list button:disabled').count(), 3);
    assert.equal(await page.locator('.map-resource-links a', { hasText: '出版方 PDF' }).getAttribute('href'), 'https://proceedings.mlr.press/v205/fu23a/fu23a.pdf');
    assert.ok(await page.locator('.map-edges path').count() <= 8);
    assert.match(page.url(), /paper=rpa-0012/);
    await page.screenshot({ path: path.join(output, 'desktop-selected.png'), fullPage: true });
    const beforeRelated = await page.locator('#map-selected-title').innerText();
    await page.locator('[data-related-paper]').first().click(); await pause(page);
    assert.notEqual(await page.locator('#map-selected-title').innerText(), beforeRelated);
    await page.goBack(); await pause(page);
    assert.equal(await page.locator('#map-selected-title').innerText(), beforeRelated);
    await page.locator('#map-panel-close').click(); await pause(page);
    assert.equal(await page.locator('.map-panel-selected').isVisible(), false);
    assert.equal(await page.locator('.map-edges path').count(), 0);
    assert.ok(!page.url().includes('paper='));

    // Every category is reachable in one click, and unknown query has a usable reset.
    for (const [topic, count] of [['navigation',16], ['wbc',31], ['vla',17], ['foundations',31], ['all',95]]) {
      await page.locator(`[data-map-topic="${topic}"]`).click(); await pause(page);
      assert.equal(await page.locator('.map-node:visible').count(), count);
    }
    await input.fill('no_match_7f7389'); await pause(page);
    assert.equal(await page.locator('.map-node:visible').count(), 0);
    assert.equal(await page.locator('.map-empty').isVisible(), true);
    await page.locator('.map-empty [data-map-reset]').click(); await pause(page);
    assert.equal(await page.locator('.map-node:visible').count(),95);

    // Repeated/interrupted close-search-view sequences must not reopen stale panels.
    for (const query of ['diffusion','mpc','navigation']) {
      await input.fill(query); await input.press('Enter');
      await page.locator('#map-panel-close').click();
      await page.locator('[data-map-view="list"]').click();
      await page.locator('[data-map-view="map"]').click();
    }
    await pause(page); assert.equal(await page.locator('.map-panel-selected').isVisible(),false);
    assert.equal(await page.locator('#map-suggestions').isVisible(),false);
    const stopped = await page.locator('.map-world').getAttribute('transform');
    await pause(page); assert.equal(await page.locator('.map-world').getAttribute('transform'),stopped);

    // Direct dragging is immediate. Ordinary wheel never changes camera scale.
    const box = await page.locator('#map-canvas').boundingBox();
    const prior = await page.locator('.map-world').getAttribute('transform');
    await page.mouse.move(box.x + 20, box.y + box.height / 2); await page.mouse.down();
    await page.mouse.move(box.x + 50, box.y + box.height / 2 + 20); await page.mouse.up();
    const dragged = await page.locator('.map-world').getAttribute('transform'); assert.notEqual(dragged,prior);
    await page.mouse.wheel(0,180); await pause(page);
    assert.equal(await page.locator('.map-world').getAttribute('transform'),dragged);
    await page.locator('[data-camera="fit"]').click(); await pause(page);
    // Keyboard node selection, Escape restore, and map zoom controls.
    await page.locator('.map-node[tabindex="0"]').focus();
    await page.keyboard.press('ArrowRight'); await page.keyboard.press('Enter');
    assert.equal(await page.locator('.map-panel-selected').isVisible(),true);
    await page.keyboard.press('Escape'); assert.equal(await page.locator('.map-panel-selected').isVisible(),false);

    // Responsive mobile emulation only; this is NOT a physical-device touch test.
    const mobile = await browser.newPage({ viewport: {width:390,height:844}, isMobile:true, hasTouch:true });
    mobile.on('pageerror',error=>errors.push(error.message)); await mobile.goto(url); await pause(mobile);
    assert.equal(await mobile.locator('#paper-map').getAttribute('data-view'),'list');
    assert.equal(await mobile.locator('.map-paper-list li:visible').count(),95);
    assert.ok(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await mobile.screenshot({path:path.join(output,'mobile-list.png'),fullPage:false});
    await mobile.locator('[data-map-paper="rpa-0012"]').click();
    assert.match(await mobile.locator('#map-selected-title').innerText(),/Deep Whole-Body/);
    await mobile.locator('#map-panel-close').click(); await mobile.locator('[data-map-view="map"]').click();
    assert.equal(await mobile.locator('#map-canvas').isVisible(),true);
    await mobile.locator('[data-camera="in"]').click(); await pause(mobile);
    assert.ok(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await mobile.screenshot({path:path.join(output,'mobile-optional-map.png'),fullPage:false});

    const reduced = await browser.newPage({viewport:{width:1280,height:950},reducedMotion:'reduce'});
    reduced.on('pageerror',error=>errors.push(error.message)); await reduced.goto(url); await pause(reduced);
    await reduced.locator('#map-search').fill('Deep Whole-Body Control'); await reduced.locator('#map-search').press('Enter');
    const reducedTransform=await reduced.locator('.map-world').getAttribute('transform'); await pause(reduced);
    assert.equal(await reduced.locator('.map-world').getAttribute('transform'),reducedTransform);
    assert.equal(await reduced.locator('.map-panel-selected').evaluate(el=>getComputedStyle(el).animationName),'none');

    const nojs = await browser.newPage({javaScriptEnabled:false}); await nojs.goto(url);
    assert.equal(await nojs.locator('.map-paper-list li:visible').count(),95);
    assert.equal(await nojs.locator('.map-toolbar').isVisible(),false);
    assert.equal(errors.length,0,errors.join('\n'));
    console.log('PASS desktop, search, resource links, all topics, selected-only theme edges, close/back/repeated flows, keyboard, direct drag, ordinary wheel, mobile emulation, reduced motion, no-JS fallback. Real touch remains untested.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1});
