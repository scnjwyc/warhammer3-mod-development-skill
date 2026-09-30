from i18n import tr, trf
from decimal import Decimal,ROUND_DOWN,InvalidOperation
from model import pair

def alt_pressed(state,backend,key_state=None):
 if backend=='win32':
  if key_state is None:
   import ctypes
   key_state=ctypes.windll.user32.GetKeyState(0x12)
  return bool(key_state & 0x8000)
 return bool(state & 8)

def parent_layout(doc,guid):
 parent=doc.by_guid.get(doc.parents.get(guid))
 return parent.child('LayoutEngine') if parent is not None else None

def fixed2(value):
 try:d=Decimal(str(value))
 except InvalidOperation:raise ValueError(tr('숫자를 입력하세요.'))
 if not d.is_finite():raise ValueError(tr('유한한 숫자를 입력하세요.'))
 try:d=d.quantize(Decimal('.01'),rounding=ROUND_DOWN)
 except InvalidOperation:raise ValueError(tr('숫자 범위가 너무 큽니다.'))
 return format(abs(d) if d==0 else d,'.2f')

def points(box):
 x,y,w,h=box
 return {(i,j):(x+w*i/2,y+h*j/2) for j in range(3) for i in range(3)}

def resized(box,handle,dx,dy,alt=False,shift=False,allow_x=True,allow_y=True):
 x,y,w,h=box;i,j=handle
 if handle==(1,1):return x+dx,y+dy,w,h
 sx=i-1;sy=j-1
 if not allow_x:sx=0
 if not allow_y:sy=0
 if shift and sx and sy:
  if abs(dx)>=abs(dy):sy=0
  else:sx=0
 nw=max(1,w+sx*dx*(2 if alt else 1));nh=max(1,h+sy*dy*(2 if alt else 1))
 nx=x-(nw-w)/2 if alt else x-(nw-w) if sx<0 else x
 ny=y-(nh-h)/2 if alt else y-(nh-h) if sy<0 else y
 return nx,ny,nw,nh

def offset_delta(component,before,after):
 x,y,w,h=before;nx,ny,nw,nh=after
 from layout_geometry import docking_anchor,docking_value
 ax,ay=docking_anchor(component) if docking_value(component) else (0,0)
 return nx-x+ax*(nw-w),ny-y+ay*(nh-h)

class TransformTools:
 def handle_at(self,e):
  if self.selected not in self.boxes or self.is_locked(self.selected):return None
  x,y=self.canvas.canvasx(e.x),self.canvas.canvasy(e.y)
  ps=points(self.boxes[self.selected]);z=self.zoom
  matches=[(abs(x-32-px*z)+abs(y-32-py*z),key) for key,(px,py) in ps.items() if abs(x-32-px*z)<=6 and abs(y-32-py*z)<=6]
  return min(matches)[1] if matches else None
 def transform_hover(self,e):
  if getattr(self,'drag',None):return
  handle=self.handle_at(e);cursor=''
  if handle is not None:
   i,j=handle;c=self.doc.by_guid[self.selected]
   ax=c.get('allowhorizontalresize')!='false';ay=c.get('allowverticalresize')!='false'
   if handle==(1,1):cursor='fleur'
   elif (i==1 or not ax) and (j==1 or not ay):cursor='X_cursor'
   elif i==1 or not ax:cursor='sb_v_double_arrow'
   elif j==1 or not ay:cursor='sb_h_double_arrow'
   else:cursor='size_nw_se' if i==j else 'size_ne_sw'
  try:self.canvas.configure(cursor=cursor)
  except Exception:self.canvas.configure(cursor='crosshair')
 def paint_transform(self,a,b,c,d):
  node=self.doc.by_guid[self.selected];ax=node.get('allowhorizontalresize')!='false';ay=node.get('allowverticalresize')!='false'
  for coords,allowed in [((a,b,c,b),ay),((a,d,c,d),ay),((a,b,a,d),ax),((c,b,c,d),ax)]:self.canvas.create_line(*coords,fill='#5ee0c0' if allowed else '#888888',width=2)
  for (i,j),(px,py) in points((a,b,c-a,d-b)).items():
   allowed=(i==1 and j==1) or (i!=1 and ax) or (j!=1 and ay)
   self.canvas.create_rectangle(px-4,py-4,px+4,py+4,fill='#c9e9ff' if allowed else '#777777',outline='#3575b4')
  layout=parent_layout(self.doc,self.selected)
  if layout is not None:
   content='parent LayoutEngine\n'+'\n'.join(f'{k}: {v}' for k,v in layout.attrs.items())
   tag=self.canvas.create_text(a-10,b-24,anchor='se',text=content,font=('Arial',8),fill='#ffcee1',tags=('parent_layout',))
   bounds=self.canvas.bbox(tag)
   if bounds:
    x1,y1,x2,y2=bounds
    bg=self.canvas.create_rectangle(x1-5,y1-4,x2+5,y2+4,fill='#50333f',outline='#e39ab8',tags=('parent_layout',));self.canvas.tag_lower(bg,tag)
  labels=[]
  for key in ('docking','dock_point'):
   if node.get(key):labels.append(key+': '+node.get(key))
  if node.get('docking') and not node.get('dock_point'):labels.append('dock_offset: '+node.get('dock_offset','0,0'))
  for k in ('allowverticalresize','allowhorizontalresize'):
   if node.get(k)=='false':labels.append(k+': false')
  import tkinter.font as tkfont
  font=tkfont.Font(family='Arial',size=8);self.option_tag_font=font
  yy=b+7;limit=max(0,c-a-16)
  for label in labels:
   if yy+14>d-6:break
   while label and font.measure(label)>limit:label=label[:-1]
   if not label:continue
   self.canvas.create_rectangle(a+6,yy,a+10+font.measure(label),yy+14,fill='#584d24',outline='')
   self.canvas.create_text(a+8,yy,anchor='nw',text=label,font=font,fill='#ffe49a');yy+=15
