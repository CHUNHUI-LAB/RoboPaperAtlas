import json,re,sys,unittest
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import home

class TopicControls(HTMLParser):
 def __init__(self):super().__init__();self.buttons=[];self.current=None;self.in_label=False
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='button' and 'data-topic' in attrs:
   self.current={'attrs':attrs,'visible':''};self.buttons.append(self.current)
  elif self.current is not None and tag=='span':self.in_label=True
 def handle_endtag(self,tag):
  if tag=='span':self.in_label=False
  elif tag=='button':self.current=None
 def handle_data(self,value):
  if self.current is not None and self.in_label:self.current['visible']+=value

class ReadableNavigationTests(unittest.TestCase):
 def test_home_topic_accessible_names_include_visible_chinese(self):
  parser=TopicControls();parser.feed(home(json.loads((ROOT/'data/catalog.json').read_text())))
  self.assertEqual(len(parser.buttons),5)
  for button in parser.buttons:
   visible=button['visible'].strip();name=button['attrs'].get('aria-label',visible)
   self.assertTrue(visible);self.assertIn(visible,name)
   self.assertRegex(visible,r'[\u4e00-\u9fff]')
   self.assertEqual(button['attrs'].get('type'),'button')
   self.assertIn(button['attrs'].get('aria-pressed'),['true','false'])
 def test_library_controls_have_touch_targets_and_readable_text(self):
  css=(ROOT/'assets/library.css').read_text()
  for selector,size in [(r'\.library-page \.topic-filter',16),(r'\.library-page \.filter-panel select',16),(r'\.library-page \.catalog-search-trigger',18)]:
   declarations=re.search(selector+r'\{([^}]+)\}',css).group(1)
   self.assertIn(f'font-size:{size}px',declarations)
   target=re.search(r'min-height:(\d+)px',declarations)
   self.assertIsNotNone(target);self.assertGreaterEqual(int(target.group(1)),44)
  self.assertIn('.mobile-topic-select',css)
  self.assertIn('outline:2px solid var(--accent)',css)
 def test_filter_dialog_is_progressive_and_labeled(self):
  page=home(json.loads((ROOT/'data/catalog.json').read_text()))
  self.assertIn('<details class="filter-disclosure"><summary>',page)
  self.assertIn('id="catalog-filter-title"',page)
  self.assertIn('id="apply-catalog-filters"',page)
  js=(ROOT/'assets/library.js').read_text()
  self.assertIn("document.createElement('dialog')",js)
  self.assertIn("setAttribute('aria-labelledby', 'catalog-filter-title')",js)
  self.assertIn('filterDialog.showModal()',js)
  self.assertIn("filterDialog.addEventListener('cancel'",js)
  self.assertIn('summary.focus({preventScroll: true})',js)

# Bounded static cascade model for the controls below. It reads the production
# stylesheets in load order and models selector specificity, inherited variables,
# color/background inheritance and alpha compositing. It is not browser/layout QA.
def css_split(text,separator=','):
 parts=[];start=0;depth=0;quote=None
 for i,char in enumerate(text):
  if quote:
   if char==quote and (i==0 or text[i-1]!='\\'):quote=None
  elif char in '\"\'':quote=char
  elif char in '([':depth+=1
  elif char in ')]':depth-=1
  elif char==separator and depth==0:parts.append(text[start:i].strip());start=i+1
 parts.append(text[start:].strip());return parts

class CssNode:
 def __init__(self,tag,attrs=(),parent=None):
  self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[]
  if parent:parent.children.append(self)

class CssDocument(HTMLParser):
 def __init__(self,html):
  super().__init__();self.root=CssNode('document');self.stack=[self.root];self.nodes=[];self.feed(html)
 def handle_starttag(self,tag,attrs):
  node=CssNode(tag,attrs,self.stack[-1]);self.nodes.append(node)
  if tag not in {'meta','link','input','br','hr','img','source','wbr'}:self.stack.append(node)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:self.stack=self.stack[:i];break
 def find(self,tag=None,cls=None,ident=None):
  return next(n for n in self.nodes if (tag is None or n.tag==tag) and (cls is None or cls in n.attrs.get('class','').split()) and (ident is None or n.attrs.get('id')==ident))

