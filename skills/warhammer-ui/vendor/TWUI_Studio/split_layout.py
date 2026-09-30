"""Three stable columns; move a divider guide, commit geometry on release."""
import tkinter as tk

def constrained_positions(width,left,xml_width):
    width=max(1,width)
    # Main window minimum is 1000; fractions also make initial tiny layouts safe.
    left_min=min(220,width*.22)
    center_min=min(180,width*.18)
    xml_min=min(260,width*.26)
    right=max(width/2,width-max(xml_min,xml_width))
    right=min(width-xml_min,right)
    left=max(left_min,min(left,right-center_min))
    return round(left),round(right)

class StableColumns(tk.Frame):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,bd=0,highlightthickness=0)
        self.panes=[];self.handles=[];self.left=300;self.xml_width=440;self.positions=(300,1000)
        self.pending=None;self.dragging=None;self.guide=None
        self.bind('<Configure>',self.schedule)
    def add(self,pane,weight=0):
        self.panes.append(pane)
        if len(self.panes)>1:
            index=len(self.handles)
            handle=tk.Frame(self,bg='#a5a5a5',cursor='sb_h_double_arrow',width=6)
            handle.bind('<ButtonPress-1>',lambda e,i=index:self.start(e,i))
            handle.bind('<B1-Motion>',self.move)
            handle.bind('<ButtonRelease-1>',self.release)
            self.handles.append(handle)
        self.schedule()
    def schedule(self,event=None):
        if self.pending is None:self.pending=self.after_idle(self.layout)
    def layout(self):
        self.pending=None
        if len(self.panes)!=3:return
        w=self.winfo_width();h=self.winfo_height()
        a,b=constrained_positions(w,self.left,self.xml_width);self.positions=(a,b)
        for pane,x,end in zip(self.panes,(0,a+6,b+6),(a,b,w)):
            pane.place(x=x,y=0,width=max(1,end-x),height=h)
        for handle,x in zip(self.handles,(a,b)):handle.place(x=x,y=0,width=6,height=h);handle.lift()
    def sashpos(self,index,newpos=None):
        if newpos is not None:
            if index==0:self.left=newpos
            else:self.xml_width=self.winfo_width()-newpos
            self.layout()
        return self.positions[index]
    def start(self,event,index):
        self.dragging=index
        self.guide=tk.Frame(self,bg='#247b91',width=4)
        self.move(event)
    def move(self,event):
        if self.dragging is None:return
        x=event.x_root-self.winfo_rootx();w=self.winfo_width()
        a,b=constrained_positions(w,x if self.dragging==0 else self.left,w-x if self.dragging==1 else self.xml_width)
        self.target=(a,b)[self.dragging]
        self.guide.place(x=self.target,y=0,width=4,relheight=1);self.guide.lift()
    def release(self,event):
        if self.dragging is None:return
        self.move(event)
        index=self.dragging;self.dragging=None;self.guide.destroy();self.guide=None
        self.sashpos(index,self.target)
