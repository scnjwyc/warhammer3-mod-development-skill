"""Non-destructive identity diagnostics and a complete runtime hierarchy.

Runtime keys never replace GUID attributes in the source. Ambiguous links are
reported, not silently resolved by a last-wins dictionary.
"""
from collections import defaultdict
from dataclasses import dataclass
import uuid
from i18n import tr

@dataclass
class Issue:
 code: str
 message: str
 nodes: tuple
 keys: tuple = ()
 severity: str = "error"

SEVERITY_COLORS={'error':'#ec4d55','warning':'#deb544','info':'#8b929c'}
def highest_severity(issues):
 return next((level for level in ('error','warning','info') if any(i.severity==level for i in issues)),None)
def marker_kind(issues):
 return 'missing' if any(i.code=='missing_definition' for i in issues) else highest_severity(issues)
def initial_issues(doc):return [i for i in doc.issues if i.severity=='error']
def name_tag(name):return name.replace('(','').replace(')','')

def inspect_document(doc, hierarchy):
 from model import Node
 doc.raw_hierarchy=hierarchy
 doc.issues=[];doc.issues_by_key=defaultdict(list);doc.issues_by_line=defaultdict(list)
 doc.guid_repairs=[];doc.duplicate_repairs=[];doc.unsafe_keys=set();doc.placeholder_keys=set();doc.unlinked_keys=set();doc.missing_keys=set();doc.hierarchy_nodes={}
 defs=defaultdict(list);names=defaultdict(list);refs=defaultdict(list)
 for c in doc.components:
  if c.get('this'):defs[c.get('this')].append(c)
  for name in {c.tag,c.get('id')}:
   if name:names[name].append(c)
 raw=list(hierarchy.descendants())[1:]
 for n in raw:
  if n.get('this'):refs[n.get('this')].append(n)
 # Definitions already linked by both identity and name are not fallback candidates.
 claimed=set()
 for n in raw:
  exact=[c for c in defs.get(n.get('this'),[]) if n.tag in (c.tag,c.get('id'))]
  if len(exact)==1:claimed.add(exact[0])
 unmatched_names={name:[c for c in cs if c not in claimed] for name,cs in names.items()}
 node_keys=defaultdict(list);used=set();counts=defaultdict(int)
 doc.by_guid={};doc.parents={};doc.children={}
 def issue(code,message,*nodes,severity='error'):
  doc.issues.append(Issue(code,tr(message),tuple(nodes),severity=severity))
 def check_name(n,c):
  identity=c.get('id',c.tag)
  # Parentheses in an ID are preserved; exported XML tags omit them.
  if n.tag==c.tag==name_tag(identity):return
  if n.tag==c.tag:
   issue('name_mismatch','하이어라키와 컴포넌트 태그는 같지만 id 속성이 다릅니다.',n,c,severity='warning')
  else:issue('name_mismatch','하이어라키 태그와 컴포넌트 태그가 다릅니다.',n,c)

 def clone(n,parent,key):
  p=Node(n.tag,n.start,n.end,dict(n.attrs,this=key),parent)
  if hasattr(n,'close_start'):p.close_start=n.close_start
  return p
 projected=clone(hierarchy,None,None);doc.hierarchy=projected
 def attach(n,parent,index,c=None):
  candidates=defs.get(n.get('this'),[])
  if c is None:
   exact=[x for x in candidates if n.tag in (x.tag,x.get('id'))]
   c=exact[0] if len(exact)==1 else candidates[0] if len(candidates)==1 else None
   if c is None and len(unmatched_names.get(n.tag,[]))==1:
    c=unmatched_names[n.tag][0]
   if c is None:
    issue('missing_definition' if not candidates and not names.get(n.tag) else 'unresolved','컴포넌트 정의를 확정할 수 없습니다. 계층 항목을 임시 프레임으로 표시합니다.',n,*candidates)
   elif c.get('this')!=n.get('this'):
    issue('guid_mismatch','하이어라키와 컴포넌트 GUID가 다릅니다.',n,c)
    # A unique name, a unique hierarchy target and no competing definition.
    if n.get('this') and len(unmatched_names.get(n.tag,[]))==1 and len(refs[n.get('this')])==1 and not defs.get(n.get('this')):
     doc.guid_repairs.append((c,n.get('this')))
   if c is not None:check_name(n,c)
  original=n.get('this')
  key=original if original and original not in doc.by_guid else '@hierarchy/'+str(index)
  while key in doc.by_guid:key+='!'
  p=clone(n,parent,key);parent.children.append(p)
  doc.by_guid[key]=c if c is not None else Node(n.tag,n.start,n.end,dict(n.attrs,id=n.tag),n.parent)
  doc.parents[key]=parent.get('this');doc.children[key]=[]
  node_keys[n].append(key);doc.hierarchy_nodes[key]=n
  if c is not None:used.add(c);node_keys[c].append(key)
  if c is None:
   doc.placeholder_keys.add(key);doc.by_guid[key].placeholder=True
   if not candidates and not names.get(n.tag):doc.missing_keys.add(key)
  if c is None or key!=original or (c is not None and c.get('this')!=original):doc.unsafe_keys.add(key)
  for i,ch in enumerate(n.children):
   child=attach(ch,p,str(index)+'/'+str(i));doc.children[key].append(child.get('this'))
  return p
 for i,n in enumerate(hierarchy.children):attach(n,projected,i)
 for i,c in enumerate(doc.components):
  if c not in used:
   issue('orphan','하이어라키에서 사용하지 않는 컴포넌트 정의입니다.',c,severity='info')
   # No hierarchy children: definition internals are not child components.
   n=Node(c.tag,c.start,c.end,dict(c.attrs),None)
   p=attach(n,projected,'unbound/'+str(i),c);doc.unlinked_keys.add(p.get('this'))
 for guid,nodes in refs.items():
  if len(nodes)>1:
   issue('duplicate_reference','같은 GUID가 하이어라키에 여러 번 참조됩니다.',*nodes,*defs.get(guid,[]))
   # Leaf aliases can be split by explicitly copying their one definition.
   if len(defs.get(guid,[]))==1 and all(not n.children for n in nodes):
    doc.duplicate_repairs.extend((n,defs[guid][0]) for n in nodes[1:])
 for guid,nodes in defs.items():
  if len(nodes)>1:issue('duplicate_guid','서로 다른 컴포넌트 정의가 같은 GUID를 사용합니다.',*nodes,*refs.get(guid,[]))
 for c in doc.components:
  if not c.get('this'):issue('missing_guid','컴포넌트 this GUID가 없습니다.',c)
  if c.get('uniqueguid') and c.get('uniqueguid')!=c.get('this'):
   issue('identity_mismatch','컴포넌트 this와 uniqueguid가 다릅니다.',c)
 for parent in [hierarchy]+raw:
  sibling_names=defaultdict(list)
  for child in parent.children:
   keys=node_keys.get(child,[])
   definition=doc.by_guid.get(keys[0]) if keys else None
   # Compare actual component IDs, not the normalized XML tag alone.
   name=definition.get('id',definition.tag) if definition is not None else child.tag
   sibling_names[name].append(child)
  for ns in sibling_names.values():
   if len(ns)>1:issue('duplicate_name','중복된 컴포넌트 이름 오류: 같은 부모 아래에 같은 이름의 자식이 있습니다.',*ns,severity='warning' if len({n.tag for n in ns})==len(ns) else 'error')
 # Internal identity collisions and dangling state/image links have locations too.
 for c in doc.components:
  declarations=defaultdict(list)
  for n in c.descendants():
   if n.get('this'):declarations[n.get('this')].append(n)
  for ns in declarations.values():
   if len(ns)>1:issue('internal_duplicate','컴포넌트 내부에 중복된 GUID가 있습니다. 수동 확인이 필요합니다.',*ns)
  for n in c.descendants():
   for attr in ('currentstate','defaultstate','componentimage'):
    if n.get(attr) and n.get(attr) not in declarations:
     issue('dangling_reference','연결된 스테이트 또는 이미지 GUID를 해당 컴포넌트 안에서 찾을 수 없습니다.',n)
 for item in doc.issues:
  item.keys=tuple(dict.fromkeys(k for n in item.nodes for k in node_keys[n]))
  # Internal nodes inherit their owning component's annotation.
  if not item.keys:
   for n in item.nodes:
    while n is not None and n not in node_keys:n=n.parent
    if n is not None:item.keys+=tuple(node_keys[n])
  if item.keys and all(k in doc.unlinked_keys for k in item.keys):item.severity='info'
  for key in item.keys:
   doc.issues_by_key[key].append(item)
   if item.code in ('duplicate_reference','duplicate_guid','unresolved','missing_definition'):doc.unsafe_keys.add(key)
  for n in item.nodes:
   line=doc.source.count('\n',0,n.start)+1
   if item not in doc.issues_by_line[line]:doc.issues_by_line[line].append(item)
 # Don't offer a repair that assigns two IDs to the same definition.
 counts=defaultdict(int)
 for c,g in doc.guid_repairs:counts[c]+=1
 doc.guid_repairs=[(c,g) for c,g in doc.guid_repairs if counts[c]==1]

