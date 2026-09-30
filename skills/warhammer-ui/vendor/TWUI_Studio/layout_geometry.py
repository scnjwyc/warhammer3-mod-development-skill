"""Shared canvas layout: local docking and row/column list placement."""
from model import pair,number

def component_format(component):
 # Only classify observed, unambiguous XML shapes. Missing/mixed states remain editable.
 child=getattr(component,'child',lambda name:None)
 states=child('states') is not None;refs=child('state_uniqueguids') is not None
 if refs and not states and (component.get('part_of_template') or '').lower()=='true':return 'template'
 if states and not refs and (component.get('part_of_template') or '').lower()!='true':return 'definition'
 return 'unknown'

def docking_key(component):
 kind=component_format(component)
 if kind=='template':return 'dock_point'
 if kind=='definition':return 'docking'
 return 'dock_point' if component.get('dock_point') else 'docking'

def position_offset_key(component):
 return 'dock_offset' if docking_key(component)=='docking' and component.get('docking') else 'offset'

def unsupported_docking_options(component):
 kind=component_format(component)
 return {'docking','dock_offset','component_anchor_point'} if kind=='template' else {'dock_point'} if kind=='definition' else set()

def docking_value(component):
 return (component.get(docking_key(component)) or '').replace('_',' ').strip().lower()

def docking_anchor(component):
 dock=docking_value(component);external='external' in dock
 x=1. if 'right' in dock else 0. if 'left' in dock else .5
 y=1. if 'bottom' in dock else 0. if 'top' in dock else .5
 if external:
  # Center Left/Right external sits beside the parent; Top/Bottom sits outside vertically.
  if x!=.5:x=1-x
  if y!=.5:y=1-y
 return (x,y) if docking_key(component)=='dock_point' else pair(component.get('component_anchor_point'),(x,y))

def component_position(component,size,parent_size):
 dock=docking_value(component)
 if not dock:return pair(component.get('offset'))
 w,h=size;pw,ph=parent_size;ax,ay=docking_anchor(component)
 dx,dy=pair(component.get(position_offset_key(component)))
 x=pw if 'right' in dock else 0 if 'left' in dock else pw/2
 y=ph if 'bottom' in dock else 0 if 'top' in dock else ph/2
 return x+dx-ax*w,y+dy-ay*h

def list_positions(layout,children,sizes,container=(0,0)):
 kind=layout.get('type')
 if kind not in ('List','HorizontalList'):return {},container
 order=list(reversed(children)) if layout.get('reverse_order')=='true' else list(children)
 margin=pair(layout.get('margins'));secondary=pair(layout.get('secondary_margins'));spacing=pair(layout.get('spacing'))
 cols=max(1,int(number(layout.get('itemsperrow'),1))) if kind=='List' else max(1,len(order))
 columns=layout.child('columnwidths');widths=[number(n.get('width')) for n in columns.children] if columns else []
 # A wrapping list uses child bounds plus spacing, not a repeated fixed column slot.
 if kind=='List' and cols>1:widths=[]
 left=secondary[0] if kind=='List' else margin[0];top=margin[0] if kind=='List' else secondary[0]
 right=secondary[1] if kind=='List' else margin[1];bottom=margin[1] if kind=='List' else secondary[1]
 rows=[order[i:i+cols] for i in range(0,len(order),cols)];positions={};y=top;maxright=left
 for row in rows:
  cells=[max(sizes[g][0],widths[i%len(widths)] if widths else 0) for i,g in enumerate(row)]
  rowwidth=sum(cells)+max(0,len(row)-1)*spacing[0]
  available=max(container[0]-left-right,rowwidth)
  alignment=layout.get('horizontal_alignment');x=left+(available-rowwidth)*(.5 if alignment=='Center' else 1 if alignment=='Right' else 0)
  for g,cell in zip(row,cells):positions[g]=(x,y);x+=cell+spacing[0]
  maxright=max(maxright,left+rowwidth);y+=max((sizes[g][1] for g in row),default=0)+spacing[1]
 height=y-(spacing[1] if rows else 0)+bottom
 return positions,(maxright+right,height)
