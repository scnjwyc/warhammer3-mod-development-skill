"""Approximate TWUI layout and image rendering, independent from the window."""
from PIL import Image
from model import number,pair

def dimensions(doc,g,hidden,cache):
 if g in cache:return cache[g]
 c=doc.by_guid.get(g)
 if c is None or g in hidden:return (0,0)
 s=doc.state(c);t=s.child('component_text') if s else None
 base=pair(c.get('dimensions'),(100,number(t.get('font_m_size'),12)+10 if t else 26))
 w=number(s.get('width') if s else None,base[0]);h=number(s.get('height') if s else None,base[1])
 layout=c.child('LayoutEngine')
 if layout is not None and layout.get('type') in ('List','HorizontalList') and layout.get('sizetocontent')=='true':
  from layout_geometry import list_positions
  children=[v for v in doc.children.get(g,[]) if v not in hidden]
  sizes={v:dimensions(doc,v,hidden,cache) for v in children}
  _,content=list_positions(layout,children,sizes)
  minimum=pair(layout.get('min_dimensions'))
  w=max(content[0],minimum[0]);h=max(content[1],minimum[1])
 cache[g]=(w,h);return w,h

def _raster(asset,width,height,metrics):
 """Render fixed edges and repeat/stretch middle. Margin interpretation is provisional."""
 im=Image.open(asset).convert('RGBA');width=max(1,min(4096,int(width)));height=max(1,min(4096,int(height)))
 margin=pair(metrics.get('margin'),(0,0,0,0))
 def fill(patch,size,tile=False):
  w,h=size
  if w<=0 or h<=0:return None
  if patch.width==0 or patch.height==0:return Image.new('RGBA',size)
  if not tile:return patch.resize(size,Image.Resampling.LANCZOS)
  out=Image.new('RGBA',size)
  for y in range(0,h,max(1,patch.height)):
   for x in range(0,w,max(1,patch.width)):out.paste(patch,(x,y))
  return out
 if len(margin)==4 and any(margin):
  top,right,bottom,left=[max(0,round(v)) for v in margin]
  left=min(left,im.width//2);right=min(right,im.width-left);top=min(top,im.height//2);bottom=min(bottom,im.height-top)
  dl=min(left,width//2);dr=min(right,width-dl);dt=min(top,height//2);db=min(bottom,height-dt)
  sx=[0,left,im.width-right,im.width];sy=[0,top,im.height-bottom,im.height];dx=[0,dl,width-dr,width];dy=[0,dt,height-db,height]
  out=Image.new('RGBA',(width,height))
  for row in range(3):
   for col in range(3):
    patch=fill(im.crop((sx[col],sy[row],sx[col+1],sy[row+1])),(dx[col+1]-dx[col],dy[row+1]-dy[row]),metrics.get('tile')=='true' and (row==1 or col==1))
    if patch is not None:out.paste(patch,(dx[col],dy[row]))
 else:out=fill(im,(width,height),metrics.get('tile')=='true')
 color=metrics.get('colour','#FFFFFFFF').lstrip('#')
 if len(color)==8:
  try:
   factors=[int(color[i:i+2],16)/255 for i in range(0,8,2)]
   out=Image.merge('RGBA',tuple(ch.point([round(v*f) for v in range(256)]) for ch,f in zip(out.split(),factors)))
  except ValueError:pass
 return out

# Bounded decoded-image cache shared by original and edited render passes.
from collections import OrderedDict
_cache=OrderedDict()
_cache_bytes=0
def raster(asset,width,height,metrics):
 global _cache_bytes
 stat=asset.stat()
 key=(str(asset),stat.st_mtime_ns,stat.st_size,int(width),int(height),tuple(sorted(metrics.attrs.items())))
 if key in _cache:
  _cache.move_to_end(key);return _cache[key]
 im=_raster(asset,width,height,metrics);size=im.width*im.height*4
 if size<=64*1024*1024:
  while _cache and _cache_bytes+size>64*1024*1024:
   _,old=_cache.popitem(last=False);_cache_bytes-=old.width*old.height*4
  _cache[key]=im;_cache_bytes+=size
 return im

class ZoomImageCache:
 """Share zoomed Tk images across canvases; keep a bounded LRU between draws."""
 def __init__(self,limit=64*1024*1024):
  self.limit=limit;self.bytes=0;self.cache=OrderedDict();self.frame={}
 def begin(self):self.frame={}
 def end(self):self.frame={}
 def photo(self,asset,width,height,metrics,size,master,crop=None):
  from PIL import ImageTk
  stat=asset.stat()
  appearance=tuple((k,metrics.get(k)) for k in ('margin','tile','colour'))
  key=(str(asset),stat.st_mtime_ns,stat.st_size,int(width),int(height),appearance,size,crop)
  if key in self.frame:return self.frame[key]
  if key in self.cache:
   self.cache.move_to_end(key);photo=self.cache[key][0]
  else:
   im=raster(asset,width,height,metrics)
   # Always scale the cached base raster; no progressive quality refinement.
   if crop is not None:
    l,t,r,b=crop;source_box=(l*im.width/size[0],t*im.height/size[1],r*im.width/size[0],b*im.height/size[1])
    im=im.resize((r-l,b-t),Image.Resampling.NEAREST,box=source_box)
   elif im.size!=size:im=im.resize(size,Image.Resampling.NEAREST)
   photo=ImageTk.PhotoImage(im,master=master);cost=im.width*im.height*4
   if cost<=self.limit:
    while self.cache and self.bytes+cost>self.limit:
     _,(_,old_cost)=self.cache.popitem(last=False);self.bytes-=old_cost
    self.cache[key]=(photo,cost);self.bytes+=cost
  self.frame[key]=photo
  return photo


def visible_crop(x,y,size,view):
 """Integer crop in the final bitmap; retain source placement and full extent."""
 import math
 l,t,r,b=view;w,h=size
 left=max(0,math.floor(l-x));top=max(0,math.floor(t-y))
 right=min(w,math.ceil(r-x));bottom=min(h,math.ceil(b-y))
 return (left,top,right,bottom) if right>left and bottom>top else None
