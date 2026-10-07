"""Current task-map navigation replaces the nineteen-root entry, not source topology."""
from pathlib import Path
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
class TaskMapCandidateTests(unittest.TestCase):
    def test_task_map_dom_state_and_preservation(self):
        run=subprocess.run(['node',str(ROOT/'tests/test_task_map_candidate.cjs')],capture_output=True,text=True,timeout=120)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(run.stdout.count('PASS '),12,run.stdout)

    def test_corrected_script_free_cards_and_historical_blocks(self):
        import importlib.util, hashlib, re
        spec=importlib.util.spec_from_file_location('task_text',ROOT/'scripts/render_task_map_text.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        text=(ROOT/'previews/radar-c2-analysis/all-papers.html').read_text()
        self.assertEqual(mod.render(text,mod.payload()),text)
        self.assertEqual(text.count('data-current-contract='),4)
        self.assertEqual(text.count('class="current-protocol-version"'),7)
        historical=re.findall(r'<details class="historical-task-contract"><summary>历史记录：已被本轮定点纠错替代，不作为当前协议</summary>(.*?)</details>\s*<!-- task-map-',text,re.S)
        self.assertEqual(len(historical),4)
        current=re.sub(r'<details class="historical-task-contract">.*?</details></details>', '', text, flags=re.S)
        self.assertNotIn('有序或逐次给定类别目标',current)
        self.assertNotIn('MultiON/SayNav等协议各异',current)
        changed=text.replace('起始一次给定三个目标类别','伪造协议',1)
        self.assertNotEqual(mod.render(changed,mod.payload()),changed)

    def test_correction_replay_is_pinned_and_source_history_immutable(self):
        import importlib.util, sys, copy
        sys.path.insert(0,str(ROOT/'scripts'))
        import radar_c2_preview as c
        inputs={name:(ROOT/c.INPUT_SOURCE/name).read_bytes() for name in c.REVIEW_INPUTS}
        actual=c.assigned_json((ROOT/c.SOURCE/'data/literature.js').read_bytes(),'LITERATURE_TREE')
        self.assertEqual(c.expected_corrected_literature(inputs),actual)
        for name in ['data/literature-seed.json','data/task-contract-corrections-20261007.json']:
            changed=copy.deepcopy(inputs);changed[name]+=b' '
            with self.assertRaises(ValueError):c.expected_corrected_literature(changed)
