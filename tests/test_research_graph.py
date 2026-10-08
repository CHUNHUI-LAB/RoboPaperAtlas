"""Discovery entrypoint for explicit research graph and reading workflows.

These deterministic tests are separate from scientific cross-review and real-browser acceptance.
"""
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ResearchGraphContracts(unittest.TestCase):
    def test_versioned_reader(self):
        subprocess.run(['node', 'tests/test_research_graph.cjs'], cwd=ROOT, check=True)

    def test_reviewed_data_and_workflows(self):
        subprocess.run(['node', 'tests/test_research_workflows.cjs'], cwd=ROOT, check=True)
