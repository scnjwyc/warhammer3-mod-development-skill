"""Finish one inspector field without applying the whole property dialog."""

def bind_completion(widget, owner):
    if getattr(widget, '_input_completion_managed', False):
        return
    kind = widget.winfo_class()
    if kind not in ('Entry','TEntry','TCombobox','Spinbox','TSpinbox','Text') and not hasattr(widget,'_edit_snapshot'):
        return
    widget._input_completion_managed = True
    def read():
        getter = getattr(widget, '_edit_snapshot', None)
        if getter is not None:return getter()
        return widget.get('1.0','end-1c') if kind=='Text' else widget.get()
    def restore(value):
        setter = getattr(widget, '_edit_restore', None)
        if setter is not None:
            setter(value);return
        if kind=='Text':
            widget.delete('1.0','end');widget.insert('1.0',value)
        else:
            variable = str(widget.cget('textvariable'))
            if variable:
                # Setting through Tcl preserves the variable's ownership and traces.
                widget.tk.globalsetvar(variable, value)
            else:
                widget.delete(0,'end');widget.insert(0,value)
    saved = [read()]
    insertwidth = widget.cget('insertwidth') if kind=='Text' else None
    def begin(event=None):
        if event is not None and getattr(widget,'_edit_skip_focus_once',False):
            widget._edit_skip_focus_once=False
            return
        saved[0] = read()
        if kind=='Text':widget.configure(insertwidth=insertwidth)
    def finish(event=None, cancel=False):
        if cancel:restore(saved[0])
        else:
            normalize = getattr(widget, '_edit_finish', None)
            if normalize is not None:normalize()
            saved[0] = read()
        if kind=='Text':
            widget.tag_remove('sel','1.0','end');widget.configure(insertwidth=0)
        elif hasattr(widget,'selection_clear'):widget.selection_clear()
        owner.focus_set()
        return 'break'
    widget._edit_begin=begin
    widget.bind('<FocusIn>',begin,add='+')
    widget.bind('<Return>',finish)
    widget.bind('<KP_Enter>',finish)
    widget.bind('<Escape>',lambda e:finish(e,True))
    if kind=='Text':
        # Keep an explicit way to add lines to CCO expressions.
        widget.bind('<Shift-Return>',lambda e:None)

def install_completion(owner):
    def visit(widget):
        bind_completion(widget,owner)
        for child in widget.winfo_children():visit(child)
    visit(owner)
