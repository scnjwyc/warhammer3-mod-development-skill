import re,textwrap

class History:
 def __init__(self,value):self.current=value;self.past=[];self.future=[]
 def record(self,value):
  if value!=self.current:self.past.append(self.current);self.current=value;self.future.clear()
 def undo(self):
  if self.past:self.future.append(self.current);self.current=self.past.pop()
  return self.current
 def redo(self):
  if self.future:self.past.append(self.current);self.current=self.future.pop()
  return self.current

def bind_entry_history(widget,variable):
 history=History(variable.get());busy=[False]
 def record(*args):
  if not busy[0]:
   history.record(variable.get());widget.winfo_toplevel().last_history=travel
 trace=variable.trace_add('write',record)
 def travel(redo=False):
  if not (history.future if redo else history.past):return 'break'
  busy[0]=True
  try:variable.set(history.redo() if redo else history.undo());widget.icursor('end')
  finally:busy[0]=False
  return 'break'
 widget.bind('<Control-z>',lambda e:travel());widget.bind('<Control-Shift-Z>',lambda e:travel(True));widget.bind('<Control-y>',lambda e:travel(True))
 return history

def expression_display(raw):
 return textwrap.dedent(raw.replace('\r\n','\n').strip('\r\n')).strip()

def expression_value(raw,edited,source,node):
 if edited==expression_display(raw):return raw
 edited=edited.replace('\r\n','\n')
 if '\n' not in edited:return edited
 newline='\r\n' if '\r\n' in source else '\n'
 token=source[node.start:node.end]
 match=re.search(r'\n([ \t]*)context_function_id\s*=',token)
 if match:indent=match[1]
 else:indent=re.match(r'[ \t]*',source[source.rfind('\n',0,node.start)+1:node.start])[0]+'\t'
 unit='\t' if '\t' in indent else '    '
 return newline+newline.join(indent+unit+line for line in edited.split('\n'))+newline+indent
