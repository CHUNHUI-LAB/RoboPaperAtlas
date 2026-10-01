"""Public HTML regression checks for visible, attributed Stage 2 excerpts."""
import hashlib
import json
from html.parser import HTMLParser


class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []
    def text(self):
        return ''.join(x.text() if isinstance(x, Node) else x for x in self.children)
    def nodes(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.nodes()
    def has(self, name):
        return name in self.attrs.get('class', '').split()
    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent


class Document(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self, text):
        super().__init__()
        self.root = self.current = Node()
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in self.VOID:
            self.current = node
    def handle_endtag(self, tag):
        if tag not in self.VOID:
            assert self.current.tag == tag, (self.current.tag, tag)
            self.current = self.current.parent
    def handle_data(self, value):
        self.current.children.append(value)


def normalized(text):
    return ''.join(text.split())


def assert_stage2_inline(case, prior_text, candidate_text):
    old, new = Document(prior_text).root, Document(candidate_text).root
    case.assertEqual(hashlib.sha256(candidate_text.encode()).hexdigest(), '60e314370d4086e277bced1a45ad607ce494bf71713255e79f6ef8722e7455dc')
    scripts = [n.text() for n in new.nodes() if n.tag == 'script' and n.attrs.get('type') != 'application/json']
    case.assertEqual(hashlib.sha256('\n'.join(scripts).encode()).hexdigest(), 'd6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798')
    rows = [n for n in old.nodes() if n.has('source-row')]
    pairs = [n for n in new.nodes() if n.has('source-unit-parallel')]
    case.assertEqual(len(rows), 37)
    case.assertEqual(len(pairs), 37)
    case.assertEqual([n.attrs['data-source-row'] for n in rows], [n.attrs['id'] for n in pairs])
    old_units = json.loads(next(n.text() for n in old.nodes() if 'data-source-units' in n.attrs))
    snapshots = []
    for row, pair, unit in zip(rows, pairs, old_units):
        nodes = list(pair.nodes())
        case.assertEqual(pair.attrs['id'], unit['id'])
        case.assertEqual(pair.attrs['data-source-row'], unit['id'])
        case.assertFalse(any(n.tag == 'details' or 'hidden' in n.attrs for n in [pair, *nodes, *pair.ancestors()]))
        quotes = [n for n in nodes if n.has('source-excerpt')]
        case.assertEqual(len(quotes), 1)
        quote = quotes[0]
        case.assertEqual((quote.tag, quote.attrs.get('lang')), ('blockquote', 'en'))
        gloss = next(n for n in nodes if n.has('source-gloss'))
        gloss_text = next(n.text() for n in gloss.nodes() if n.tag == 'p')
        case.assertTrue(gloss_text.strip())
        heading = next(n for n in nodes if n.has('source-pair-heading'))
        case.assertEqual(next(n.text() for n in heading.nodes() if n.tag == 'p'), unit['location'])
        citation = next(n for n in nodes if n.has('source-citation'))
        case.assertEqual([n.attrs['href'] for n in citation.nodes() if n.tag == 'a'], [unit['url'], '#excerpt-attribution'])
        writing = next(n for n in nodes if n.has('source-writing'))
        cells = [n for n in row.children if isinstance(n, Node) and n.tag == 'td']
        expected = '写作分析[推断]核心信息：' + unit['paraphrase'] + '功能与衔接' + cells[1].text() + '语言与可借鉴动作' + cells[2].text()
        case.assertEqual(normalized(writing.text()), normalized(expected), unit['id'])
        snapshots.append([unit['id'], quote.text(), gloss_text, unit['location'], unit['url']])
    # Pins the reviewed public quote/gloss/location/URL tuples without publishing authoring inputs.
    digest = hashlib.sha256(json.dumps(snapshots, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    case.assertEqual(digest, 'a623309570079ac581901fd22b9ac071e9f41df2e4a98f970729554d45d5f5e3')
    case.assertEqual(sum(len(row[1].split()) for row in snapshots), 857)
    article = next(n for n in new.nodes() if n.tag == 'article' and n.has('reader-article'))
    for n in old.nodes():
        if n.tag not in {'p', 'h3'} or not any(a.tag == 'article' for a in n.ancestors()):
            continue
        if any(a.has('source-row') for a in n.ancestors()):
            continue
        text = normalized(n.text())
        if text and '正文只展示中文概括与定位，不重排发布整段英文原文。' not in text:
            case.assertIn(text, normalized(article.text()))
    attribution = next(n for n in new.nodes() if n.attrs.get('id') == 'excerpt-attribution')
    case.assertIn('CC BY 4.0', attribution.text())
    urls = {n.attrs['href'] for n in attribution.nodes() if n.tag == 'a'}
    case.assertTrue({'https://proceedings.mlr.press/v270/ha25a.html', 'https://creativecommons.org/licenses/by/4.0/', 'https://proceedings.mlr.press/pmlr-license-agreement.html'} <= urls)
    case.assertFalse(any(n.has('reader-source-panel') or 'data-source-units' in n.attrs for n in new.nodes()))
