from i18n import tr, trf
from model import Document
HISTORY_LIMIT=20
class TabHistory:
 def action_state(self):
  return dict(xml=self.doc.source,locks=set(self.locks),hidden=set(self.hidden),focus=self.focus_guid,root_lock=self.root_lock.get(),selected=self.selected)
 def refresh_history(self):
  panel=getattr(self,'history_panel',None)
  if panel is not None:panel.refresh()
 def record_action(self,before,label=None):
  after=self.action_state()
  if before==after:return
  if before['xml']!=after['xml'] and 0<=getattr(self,'active_document',-1)<len(getattr(self,'documents',[])):
   self.documents[self.active_document]['ever_edited']=True
  if label is None:
   if before['xml']!=after['xml']:label=tr('XML 편집')
   elif before['locks']!=after['locks'] or before['root_lock']!=after['root_lock']:label=tr('잠금 변경')
   elif before['focus']!=after['focus']:label=tr('선택만 보기') if after['focus'] else tr('전체 보기')
   else:label=tr('표시 / 숨김 변경')
  self.undo_stack.append({**before,'_label':label});del self.undo_stack[:-HISTORY_LIMIT];self.redo_stack.clear();self.refresh_history()
 def history_travel(self,redo=False,redraw=True):
  stack=self.redo_stack if redo else self.undo_stack
  if not stack:return 'break'
  current=self.action_state();state=stack.pop()
  if isinstance(state,str):state={**current,'xml':state}
  current['_label']=state.get('_label',tr('XML 편집'));(self.undo_stack if redo else self.redo_stack).append(current)
  self.doc=Document(state['xml']);self.locks=set(state['locks']);self.hidden=set(state['hidden']);self.focus_guid=state['focus'];self.root_lock.set(state['root_lock']);self.selected=state['selected'];self.dirty=self.doc.source!=self.saved_source;self.drag=None
  if redraw:self.rebuild();self.refresh_history()
  return 'break'
 def history_jump(self,index):
  if not 0<=index<=len(self.undo_stack)+len(self.redo_stack) or index==len(self.undo_stack):return
  # Properties drafts must not be applied to a different historical document.
  if hasattr(self,'document_switch_allowed') and not self.document_switch_allowed():return
  while len(self.undo_stack)!=index:self.history_travel(redo=len(self.undo_stack)<index,redraw=False)
  self.rebuild();self.refresh_history()
