import re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ReadableNavigationTests(unittest.TestCase):
 def test_home_accessible_name_keeps_visible_chinese(self):
  source=(ROOT/'scripts/home_page.py').read_text()
  self.assertNotIn('aria-label="{esc(hints[key])}',source)
  self.assertEqual(source.count('aria-label="{esc(topic_labels[key])}'),3)
 def test_explicit_large_control_and_hero_rules(self):
  css=(ROOT/'assets/experience.css').read_text()
  self.assertIn('.atlas-experience .topic-filter{font-size:17px',css)
  self.assertIn('.atlas-galaxy .atlas-galaxy__topics a{font-size:17px',css)
  self.assertIn('.filter-panel label,.filter-panel select',css)
  self.assertIn('.paper-grid:not(.list-view) .card-summary',css)