def css_chain(selector):
 parts=[];token='';depth=0;relation=None;quote=None
 for char in selector:
  if quote:
   token+=char
   if char==quote:quote=None
  elif char in '\"\'':quote=char;token+=char
  elif char in '([':depth+=1;token+=char
  elif char in ')]':depth-=1;token+=char
  elif depth==0 and (char.isspace() or char in '>+~'):
   if token:parts.append((token,relation));token='';relation=' '
   if char in '>+~':relation=char
  else:token+=char
 if token:parts.append((token,relation))
 return parts

def css_tokens(compound):
 tokens=[];i=0
 while i<len(compound):
  char=compound[i]
  if char=='*':tokens.append(('universal','*'));i+=1;continue
  if char=='[':
   end=compound.index(']',i);tokens.append(('attribute',compound[i+1:end]));i=end+1;continue
  prefix=re.match(r'(::?|[.#])?([-\w]+)',compound[i:])
  if not prefix:raise AssertionError('Unsupported CSS selector: '+compound)
  marker,name=prefix.groups();i+=len(prefix.group())
  kind={None:'tag','.':'class','#':'id',':':'pseudo','::':'element'}[marker]
  if kind=='pseudo' and name in {'before','after'}:kind='element'
  if i<len(compound) and compound[i]=='(':
   start=i+1;depth=1;i+=1
   while depth:
    if compound[i]=='(':depth+=1
    elif compound[i]==')':depth-=1
    i+=1
   tokens.append(('function',(name,compound[start:i-1])))
  else:tokens.append((kind,name))
 return tokens

def css_specificity(selector):
 result=[0,0,0]
 for compound,_ in css_chain(selector):
  for kind,value in css_tokens(compound):
   if kind=='id':result[0]+=1
   elif kind in {'class','attribute','pseudo'}:result[1]+=1
   elif kind in {'tag','element'}:result[2]+=1
   elif kind=='function':
    name,body=value
    if name=='where':continue
    if name not in {'is','not','has'}:raise AssertionError('Unsupported CSS function: '+name)
    extra=max(css_specificity(s) for s in css_split(body))
    result=[a+b for a,b in zip(result,extra)]
 return tuple(result)

def css_matches(selector,node,target,states):
 def descendant(child,ancestor):
  while child:
   if child is ancestor:return True
   child=child.parent
  return False
 def compound_matches(compound,current):
  for kind,value in css_tokens(compound):
   if kind=='element':return False
   if kind=='tag' and current.tag!=value:return False
   if kind=='class' and value not in current.attrs.get('class','').split():return False
   if kind=='id' and current.attrs.get('id')!=value:return False
   if kind=='attribute':
    attr=re.fullmatch(r'([-\w]+)(?:=([\"\']?)(.*?)\2)?',value)
    if not attr:raise AssertionError('Unsupported CSS attribute: '+value)
    name,_,expected=attr.groups()
    if name not in current.attrs or (expected is not None and current.attrs[name]!=expected):return False
   if kind=='pseudo':
    if value=='root':match=current.tag=='html'
    elif value in {'hover','active'}:match=value in states and descendant(target,current)
    elif value=='focus-visible':match=value in states and current is target
    elif value=='focus-within':match='focus-visible' in states and descendant(target,current)
    elif value=='first-child':match=current.parent is not None and current.parent.children[0] is current
    elif value=='last-child':match=current.parent is not None and current.parent.children[-1] is current
    else:raise AssertionError('Unsupported CSS pseudo-class: '+value)
    if not match:return False
   if kind=='function':
    name,body=value
    if name in {'is','where','not'}:
     match=any(css_matches(part,current,target,states) for part in css_split(body))
     if match==(name=='not'):return False
    else:raise AssertionError('Unsupported matching CSS function: '+name)
  return True
 parts=css_chain(selector)
 def match_at(index,current):
  if current is None or not compound_matches(parts[index][0],current):return False
  if index==0:return True
  relation=parts[index][1]
  if relation=='>':return match_at(index-1,current.parent)
  if relation in {'+','~'}:
   siblings=current.parent.children[:current.parent.children.index(current)] if current.parent else []
   return any(match_at(index-1,n) for n in (siblings[-1:] if relation=='+' else siblings))
  ancestor=current.parent
  while ancestor:
   if match_at(index-1,ancestor):return True
   ancestor=ancestor.parent
  return False
 return bool(parts) and match_at(len(parts)-1,node)

