"""Probe plumbing tests only, not browser or application acceptance."""
import copy
import unittest
from unittest.mock import patch
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from navigation_relation_interactions import probe_close, require_details_content_focus

RID='tasks:relation:88'
class DriverStub:
    def __init__(self, visible=True, nested=False):
        self.s={'route':{'scope':'scope:all'},'selected':RID,'hidden':False,'top':0 if visible else 49,'max':49,'window':0,'focus':'np-map-relation-evidence-'+RID,'selectorOpen':False,'close':{'x':100,'y':100,'visible':visible,'hit':visible}}
        self.calls=[];self.nested=nested
    def js(self,s,*args):
        if 'gap-key-observe-start' in s:
            self.events=[];return self.s['focus']
        if 'gap-key-observe-end' in s:return self.events
        if "querySelector('button').id" in s:return 'np-relation-entry-'+RID+'-scope:target'
        if 'details[open]' in s:return self.nested
        if "return !!document.activeElement.closest" in s:return True
        return copy.deepcopy(self.s)
    def selector(self,s):return {'element-6066-11e4-a52e-4f735466cecf':'panel'}
    def settle(self):pass
    def close(self):self.s.update(hidden=True,selected='',focus='np-relation-select-'+RID,selectorOpen=True)
    def call(self,method,path,data):
        self.calls.append((path,data));self.assert_no_element_click(path)
        for row in data['actions']:
            if row['type']=='wheel':self.s['top']=0;self.s['close'].update(visible=True,hit=True)
            if row['type']=='pointer':self.close()
            if row['type']=='key':
                origin=self.s['focus']
                keys=[x.get('value') for x in row['actions'] if x['type']=='keyDown']
                if '\ue004' in keys:self.s['focus']='np-overview-relation-close' if '\ue008' in keys else 'np-relation-entry-'+RID+'-scope:target'
                if '\ue007' in keys or '\ue00c' in keys:self.close()
                names={'\ue004':'Tab','\ue007':'Enter','\ue00c':'Escape','\ue008':'Shift'}
                self.events=[{'type':'keydown' if a['type']=='keyDown' else 'keyup','key':names[a['value']],'trusted':True,'target':origin if a['type']=='keyDown' else self.s['focus'],'tag':'BUTTON'} for a in row['actions']]
    @staticmethod
    def assert_no_element_click(path):
        assert '/element/' not in path,'must not use auto-scrolling element-click'

class ProbePlumbing(unittest.TestCase):
    @patch('navigation_relation_interactions.time.sleep')
    def test_pointer_requires_native_wheel_and_pointer(self,_):
        d=DriverStub(False);r=probe_close(d,RID,'pointer');self.assertTrue(r['after']['hidden']);self.assertEqual([c[1]['actions'][0]['type'] for c in d.calls],['wheel','pointer'])
    def test_tab_then_enter(self):
        d=DriverStub();r=probe_close(d,RID,'keyboard');self.assertEqual(r['after']['focus'],'np-relation-select-'+RID)
    def test_escape_panel_contract(self):
        d=DriverStub();self.assertTrue(probe_close(d,RID,'escape')['after']['hidden'])
    def test_open_details_not_mistaken_for_panel_escape(self):
        d=DriverStub(nested=True)
        with self.assertRaisesRegex(AssertionError,'precedence'):probe_close(d,RID,'escape')
        self.assertEqual(d.calls,[])
    def test_hidden_close_at_top_is_not_silently_auto_scrolled(self):
        d=DriverStub(False);d.s['top']=0
        with self.assertRaisesRegex(AssertionError,'not hittable'):probe_close(d,RID,'pointer')
        self.assertEqual(d.calls,[])

class ProbeFailures(unittest.TestCase):
    def test_route_drift_rejected(self):
        d=DriverStub();original=d.close
        def close():
            original();d.s['route']={'scope':'wrong'}
        d.close=close
        with self.assertRaises(AssertionError):probe_close(d,RID,'pointer')
    def test_wrong_return_focus_rejected(self):
        d=DriverStub();original=d.close
        def close():
            original();d.s['focus']='wrong'
        d.close=close
        with self.assertRaises(AssertionError):probe_close(d,RID,'keyboard')
    def test_occluded_close_rejected(self):
        d=DriverStub();d.s['close']['hit']=False
        with self.assertRaisesRegex(AssertionError,'not hittable'):probe_close(d,RID,'pointer')
    def test_keyboard_has_tab_shift_tab_enter(self):
        d=DriverStub();probe_close(d,RID,'keyboard')
        keys=[[x.get('value') for x in data['actions'][0]['actions'] if x['type']=='keyDown'] for _,data in d.calls]
        self.assertEqual(keys, [['\ue004'],['\ue008','\ue004'],['\ue007']])
    def test_wrong_selected_relation_rejected(self):
        d=DriverStub()
        with self.assertRaises(AssertionError):probe_close(d,'tasks:relation:90','escape')
        self.assertEqual(d.calls,[])
    def test_pointer_fitting_panel_does_not_claim_wheel(self):
        d=DriverStub();d.s['max']=0
        result=probe_close(d,RID,'pointer')
        self.assertEqual([data['actions'][0]['type'] for _,data in d.calls],['pointer'])
        self.assertEqual(result['before']['max'],0)


class WeakPathNegativeControls(unittest.TestCase):
    def test_forward_tab_landing_directly_on_close_rejected(self):
        d=DriverStub();original=d.call
        def call(method,path,data):
            original(method,path,data)
            actions=data['actions'][0]
            keys=[a.get('value') for a in actions.get('actions',[]) if a['type']=='keyDown']
            if keys==['\ue004']:d.s['focus']='np-overview-relation-close'
        d.call=call
        with self.assertRaisesRegex(AssertionError,'exact first endpoint'):probe_close(d,RID,'keyboard')
    def test_noop_forward_tab_rejected(self):
        d=DriverStub();original=d.call
        def call(method,path,data):
            original(method,path,data)
            keys=[a.get('value') for a in data['actions'][0]['actions'] if a['type']=='keyDown']
            if keys==['\ue004']:d.s['focus']='np-map-relation-evidence-'+RID
        d.call=call
        with self.assertRaisesRegex(AssertionError,'exact first endpoint'):probe_close(d,RID,'keyboard')
    def test_untrusted_key_events_rejected(self):
        d=DriverStub();original=d.call
        def call(method,path,data):
            original(method,path,data)
            for e in d.events:e['trusted']=False
        d.call=call
        with self.assertRaisesRegex(AssertionError,'untrusted'):probe_close(d,RID,'keyboard')
    def test_summary_inside_details_is_not_content(self):
        class Summary:
            def js(self,_):return {'id':'','tag':'SUMMARY','inside':True,'native':False}
        with self.assertRaisesRegex(AssertionError,'actual native selector'):require_details_content_focus(Summary(),'np-relation-select-'+RID)
    def test_wrong_selector_is_not_exact_first_selector(self):
        class Wrong:
            def js(self,_):return {'id':'wrong','tag':'BUTTON','inside':True,'native':True}
        with self.assertRaisesRegex(AssertionError,'actual native selector'):require_details_content_focus(Wrong(),'np-relation-select-'+RID)
    def test_exact_native_first_selector_accepted(self):
        class Right:
            def js(self,_):return {'id':'np-relation-select-'+RID,'tag':'BUTTON','inside':True,'native':True}
        require_details_content_focus(Right(),'np-relation-select-'+RID)

if __name__=='__main__':unittest.main()


