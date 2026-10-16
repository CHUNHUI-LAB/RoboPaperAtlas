"""Supplemental real-WebDriver probes. Never edits the original receipt.

Import from an existing exact-ed121ae browser run; call probe_close(driver, rid,
mode) after opening that relation normally. mode: pointer, keyboard, escape.
Real execution is pending; stub tests are not browser acceptance. It changes only temporary UI state.
"""
import time

SNAPSHOT = r'''
var p=document.getElementById('np-overview-relation-panel'),c=document.getElementById('np-overview-relation-close');
var r=c.getBoundingClientRect(),b=p.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,h=document.elementFromPoint(x,y);
return {route:NavigationProductApp.getState().route,selected:document.getElementById('np-overview-map').dataset.selectedRelation,
 hidden:p.hidden,top:p.scrollTop,max:p.scrollHeight-p.clientHeight,window:scrollY,
 focus:document.activeElement.id,selectorOpen:document.getElementById('np-task-relations').open,
 close:{x:x,y:y,visible:r.width>0&&r.height>0&&r.top>=Math.max(0,b.top+p.clientTop)&&r.bottom<=Math.min(innerHeight,b.top+p.clientTop+p.clientHeight)&&r.left>=Math.max(0,b.left+p.clientLeft)&&r.right<=Math.min(innerWidth,b.left+p.clientLeft+p.clientWidth),hit:!!h&&(h===c||c.contains(h))}};
'''

def key(driver, value, shift=False):
    expected = {'\ue004':'Tab','\ue007':'Enter','\ue00c':'Escape'}[value]
    origin = driver.js(r'''// gap-key-observe-start
      if(window.__relationGapKeys)throw Error('Key observation already active');
      var capture={events:[]};
      capture.listener=function(e){capture.events.push({type:e.type,key:e.key,
        trusted:e.isTrusted,target:e.target.id||'',tag:e.target.tagName});};
      window.__relationGapKeys=capture;
      document.addEventListener('keydown',capture.listener,true);
      document.addEventListener('keyup',capture.listener,true);
      return document.activeElement.id||'';
    ''')
    actions=[]
    if shift: actions.append({'type':'keyDown','value':'\ue008'})
    actions += [{'type':'keyDown','value':value},{'type':'keyUp','value':value}]
    if shift: actions.append({'type':'keyUp','value':'\ue008'})
    try:
        driver.call('POST','/actions',{'actions':[{'type':'key','id':'gap-key','actions':actions}]})
        driver.settle()
    finally:
        events = driver.js(r'''// gap-key-observe-end
          var capture=window.__relationGapKeys;
          document.removeEventListener('keydown',capture.listener,true);
          document.removeEventListener('keyup',capture.listener,true);
          delete window.__relationGapKeys;return capture.events;
        ''')
    assert events and all(e['trusted'] for e in events), ('untrusted or missing native key events',events)
    down=[e for e in events if e['type']=='keydown' and e['key']==expected]
    up=[e for e in events if e['type']=='keyup' and e['key']==expected]
    assert len(down)==1 and len(up)==1 and down[0]['target']==origin, (origin,events)
    return {'origin':origin,'events':events}

