"""Editor visibility never changes component geometry."""
def top_targets(doc,selected):
 chosen=set(selected);result=[]
 for g in selected:
  parent=doc.parents.get(g)
  while parent and parent not in chosen:parent=doc.parents.get(parent)
  if parent is None and g not in result:result.append(g)
 return result

def descendants(doc,roots):
 result=set();pending=list(roots)
 while pending:
  g=pending.pop()
  if g in result:continue
  result.add(g);pending.extend(doc.children.get(g,[]))
 return result

def focus_set(focus):return set(focus if isinstance(focus,(list,tuple,set)) else [focus]) if focus else set()

def shown(doc,g,hidden,focus):
 isolated=focus_set(focus)
 if focus is not None:return g in isolated and g not in hidden
 while g:
  if g in hidden:return False
  g=doc.parents.get(g)
 return True

def toggle_roots(hidden,roots):
 result=set(hidden)
 # Mixed selection becomes hidden as a group; next click restores root flags.
 if all(g in result for g in roots):result.difference_update(roots)
 else:result.update(roots)
 return result

class ViewActions:
 def selected_group_members(self):
  from hierarchy_edit import NO_PARENT
  rows=self.tree.selection() or [self.selected]
  return set(getattr(self.doc,'unlinked_keys',set())) if NO_PARENT in rows else set()
 def selected_guids(self,expand_groups=False):
  rows=self.tree.selection()
  selected=[g for g in rows if g in self.doc.by_guid]
  if expand_groups:selected.extend(sorted(self.selected_group_members()-set(selected)))
  # A selected empty group must never fall back to the previous component.
  return selected if rows else selected or ([self.selected] if self.selected in self.doc.by_guid else [])
 def view_action(self,action):
  if not self.doc:return
  selected=self.selected_guids(expand_groups=True)
  if not selected and action not in ('all_show','all_hide'):return
  targets=top_targets(self.doc,selected);before=self.action_state()
  if action=='only':
   visible=descendants(self.doc,targets)
   self.focus_guid=sorted(visible) or None;self.hidden.difference_update(visible)
  elif action=='exact':
   self.focus_guid=sorted(set(selected));self.hidden.difference_update(selected)
  elif action=='all_show':self.focus_guid=None;self.hidden.clear()
  elif action=='all_hide':self.focus_guid=None;self.hidden=set(self.doc.by_guid)
  elif action in ('children_show','children_hide'):
   children=(descendants(self.doc,targets)-set(targets)) | self.selected_group_members()
   if action=='children_show':self.hidden.difference_update(children)
   else:self.hidden.update(children)
   self.focus_guid=None
  elif action=='toggle' and targets:
   if self.focus_guid is not None:
    visible=focus_set(self.focus_guid);subtree=descendants(self.doc,targets)
    if all(shown(self.doc,g,self.hidden,self.focus_guid) for g in targets):
     visible.difference_update(subtree);self.hidden.update(targets)
    else:
     visible.update(subtree);self.hidden.difference_update(subtree)
    # An empty explicit view must not fall back to displaying the whole document.
    self.focus_guid=sorted(visible)
   else:self.hidden=toggle_roots(self.hidden,targets)
  self.record_action(before);self.tree_states();self.draw()
