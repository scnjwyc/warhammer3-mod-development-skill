"""Linked degree/radian inputs. Display rounding never rewrites untouched XML."""
import math
import tkinter as tk
from tkinter import ttk

TAU_DISPLAY = float(f'{math.tau:.8f}')

def angle_value(text, unit):
    value = float(text)
    limit = 360 if unit == 'deg' else TAU_DISPLAY
    if not math.isfinite(value) or not 0 <= value <= limit:
        raise ValueError('Angle outside range')
    return math.radians(value) if unit == 'deg' else min(value, math.tau)

def angle_text(radians):
    return f'{math.degrees(radians):.5f}'.rstrip('0').rstrip('.') or '0', f'{radians:.8f}'

def mouse_degrees(x, y):
    return math.degrees(math.atan2(-y, x)) % 360

class AngleEditor(ttk.Frame):
    def __init__(self, parent, value, changed, travel):
        super().__init__(parent)
        self.changed = changed
        self.guard = False
        self.value = value
        try:
            radians = float(value)
            if not math.isfinite(radians):raise ValueError()
        except ValueError:radians = 0
        degree, radian = angle_text(radians)
        self.variables = {'deg': tk.StringVar(value=degree), 'rad': tk.StringVar(value=radian)}
        self.dial = tk.Canvas(self, width=44, height=44, highlightthickness=0, bg='#232830', takefocus=0)
        self.dial.pack(side='left', padx=(0,5))
        for unit, limit, increment, label in (('deg',360,1,'°'),('rad',TAU_DISPLAY,.01,'rad')):
            variable = self.variables[unit]
            def valid(text, u=unit):
                if text in ('','.'):return True
                try:angle_value(text,u);return True
                except ValueError:return False
            entry = ttk.Spinbox(self, from_=0, to=limit, increment=increment, textvariable=variable, width=10 if unit=='rad' else 7,
                                validate='key', validatecommand=(self.register(valid),'%P'))
            entry.pack(side='left', fill='x', expand=True)
            ttk.Label(self,text=label).pack(side='left',padx=(2,5))
            variable.trace_add('write',lambda *a,u=unit:self.edit(u))
            entry.bind('<FocusOut>',lambda e:self.refresh())
            entry._edit_snapshot=lambda:self.value
            entry._edit_restore=self.restore_value
            entry._edit_finish=self.refresh
            for seq,redo in (('<Control-z>',False),('<Control-y>',True),('<Control-Shift-Z>',True)):
                entry.bind(seq,lambda e,r=redo:travel(r))
        self.dial._edit_snapshot=lambda:self.value
        self.dial._edit_restore=self.restore_value
        self.dial._edit_finish=self.refresh
        self.dial.bind('<Button-1>',self.drag)
        self.dial.bind('<B1-Motion>',self.drag)
        self.paint(radians)
    def paint(self, radians):
        c=self.dial;c.delete('all')
        c.create_oval(4,4,40,40,outline='#b5cadd')
        c.create_line(22,22,43,22,fill='#808080',width=2,tags=('zero_reference',))
        c.create_line(22,22,22+17*math.cos(radians),22-17*math.sin(radians),fill='#ff8cbd',width=2,arrow='last')
    def edit(self,unit):
        if self.guard:return
        try:radians=angle_value(self.variables[unit].get(),unit)
        except ValueError:return
        self.value=repr(radians)
        degree,radian=angle_text(radians)
        self.guard=True
        try:self.variables['rad' if unit=='deg' else 'deg'].set(radian if unit=='deg' else degree)
        finally:self.guard=False
        self.paint(radians);self.changed(self.value)
    def refresh(self):
        try:radians=float(self.value);degree,radian=angle_text(radians)
        except ValueError:return
        self.guard=True
        try:
            self.variables['deg'].set(degree);self.variables['rad'].set(radian)
        finally:self.guard=False
    def restore_value(self,value):
        self.value=value
        self.refresh()
        try:self.paint(float(value))
        except ValueError:pass
        self.changed(value)
    def drag(self,event):
        if abs(event.x-22)+abs(event.y-22)<2:return 'break'
        if self.focus_get() is not self.dial:
            if hasattr(self.dial,'_edit_begin'):self.dial._edit_begin()
            self.dial._edit_skip_focus_once=True
            self.dial.focus_set()
        self.variables['deg'].set(f'{mouse_degrees(event.x-22,event.y-22):.2f}')
        return 'break'