def probe_close(driver, relation, mode):
    """Requires relation opened by actual control. Pointer never element-clicks close.

    Existing screenshot calls element-click which may auto-scroll; here only native
    wheel reaches the button, then geometry/hit-test precedes viewport pointer click.
    Keyboard uses Tab into native panel content, Shift+Tab to close, then Enter.
    Escape is tested only with focus in panel, matching current source contract.
    """
    assert mode in ('pointer','keyboard','escape')
    initial=driver.js(SNAPSHOT)
    assert not initial['hidden'] and initial['selected']==relation, initial
    rows=[initial]
    keyboard_events=[]
    if mode=='pointer':
        for _ in range(64):
            s=driver.js(SNAPSHOT)
            if s['close']['visible'] and s['close']['hit']: break
            if s['top']==0: raise AssertionError(('close not hittable at panel top',s))
            driver.call('POST','/actions',{'actions':[{'type':'wheel','id':'gap-wheel','actions':[{'type':'scroll','origin':driver.selector('#np-overview-relation-panel'),'x':0,'y':0,'deltaX':0,'deltaY':-min(240,max(1,s['top'])),'duration':100}]}]})
            time.sleep(.15);driver.settle();rows.append(driver.js(SNAPSHOT))
        else: raise AssertionError('native wheel did not reach close within safety bound')
        s=driver.js(SNAPSHOT);assert s['close']['visible'] and s['close']['hit'],s
        driver.call('POST','/actions',{'actions':[{'type':'pointer','id':'gap-pointer','parameters':{'pointerType':'mouse'},'actions':[{'type':'pointerMove','duration':0,'origin':'viewport','x':round(s['close']['x']),'y':round(s['close']['y'])},{'type':'pointerDown','button':0},{'type':'pointerUp','button':0}]}]})
    elif mode=='keyboard':
        first = driver.js("return document.getElementById('np-map-relation-evidence-'+arguments[0]).querySelector('button').id;", relation)
        keyboard_events.append(key(driver,'\ue004'))
        entered=driver.js(SNAPSHOT)
        assert entered['focus']==first and first.startswith('np-relation-entry-'+relation+'-'), ('Tab did not enter exact first endpoint',entered,first)
        rows.append(entered)
        keyboard_events.append(key(driver,'\ue004',shift=True))
        s=driver.js(SNAPSHOT);rows.append(s)
        assert s['focus']=='np-overview-relation-close', ('Shift+Tab did not reach exact close',s)
        assert s['close']['visible'] and s['close']['hit'],s
        keyboard_events.append(key(driver,'\ue007'))
    else:
        assert driver.js("return !!document.activeElement.closest('#np-overview-relation-panel')"),'Escape contract requires focus inside panel'
        assert not driver.js("return !!document.activeElement.closest('details[open]')"),'nested details has first Escape precedence'
        keyboard_events.append(key(driver,'\ue00c'))
    driver.settle();final=driver.js(SNAPSHOT)
    assert final['hidden'] and not final['selected'],final
    assert final['focus']=='np-relation-select-'+relation and final['selectorOpen'],final
    assert final['route']==initial['route'],(initial,final)
    return {'relation':relation,'mode':mode,'before':initial,'movement':rows,'after':final,'keyboardEvents':keyboard_events}


def require_details_content_focus(driver, first_selector):
    actual=driver.js("var a=document.activeElement;return {id:a.id,tag:a.tagName,inside:!!a.closest('#np-task-relations[open]'),native:a.matches('button[data-relation-select]')&&!a.disabled&&a.tabIndex===0};")
    assert actual=={'id':first_selector,'tag':'BUTTON','inside':True,'native':True}, ('Tab did not enter actual native selector content',actual)