def css_rules(source,width):
 source=re.sub(r'/\*.*?\*/','',source,flags=re.S)
 def walk(text):
  position=0
  while position<len(text):
   opening=text.find('{',position)
   if opening<0:break
   header=text[position:opening].strip();depth=1;closing=opening+1
   while depth:
    if text[closing]=='{':depth+=1
    elif text[closing]=='}':depth-=1
    closing+=1
   body=text[opening+1:closing-1];position=closing
   if header.startswith('@media'):
    query=header[6:].strip();checks=[]
    for item in re.findall(r'\(([^)]+)\)',query):
     key,value=[x.strip() for x in item.split(':',1)]
     if key in {'min-width','max-width'}:
      assert value.endswith('px'),query;size=float(value[:-2]);checks.append(width>=size if key=='min-width' else width<=size)
     elif key=='prefers-reduced-motion':checks.append(value=='no-preference')
     else:raise AssertionError('Unsupported modeled media query: '+query)
    if checks and all(checks):yield from walk(body)
   elif header.startswith('@keyframes'):continue
   elif header.startswith('@'):raise AssertionError('Unsupported modeled CSS at-rule: '+header)
   else:
    declarations=[]
    for item in css_split(body,';'):
     if ':' not in item:continue
     name,value=item.split(':',1);name=name.strip();value=value.strip()
     if name in {'color','background','background-color'} or name.startswith('--'):
      important=value.endswith('!important');value=value.removesuffix('!important').strip()
      declarations.append(('background-color' if name=='background' else name,value,important))
    if declarations:
     for selector in css_split(header):yield selector,css_specificity(selector),declarations
 return list(walk(source))

def css_rgba(value,current=(0,0,0,1)):
 value=value.strip().lower();named={'white':'#fff','black':'#000','transparent':'#0000','none':'#0000'};value=named.get(value,value)
 if value=='currentcolor':return current
 # This bounded model checks the worst endpoint of the declared two-stop
 # monochromatic control gradients; it is not a general image contrast test.
 if value.startswith('linear-gradient('):
  stops=re.findall(r'#[0-9a-f]{3,8}',value)
  assert len(stops)>=2,value
  return min((css_rgba(stop,current) for stop in stops),key=lambda stop:css_contrast(current,css_composite(stop,(.031,.047,.075,1))))
 if value.startswith('#'):
  digits=value[1:]
  if len(digits) in {3,4}:digits=''.join(c*2 for c in digits)
  if len(digits)==6:digits+='ff'
  assert len(digits)==8,value
  return tuple(int(digits[i:i+2],16)/255 for i in [0,2,4,6])
 match=re.fullmatch(r'rgba?\(([^)]+)\)',value)
 if match:
  numbers=[float(x.strip()) for x in match.group(1).split(',')]
  return tuple(x/255 for x in numbers[:3])+(numbers[3] if len(numbers)==4 else 1,)
 raise AssertionError('Unsupported modeled color/background: '+value)

def css_composite(front,back):
 alpha=front[3]+back[3]*(1-front[3])
 return tuple((front[i]*front[3]+back[i]*back[3]*(1-front[3]))/alpha for i in range(3))+(alpha,)

def css_contrast(foreground,background):
 def luminance(color):
  linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in color[:3]]
  return sum(a*b for a,b in zip(linear,[.2126,.7152,.0722]))
 a,b=sorted([luminance(css_composite(foreground,background)),luminance(background)])
 return (b+.05)/(a+.05)

class ControlCascade:
 def __init__(self,source,width):self.rules=css_rules(source,width)
 def computed(self,node,target,states):
  cache={}
  def visit(current):
   if current is None:return {},(0,0,0,1),(1,1,1,1),{}
   if current in cache:return cache[current]
   variables,parent_color,parent_background,_=visit(current.parent);variables=dict(variables);winners={}
   for order,(selector,specificity,declarations) in enumerate(self.rules):
    if not css_matches(selector,current,target,states):continue
    for declaration,(name,value,important) in enumerate(declarations):
     priority=(important,specificity,order,declaration)
     if name not in winners or priority>=winners[name][0]:winners[name]=(priority,value,selector)
   for name,(_,value,_) in winners.items():
    if name.startswith('--'):variables[name]=value
   def resolved(value):
    for _ in range(20):
     if 'var(' not in value:return value
     def replace(match):
      name,fallback=match.groups()
      if name in variables:return variables[name]
      assert fallback is not None,'Undefined CSS variable '+name
      return fallback
     value=re.sub(r'var\(\s*(--[-\w]+)\s*(?:,\s*([^()]+))?\)',replace,value)
    raise AssertionError('Unresolved CSS variable: '+value)
   foreground=resolved(winners.get('color',(None,'inherit',None))[1])
   color=parent_color if foreground in {'inherit','unset'} else css_rgba(foreground)
   background=resolved(winners.get('background-color',(None,'transparent',None))[1])
   paint=parent_background if background=='inherit' else css_composite(css_rgba(background,color),parent_background)
   cache[current]=(variables,color,paint,winners);return cache[current]
  return visit(node)

class LibraryControlContrastTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source='\n'.join((ROOT/'assets'/name).read_text() for name in ['styles.css','library.css','library-editorial.css'])
  cls.dom=CssDocument(home(json.loads((ROOT/'data/catalog.json').read_text())))
  drawer=cls.dom.find(ident='drawer-body')
  # Generated by interface.js after a successful or failed quick-view request.
  primary=CssNode('a',{'class':'primary-link'},drawer)
  cls.controls={'preview full-detail anchor':primary}
  for name,tag,style,ident in [
   ('filter method','button','method-chip',None),('empty message','div','empty-state',None),('noscript message','p','noscript-note',None),('all results','a',None,'global-all-results'),('load more','button',None,'load-more'),('empty-state reset','button',None,'reset-filters'),
   ('paper preview','button','card-arrow',None),('paper detail','a','paper-open',None),('clear filters','button',None,'clear-all-filters'),
   ('search submit','button','library-search-submit',None),('global search','button','global-search-trigger',None),('mobile menu','button','mobile-menu',None),
   ('clear search','button',None,'clear-catalog-search'),('filter apply','button',None,'apply-catalog-filters'),
   ('preview close','button','drawer-close',None),('global search close','button','dialog-close',None),
   ('skip link','a','skip-link',None)]:
   cls.controls[name]=cls.dom.find(tag,style,ident)
  for n in cls.dom.nodes:
   if n.tag=='button' and 'data-view' in n.attrs:cls.controls['view '+n.attrs['data-view']]=n
   if n.tag=='button' and 'data-topic' in n.attrs:cls.controls['topic '+n.attrs['data-topic']]=n
  # Match library.js's progressive reparenting of the filter panel into a dialog.
  panel=cls.dom.find(cls='filter-panel');panel.parent.children.remove(panel)
  dialog=CssNode('dialog',{'class':'library-filter-dialog','id':'catalog-filter-dialog'},cls.dom.find('body'))
  panel.parent=dialog;dialog.children.append(panel)
  cls.controls['filter close']=cls.dom.find(cls='filter-panel-heading').children[-1]
 def test_known_control_text_contrast_in_declared_interaction_states(self):
  from itertools import product
  for width in [1180,390]:
   cascade=ControlCascade(self.source,width)
   for name,node in self.controls.items():
    for flags in product([False,True],repeat=3):
     states=frozenset(state for state,on in zip(['hover','focus-visible','active'],flags) if on)
     with self.subTest(width=width,control=name,states=sorted(states)):
      _,color,background,winners=cascade.computed(node,node,states)
      sources={key:value[2] for key,value in winners.items() if key in {'color','background-color'}}
      self.assertGreaterEqual(css_contrast(color,background),4.5,f'{color=} {background=} {sources=}')
 def test_model_detects_the_primary_anchor_hover_regression(self):
  # Prove the test notices selector precedence, not just favorable token pairs.
  old_library=re.sub(r'(\.library-page \.primary-link:hover\{[^}]*?)color:#fff;?',r'\1',(ROOT/'assets/library.css').read_text())
  self.assertNotEqual(old_library,(ROOT/'assets/library.css').read_text())
  old=(ROOT/'assets/styles.css').read_text()+'\n'+old_library
  node=self.controls['preview full-detail anchor']
  _,color,background,winners=ControlCascade(old,1180).computed(node,node,{'hover'})
  self.assertEqual(winners['color'][2],'.library-page a:hover')
  self.assertLess(css_contrast(color,background),4.5)

