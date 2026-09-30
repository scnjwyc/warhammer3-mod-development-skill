from i18n import tr, trf
"""Read-only XML sidebar with visible-line highlighting and source synchronization."""
import re
import tkinter as tk
from tkinter import ttk

def source_index(source, offset):
    """Convert original CRLF/LF source offsets to Tk line.column indices."""
    line = source.count('\n', 0, offset) + 1
    column = offset - (source.rfind('\n', 0, offset) + 1)
    return f'{line}.{column}'

class XMLViewer(ttk.Frame):
    def __init__(self, parent, format_command=None):
        super().__init__(parent, width=430, padding=(5, 0, 0, 0))
        self.source = None
        self.issue_lines = {}
        from diagnostics_ui import HoverNote, issue_text
        self._issue_text = issue_text
        self.job = None
        self.last_paint = None
        header = ttk.Frame(self, padding=5)
        header.pack(fill='x')
        ttk.Label(header, text=tr('XML 코드 · 읽기 전용'), font=('', 11, 'bold')).pack(side='left')
        ttk.Button(header, text=tr('전체 복사'), command=self.copy_all).pack(side='right')
        ttk.Button(header, text=tr('XML 정렬'), command=format_command).pack(side='right', padx=4)
        search = ttk.Frame(self, padding=(5, 0, 5, 5))
        search.pack(fill='x')
        self.query = tk.StringVar()
        entry = ttk.Entry(search, textvariable=self.query)
        entry.pack(side='left', fill='x', expand=True)
        entry.bind('<Return>', lambda e: self.find())
        entry.bind('<Shift-Return>', lambda e: self.find(True))
        self.case_sensitive=tk.BooleanVar(value=False)
        for label,command in [('↑',lambda:self.find(True)),('↓',self.find)]:
            ttk.Button(search,text=label,width=3,command=command).pack(side='left',padx=(4,0))
        ttk.Checkbutton(search,text='Aa',width=3,style='Toolbutton',variable=self.case_sensitive,command=self.reset_search).pack(side='left',padx=(4,0))
        self.query.trace_add('write',lambda *args:self.reset_search())
        area = ttk.Frame(self)
        area.pack(fill='both', expand=True)
        area.columnconfigure(1, weight=1)
        area.rowconfigure(0, weight=1)
        self.gutter = tk.Canvas(area, width=55, bg='#20242c', highlightthickness=0)
        self.gutter.grid(row=0, column=0, sticky='ns')
        self.warning_hover = HoverNote(self.gutter, lambda e:self._issue_text(self.issue_lines.get(int(self.text.index(f'@0,{e.y}').split('.')[0]), [])))
        self.text = tk.Text(area, width=45, wrap='none', bg='#20242c', fg='#d5dce8',
                            insertbackground='white', selectbackground='#2676c9', selectforeground='#ffffff', inactiveselectbackground='#2676c9',
                            font=('Consolas', 10), relief='flat', padx=6, pady=4,
                            tabs=('32p',), state='disabled', exportselection=False)
        self.text.grid(row=0, column=1, sticky='nsew')
        self.vbar = ttk.Scrollbar(area, orient='vertical', command=self.text.yview)
        self.vbar.grid(row=0, column=2, sticky='ns')
        hbar = ttk.Scrollbar(area, orient='horizontal', command=self.text.xview)
        hbar.grid(row=1, column=1, sticky='ew')
        self.text.configure(yscrollcommand=self.scrolled, xscrollcommand=hbar.set)
        for tag, color in [('xmltag','#77c4ff'),('attribute','#95d6aa'),('value','#e8bb83'),('comment','#82918a')]:
            self.text.tag_configure(tag, foreground=color)
        self.text.tag_configure('component', background='#314d4b')
        self.text.tag_configure('match', background='#866524', foreground='white')
        self.text.tag_raise('sel')
        self.text.bind('<Button-1>',lambda e:self.text.focus_set(),add='+')
        self.text.bind('<Configure>', self.schedule)
        self.text.bind('<Control-a>', self.select_all)
        self.text.bind('<Control-A>', self.select_all)
        self.text.bind('<Control-c>', self.copy_selection)
        self.text.bind('<Control-C>', self.copy_selection)
        self.info = tk.StringVar(value=tr('XML을 열면 현재 코드가 표시됩니다.'))
        ttk.Label(self, textvariable=self.info, padding=5).pack(fill='x')

    def scrolled(self, first, last):
        self.vbar.set(first, last)
        self.schedule()

    def schedule(self, event=None):
        if self.job is None:
            self.job = self.after(40,self.paint)

    def paint(self):
        self.job = None
        signature=(self.source,self.text.index('@0,0'),self.text.winfo_height(),self.text.winfo_width(),self.text.yview())
        if signature == self.last_paint:return
        self.last_paint=signature
        self.gutter.delete('all')
        index = self.text.index('@0,0')
        while True:
            box = self.text.dlineinfo(index)
            if box is None: break
            self.gutter.create_text(47, box[1], anchor='ne', text=index.split('.')[0],
                                    fill='#7d889a', font=('Consolas', 10))
            if int(index.split('.')[0]) in self.issue_lines:
                y=box[1]+2
                from diagnostics import marker_kind, SEVERITY_COLORS
                kind=marker_kind(self.issue_lines[int(index.split('.')[0])])
                if kind=='missing':
                    self.gutter.create_text(7,y+6,text='?',fill='#ec4d55',font=('',11,'bold'))
                else:
                    self.gutter.create_polygon(7,y,1,y+11,13,y+11,fill=SEVERITY_COLORS[kind],outline='')
                    self.gutter.create_text(7,y+7,text='!',fill='white',font=('',8,'bold'))
            next_index = self.text.index(index + '+1line')
            if self.text.compare(next_index, '<=', index): break
            index = next_index
        start = self.text.index('@0,0 linestart')
        end = self.text.index(f'@0,{self.text.winfo_height()} lineend +1c')
        fragment = self.text.get(start, end)
        patterns = [('xmltag',r'</?[\w:.-]+|/?>'),
                    ('attribute',r'[\w:.-]+(?=\s*=)'),
                    ('value',r'"[^\"]*"|\x27[^\x27]*\x27'),
                    ('comment',r'<!--[\s\S]*?-->')]
        for tag, pattern in patterns:
            self.text.tag_remove(tag, '1.0', 'end')
            ranges=[]
            for m in re.finditer(pattern, fragment):
                ranges.extend((f'{start}+{m.start()}c', f'{start}+{m.end()}c'))
            if ranges: self.text.tag_add(tag, *ranges)

    def set_document(self, doc):
        self.issue_lines = getattr(doc, "issues_by_line", {})
        if self.source == doc.source: return
        scroll = self.text.yview()
        self.source = doc.source
        self.text.configure(state='normal')
        self.text.delete('1.0','end')
        self.text.insert('1.0', self.source.replace('\r\n','\n'))
        self.text.configure(state='disabled')
        self.text.yview_moveto(scroll[0])
        self.text.mark_set('search_from', '1.0')
        self.info.set(trf('{0:,}줄 · 현재 편집 내용', self.source.count(chr(10)) + 1))
        self.schedule()

    def reveal(self, node):
        if self.source is None: return
        start, end = source_index(self.source,node.start), source_index(self.source,node.end)
        self.text.tag_remove('component','1.0','end')
        self.text.tag_add('component',start,end)
        self.text.see(start)
        self.info.set(trf('{0} · {1}줄', node.get('id', node.tag), start.split('.')[0]))
        self.schedule()

    def reset_search(self):
        self.text.tag_remove('match','1.0','end')
        self.text.mark_set('search_from','1.0')

    def find(self, backwards=False):
        query=self.query.get()
        if not query or self.source is None:return 'break'
        ranges=self.text.tag_ranges('match')
        start=str(ranges[0] if backwards else ranges[1]) if ranges else ('end' if backwards else '1.0')
        options=dict(nocase=not self.case_sensitive.get(),backwards=backwards,exact=True)
        found=self.text.search(query,start,stopindex='1.0' if backwards else 'end',**options)
        if not found:found=self.text.search(query,'end' if backwards else '1.0',stopindex=start,**options)
        self.text.tag_remove('match','1.0','end')
        if not found:self.info.set(tr('검색 결과 없음'));return 'break'
        end=self.text.index(f'{found}+{len(query)}c')
        self.text.tag_add('match',found,end)
        self.text.see(found)
        self.info.set(trf('검색 위치 · {0}줄', found.split('.')[0]))
        return 'break'

    def select_all(self,event=None):
        self.text.tag_add('sel','1.0','end-1c');return 'break'

    def copy_selection(self,event=None):
        if self.text.tag_ranges('sel'):
            self.clipboard_clear();self.clipboard_append(self.text.get('sel.first','sel.last'))
        return 'break'

    def copy_all(self):
        if self.source is not None:
            self.clipboard_clear();self.clipboard_append(self.source)
            self.info.set(tr('현재 XML 전체를 복사했습니다.'))
