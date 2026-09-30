"""Local wheel routing: never propagate one wheel event to two scroll areas."""
def wheel_units(event):
 num=getattr(event,'num',None)
 if num in (4,5):return -3 if num==4 else 3
 delta=getattr(event,'delta',0)
 if not delta:return 0
 return (-1 if delta>0 else 1)*max(1,abs(int(delta))//120)*3

def install_scrolling(owner):
 def route(e):
  steps=wheel_units(e)
  if not steps:return 'break'
  widget=e.widget
  # Focused text boxes and candidate lists keep their own scrolling, even at their edges.
  target=getattr(widget,'_wheel_target',None)
  if target is None and widget.winfo_class() in ('Listbox','Treeview'):target=widget
  if target is None and widget.winfo_class()=='Text' and owner.focus_get()==widget:target=widget
  if target is None:
   choice=getattr(owner,'active_choice',None)
   if choice and choice.list_area.winfo_manager() and widget in (choice.entry,choice.arrow):target=choice.box
  if target is None:target=owner.canvas
  first,last=map(float,target.yview())
  if (steps<0 and first<=0) or (steps>0 and last>=1):return 'break'
  target.yview_scroll(steps,'units');return 'break'
 def visit(widget):
  for seq in ('<MouseWheel>','<Button-4>','<Button-5>'):widget.bind(seq,route)
  for child in widget.winfo_children():visit(child)
 visit(owner)
 # Actual wheel events stop at the widget binding; no bind_all or global side effects.

 from input_completion import install_completion
 install_completion(owner)
