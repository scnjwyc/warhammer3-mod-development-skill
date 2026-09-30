"""Read-only template definitions, cached per original UI root until refresh."""
from pathlib import Path
import xml.etree.ElementTree as ET
from model import resource_root,Document

class TemplateIndex:
 def __init__(self,value):
  self.root=resource_root(value);self.entries={};self.errors=[];self.loaded=False;self.available=False
 def load(self):
  if self.loaded:return
  self.loaded=True
  folder=self.root/'templates' if self.root else None
  if folder and not folder.is_dir() and self.root.is_dir():
   folder=next((p for p in self.root.iterdir() if p.is_dir() and p.name.lower()=='templates'),folder)
  if folder is None or not folder.is_dir():return
  self.available=True
  for path in sorted(folder.rglob('*.xml')):
   try:
    root=ET.fromstring(path.read_bytes())
    for c in root.findall('./components/*'):
     for guid in set(filter(None,(c.get('this'),c.get('uniqueguid_in_template')))):
      self.entries.setdefault(guid,[]).append((path,c))
   except (OSError,ValueError,ET.ParseError) as error:self.errors.append((path,str(error)))
 def resolve(self,doc,key):
  self.load();c=doc.by_guid[key];matches=self.entries.get(c.get('uniqueguid_in_template'),[])
  # Prefer the template named by this component or its hierarchy ancestors.
  cursor=key;visited=set()
  while cursor and cursor not in visited:
   visited.add(cursor);node=doc.by_guid.get(cursor);name=node.get('template_id') if node else None
   if name:
    candidates=[m for m in matches if m[0].name==name+'.twui.xml' or m[0].stem==name]
    if candidates:matches=candidates;break
   cursor=doc.parents.get(cursor)
  if len(matches)==1:return matches[0]
  # Reused definitions can occur in multiple template files. Do not guess if
  # their attributes or children differ.
  if matches and len({ET.tostring(c,encoding='unicode') for _,c in matches})==1:return matches[0]
  return None

def template_index(app):
 value=app.settings.get('resource','');index=getattr(app,'template_index',None)
 if index is None or index.root!=resource_root(value):index=app.template_index=TemplateIndex(value)
 return index

def state_items(component):
 states=component.child('states')
 if states is not None:return states.children,False
 refs=component.child('state_uniqueguids')
 return (refs.children if refs is not None else []),refs is not None

def merge_template_texts(source,draft,initial,key):
 """Merge only edited text attributes, preserving other property-page edits."""
 base=Document(initial).by_guid[key];edit=Document(draft).by_guid[key];target=Document(source)
 def texts(c):
  group=c.child('localised_texts');return group.children if group is not None else []
 old,new,current=texts(base),texts(edit),texts(target.by_guid[key])
 if len(old)!=len(new) or len(old)!=len(current):raise ValueError('localised_texts structure changed; reopen properties.')
 patches=[]
 for a,b,c in zip(old,new,current):
  if a.get('state')!=b.get('state') or a.get('state')!=c.get('state'):raise ValueError('localised_texts state changed; reopen properties.')
  changes={k:b.attrs.get(k) for k in a.attrs.keys()|b.attrs.keys() if a.attrs.get(k)!=b.attrs.get(k)}
  if changes:patches.append((c,changes))
 return target.patch(patches)
