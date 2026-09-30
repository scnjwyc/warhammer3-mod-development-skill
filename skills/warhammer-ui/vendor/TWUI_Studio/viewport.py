def stable_region(previous,bounds,left,top,width,height):
 values=[(left-32,top-32,left+width+32,top+height+32)]
 if len(previous)==4:values.append(previous)
 if bounds:values.append((bounds[0]-32,bounds[1]-32,bounds[2]+64,bounds[3]+64))
 return (min(v[0] for v in values),min(v[1] for v in values),max(v[2] for v in values),max(v[3] for v in values))

def clipped_label(text,measure,limit):
 if limit<=0:return ''
 if measure(text)<=limit:return text
 while text and measure(text+'…')>limit:text=text[:-1]
 return text+'…' if measure(text+'…')<=limit else ''

def fit_zoom(width,height,box,fill=.72):
 return max(.02,min(8,max(1,width)*fill/max(1,box[2]),max(1,height)*fill/max(1,box[3])))

def grid_positions(start,length,zoom):
 import math
 step=24*zoom
 # Keep a legible major grid at extreme zoom-out; no fixed pixel grid.
 while step<6:step*=5
 first=math.floor((start-32)/step)
 return [32+i*step for i in range(first,math.ceil((start+length-32)/step)+1)]

def zoom_origin(left,top,width,height,old_zoom,new_zoom,box=None):
 """Preserve the selected world center, or the viewport center, on screen."""
 if box is None:
  sx,sy=width/2,height/2;wx=(left+sx-32)/old_zoom;wy=(top+sy-32)/old_zoom
 else:
  x,y,w,h=box;wx,wy=x+w/2,y+h/2;sx=32+wx*old_zoom-left;sy=32+wy*old_zoom-top
 return 32+wx*new_zoom-sx,32+wy*new_zoom-sy
