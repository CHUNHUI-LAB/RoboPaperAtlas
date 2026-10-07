from pathlib import Path
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ProtocolFocusTests(unittest.TestCase):
    def test_browser_observation_regressions(self):
        run=subprocess.run(['node',str(ROOT/'tests/test_protocol_focus.cjs')],capture_output=True,text=True,timeout=120)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(run.stdout.count('PASS '),10,run.stdout)