def repair_hierarchy_guids(doc):
 changes=[]
 for c,g in doc.guid_repairs:
  values={'this':g}
  if c.get('uniqueguid') is not None:values['uniqueguid']=g
  changes.append((c,values))
 return doc.patch(changes)

def repair_duplicate_guids(doc):
 """Split unambiguous leaf aliases, preserving scoped state/image identities.

 Duplicate definitions with a unique hierarchy/name match are resolved first.
 Unknown references aren't rewritten globally.
 """
 from model import Document, TAG, ATTR, attribute_value
 from layout_edit import node_end
 from state_edit import append_fragment
 source=repair_hierarchy_guids(doc);doc=Document(source)
 additions=[];changes=[]
 occupied={n.get(k) for n in doc.nodes for k in ('this','uniqueguid') if n.get(k)}
 for n,c in doc.duplicate_repairs:
  declarations={x.get(k) for x in c.descendants() for k in ('this','uniqueguid') if x.get(k)}
  mapping={}
  for old in declarations:
   fresh=str(uuid.uuid4()).upper()
   while fresh in occupied:fresh=str(uuid.uuid4()).upper()
   occupied.add(fresh);mapping[old]=fresh
  def token(m):
   if m[0].startswith(('<!--','<?','</')):return m[0]
   def attr(a):
    # Only known identity/reference attributes, never text/CCO strings.
    value=mapping.get(attribute_value(a[3])) if a[1] in ('this','uniqueguid','currentstate','defaultstate','componentimage') else None
    return a[0][:a.start(3)-a.start()]+value+a[0][a.end(3)-a.start():] if value else a[0]
   return ATTR.sub(attr,m[0])
  additions.append(TAG.sub(token,source[c.start:node_end(source,c)]))
  changes.append((n,{'this':mapping[c.get('this')]}))
 source=doc.patch(changes)
 if additions:
  changed=Document(source)
  source=append_fragment(source,changed.root.child('components'),'\n'.join(additions))
 Document(source)
 return source
