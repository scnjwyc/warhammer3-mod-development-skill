"""Small native tree icons: folder, XML document and image."""
import tkinter as tk

def file_kind(path):
 if path.is_dir():return 'folder'
 return 'xml' if path.suffix.lower()=='.xml' else 'image'

def make_icons(master):
 result={}
 for kind,color in [('folder','#d99b35'),('xml','#9d66bb'),('image','#777ac6')]:
  icon=tk.PhotoImage(master=master,width=16,height=16)
  if kind=='folder':
   icon.put(color,to=(1,5,15,14));icon.put(color,to=(2,3,8,5));icon.put('#f3ce77',to=(2,6,14,12))
  else:
   icon.put(color,to=(2,1,14,15));icon.put('#f4f1f6',to=(3,2,13,14))
   if kind=='xml':
    for x,y in [(5,6),(4,7),(5,8),(10,6),(11,7),(10,8),(8,5),(7,9)]:icon.put(color,(x,y))
   else:
    icon.put(color,to=(5,4,7,6))
    for y in range(8,12):icon.put(color,to=(4,y,8+(y-8),y+1))
  result[kind]=icon
 return result
