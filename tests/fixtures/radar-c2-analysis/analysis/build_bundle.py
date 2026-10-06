"""Deterministic local bundle. No retrieval, new inference, stage mutation or publication."""
from pathlib import Path
import json
ROOT=Path(__file__).parent/'data'
data={'schema':json.loads((ROOT/'method.json').read_text()),'mapping':json.loads((ROOT/'mapping.json').read_text()),'compat':json.loads((ROOT/'analysis.compat.json').read_text())}
m=data['mapping'];c=data['compat']
assert m['existingStageStateMutation'] is False and c['existingStageStateMutation'] is False
assert [(a['nodeId'],a['state'],a['answer']) for a in m['answers']]==[(a['nodeId'],a['state'],a['answer']) for a in c['answers']]
assert len(data['schema']['nodes'])==59 and len(m['expandedNodes'])==13 and len(m['unresolvedQuestions'])==6
(ROOT/'bundle.js').write_text('window.C2_DATA = '+json.dumps(data,ensure_ascii=False)+';\n')
print('Deterministic C2 bundle rebuilt from frozen local inputs')