def _run_relation_interaction_gaps(driver, relations, report, save, footer, reveal,
                                  stability, panel_saved, wait_for):
    """Additive exact-site probes. No DOM fixture insertion or app mutations.

    Run inside the existing viewport loop after its original endpoint-Back check.
    Native inputs drive the tested actions. Existing reveal and endpoint setup
    may set visibility/focus; temporary listeners only observe trusted key events.
    """
    records = report.setdefault('relationInteractionGapChecks', [])

    def open_relation(expected):
        if not driver.js("return document.getElementById('np-task-relations').open"):
            driver.click(driver.selector('#np-task-relations > summary'))
        control = driver.selector('[data-relation-select="' + expected['id'] + '"]')
        reveal(driver, control, expected['id'], report, save)
        driver.click(control)
        driver.settle()
        state = driver.js(SNAPSHOT)
        assert state['selected'] == expected['id'] and not state['hidden'], state
        assert state['focus'] == 'np-map-relation-evidence-' + expected['id'], state
        return state

    def wheel_to_end():
        for _ in range(64):
            before = driver.js(SNAPSHOT)
            if before['top'] == before['max']:
                return before
            driver.call('POST', '/actions', {'actions':[{'type':'wheel','id':'gap-end-wheel','actions':[
                {'type':'scroll','origin':driver.selector('#np-overview-relation-panel'),
                 'x':0,'y':0,'deltaX':0,'deltaY':240,'duration':100}]}]})
            wait_for(lambda: driver.js(SNAPSHOT)['top'] != before['top'])
            driver.settle()
        raise AssertionError('native wheel did not reach panel end within safety bound')

    for expected in [next(r for r in relations if r['id'] == rid)
                     for rid in ('tasks:relation:88','tasks:relation:90')]:
        rid = expected['id']
        for mode in ('pointer','keyboard','escape'):
            opened = open_relation(expected)
            record = {'relation':rid, 'mode':mode, 'opened':opened, 'status':'running'}
            records.append(record); save()
            before = footer('gap-before-' + mode + '-' + rid)
            record['beforeFooter'] = before
            if mode == 'pointer':
                record['endOfPanel'] = wheel_to_end()
                record['hasNaturalOverflow'] = record['endOfPanel']['max'] > 0
            record['probe'] = probe_close(driver, rid, mode)
            after = footer('gap-after-' + mode + '-' + rid)
            stability(before, after)
            panel_saved(after)
            record['afterFooter'] = after
            record['status'] = 'passed'; save()

        # The exact source has no details descendant inside the relation panel.
        # Exercise genuine active-details priority in its native selector instead.
        record={'relation':rid,'mode':'active-native-details-escape-priority','status':'running'}
        records.append(record);save()
        open_relation(expected)
        driver.click(driver.selector('#np-task-relations > summary'))
        selector = driver.selector('[data-relation-select="' + rid + '"]')
        reveal(driver, selector, rid, report, save)
        # reveal scrolls only; native Tab from the summary enters the selector.
        summary = driver.selector('#np-task-relations > summary')
        driver.click(summary)  # close, focus summary
        details_keys=[key(driver, '\ue007')]  # open via Enter, focus stays summary
        first_selector=driver.js("return document.querySelector('#np-task-relations [data-relation-select]').id")
        details_keys.append(key(driver, '\ue004'))
        require_details_content_focus(driver,first_selector)
        before = driver.js(SNAPSHOT)
        details_keys.append(key(driver, '\ue00c'))
        after = driver.js(SNAPSHOT)
        assert not after['selectorOpen'] and not after['hidden'] and after['selected'] == rid
        assert after['route'] == before['route']
        assert driver.js("return document.activeElement===document.querySelector('#np-task-relations > summary')")
        nested_count = driver.js("return document.querySelectorAll('#np-overview-relation-panel details').length")
        record.update({'relation':rid, 'mode':'active-native-details-escape-priority',
                        'before':before,'after':after,'status':'passed',
                        'keyboardEvents':details_keys,'nestedPanelDetailsCount':nested_count,
                        'nestedPanelDetailsStatus':'not present in exact production markup' if not nested_count else 'not exercised'})
        save()

        # Both endpoints use the same original geometry and exact restoration gate.
        open_relation(expected)
        endpoint = driver.js("return document.getElementById(arguments[0]);",
                             'np-relation-entry-' + rid + '-' + expected['to'])
        # Setup focus/visibility exactly as the existing relation90 regression;
        # navigation and Back remain actual WebDriver input/history commands.
        driver.js("arguments[0].scrollIntoView({block:'center'});arguments[0].focus({preventScroll:true});", endpoint)
        driver.settle()
        before = footer('gap-endpoint-before-' + rid)
        record = {'relation':rid,'mode':'endpoint-back','beforeFooter':before,'status':'running'}
        records.append(record); save()
        driver.click(endpoint); driver.settle()
        assert driver.js('return NavigationProductApp.getState().route.scope') == expected['to']
        driver.call('POST','/back',{}); driver.settle()
        after = footer('gap-endpoint-back-' + rid)
        stability(before, after, restore=True)
        record['afterFooter'] = after; record['status'] = 'passed'; save()


def run_relation_interaction_gaps(driver, relations, report, save, footer, reveal,
                                  stability, panel_saved, wait_for):
    try:
        return _run_relation_interaction_gaps(driver, relations, report, save,
            footer, reveal, stability, panel_saved, wait_for)
    except Exception as error:
        for record in report.get('relationInteractionGapChecks', []):
            if record.get('status') == 'running':
                record.update(status='failed', error=type(error).__name__ + ': ' + str(error))
        save()
        raise
