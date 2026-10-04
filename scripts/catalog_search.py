"""Shared reviewed classification search terms for Library and Atlas."""
import json
from pathlib import Path
from topic_labels import taxonomy_search, method_tags
from discovery_facets import GROUPS, for_catalog, method_label
ROOT=Path(__file__).resolve().parents[1]
BROWSE=for_catalog(json.loads((ROOT/'data/catalog.json').read_text())['papers'],json.loads((ROOT/'data/classification.json').read_text())['records'])
BROWSE_LABELS={key:label for key,label,_ in GROUPS}
# Curated abbreviations supplement search without changing titles or classifications.
SEARCH_ALIASES=json.loads((ROOT/'data/search-aliases.json').read_text())
if set(SEARCH_ALIASES)-set(BROWSE) or any(not isinstance(values,list) or any(not isinstance(x,str) or not x.strip() for x in values) for values in SEARCH_ALIASES.values()):raise ValueError('Invalid curated search aliases')
def browse_groups(p):return BROWSE[p['id']]['groups']
def browse_search(p):return ' '.join([*(BROWSE_LABELS[k] for k in browse_groups(p)),*(method_label(t) for t in method_tags(p))])

def classification_search(p):
    return " ".join([taxonomy_search(p), browse_search(p), *SEARCH_ALIASES.get(p["id"], [])])
