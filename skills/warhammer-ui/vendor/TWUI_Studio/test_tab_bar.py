"""Run with xvfb-run -a python3 -m unittest test_tab_bar on headless Linux."""
import tkinter as tk
from tkinter import ttk
import unittest
from tab_bar import DocumentTabs


class DocumentTabsTests(unittest.TestCase):
 def setUp(self):
  try:self.root=tk.Tk()
  except tk.TclError as error:self.skipTest(str(error))
  self.errors=[];self.root.report_callback_exception=lambda *args:self.errors.append(args)
  ttk.Style(self.root).theme_use('clam');self.root.geometry('540x100')
  self.closed=[];self.tabs=DocumentTabs(self.root,self.closed.append);self.tabs.pack(fill='x')
  for i in range(12):self.tabs.add(ttk.Frame(self.tabs.notebook),text=f'campaign_document_{i:02}.twui.xml')
  self.tabs.select(0);self.root.update()

 def tearDown(self):
  if hasattr(self,'tabs'):
   self.root.destroy();self.assertEqual(self.errors,[])

 def span(self,index,element=None):
  n=self.tabs.notebook;y=n.winfo_height()//2;xs=[]
  for x in range(n.winfo_width()):
   try:at=n.index(f'@{x},{y}')
   except tk.TclError:continue
   if at==index and (element is None or element in n.identify(x,y)):xs.append(x)
  self.assertTrue(xs);return min(xs),max(xs)+1,y

 def assertVisible(self,index):
  left,right,_=self.span(index);start=self.tabs.viewport.canvasx(0)
  self.assertGreaterEqual(left,start-2)
  self.assertLessEqual(right,start+self.tabs.viewport.winfo_width()+2)

 def test_no_compression_and_no_scrollbar(self):
  widths=[self.span(i)[1]-self.span(i)[0] for i in range(12)]
  self.root.geometry('350x100');self.root.update()
  self.assertEqual(widths,[self.span(i)[1]-self.span(i)[0] for i in range(12)])
  self.assertTrue(self.tabs.left.winfo_ismapped());self.assertTrue(self.tabs.right.winfo_ismapped())
  self.assertLess(self.tabs.viewport.winfo_x(),self.tabs.left.winfo_x())
  self.assertLess(self.tabs.left.winfo_x(),self.tabs.right.winfo_x())
  self.assertGreater(self.span(11,'close')[1]-self.span(11,'close')[0],5)
  self.assertFalse(any(isinstance(w,ttk.Scrollbar) for w in self.tabs.winfo_children()))

 def test_wheel_only_scrolls(self):
  events=[];self.tabs.bind('<<NotebookTabChanged>>',lambda e:events.append(1))
  self.tabs.notebook.event_generate('<MouseWheel>',delta=-120);self.root.update()
  moved=self.tabs.viewport.canvasx(0);self.assertGreater(moved,0)
  self.tabs.notebook.event_generate('<MouseWheel>',delta=120);self.root.update()
  self.assertLess(self.tabs.viewport.canvasx(0),moved)
  self.tabs.notebook.event_generate('<Button-5>',x=30,y=10);self.root.update();self.assertGreater(self.tabs.viewport.canvasx(0),0)
  self.tabs.notebook.event_generate('<Button-4>',x=30,y=10);self.root.update()
  self.assertEqual(self.tabs.index(self.tabs.select()),0);self.assertEqual(events,[])

 def test_arrows_clamp_without_selecting(self):
  self.tabs.right.invoke();self.root.update();self.assertGreater(self.tabs.viewport.canvasx(0),0)
  self.tabs.scroll(100000);self.root.update();self.assertAlmostEqual(self.tabs.viewport.xview()[1],1)
  self.assertIn('disabled',self.tabs.right.state())
  self.tabs.left.invoke();self.root.update();self.assertLess(self.tabs.viewport.xview()[1],1)
  self.tabs.scroll(-100000);self.assertEqual(self.tabs.viewport.canvasx(0),0)
  self.assertIn('disabled',self.tabs.left.state());self.assertEqual(self.tabs.index(self.tabs.select()),0)

 def test_select_reveals_and_last_aligns_right(self):
  for i in (11,4,0,8):
   self.tabs.select(i);self.root.update();self.assertVisible(i)
  self.tabs.select(11);self.root.update();self.assertAlmostEqual(self.tabs.viewport.xview()[1],1)
  self.tabs.scroll(-500);self.tabs.select(11);self.root.update();self.assertAlmostEqual(self.tabs.viewport.xview()[1],1)

 def test_click_and_close_after_scrolling(self):
  self.tabs.select(10);self.root.update()
  left,right,y=self.span(10);n=self.tabs.notebook
  self.tabs.select(9);self.root.update()
  # Bring tab 10 back into view without selecting it.
  self.tabs.scroll(180);self.root.update()
  n.event_generate('<ButtonPress-1>',x=left+30,y=y);n.event_generate('<ButtonRelease-1>',x=left+30,y=y)
  self.root.update();self.assertEqual(self.tabs.index(self.tabs.select()),10)
  left,right,y=self.span(10,'close')
  n.event_generate('<ButtonPress-1>',x=(left+right)//2,y=y)
  n.event_generate('<ButtonRelease-1>',x=(left+right)//2,y=y)
  self.root.update();self.assertEqual(self.closed,[10])
  # A cancelled close callback must leave the document and selection intact.
  self.assertEqual(len(self.tabs.tabs()),12);self.assertEqual(self.tabs.index(self.tabs.select()),10)

 def test_context_menu_uses_scrolled_coordinates(self):
  self.tabs.select(11);self.root.update();left,right,y=self.span(11)
  seen=[];self.tabs.bind('<Button-3>',lambda e:seen.append(self.tabs.index(f'@{e.x},{e.y}')))
  n=self.tabs.notebook;x=left+30
  n.event_generate('<Button-3>',x=x,y=y,rootx=n.winfo_rootx()+x,rooty=n.winfo_rooty()+y)
  self.root.update();self.assertEqual(seen,[11])

 def test_destroy_reset_and_rename(self):
  self.tabs.select(11);self.root.update()
  self.tabs.tab(11,text='renamed_document.twui.xml *');self.root.update()
  self.assertEqual(self.tabs.tab(11,'text'),'renamed_document.twui.xml *')
  for name in self.tabs.tabs():self.tabs.nametowidget(name).destroy()
  self.root.update();self.assertEqual(self.tabs.tabs(),())
  frame=ttk.Frame(self.tabs.notebook);self.tabs.add(frame,text='new.xml');self.tabs.select(frame);self.root.update()
  self.assertEqual(self.tabs.index(self.tabs.select()),0)
  self.assertFalse(self.tabs.left.winfo_ismapped());self.assertEqual(self.tabs.viewport.canvasx(0),0)

 def test_resize_to_fit_hides_buttons(self):
  for name in self.tabs.tabs()[2:]:self.tabs.nametowidget(name).destroy()
  self.root.geometry('1000x100');self.root.update()
  self.assertFalse(self.tabs.left.winfo_ismapped());self.assertFalse(self.tabs.right.winfo_ismapped())
  self.assertEqual(self.tabs.viewport.xview(),(0.0,1.0))

class DocumentTabsIntegrationTests(unittest.TestCase):
 def test_real_studio_switch_history_close_and_reset(self):
  from unittest.mock import patch
  from app import Studio
  try:probe=tk.Tk();probe.destroy()
  except tk.TclError as error:self.skipTest(str(error))
  app=Studio();errors=[];app.report_callback_exception=lambda *args:errors.append(args)
  try:
   app.update()
   with patch('multidoc.messagebox.askyesno') as question:
    self.assertTrue(app.discard_ok());question.assert_not_called()
   for i in range(11):
    app.add_document(app.blank_payload(f'campaign_long_document_{i:02}.twui.xml'));app.update()
   self.assertEqual(app.active_document,11);self.assertAlmostEqual(app.tabs.viewport.xview()[1],1)
   original=app.doc.source;edited=original.replace('1600','1650');app.commit(edited);app.update()
   app.tabs.select(2);app.update();self.assertEqual(app.active_document,2)
   app.tabs.select(11);app.update();self.assertEqual(app.doc.source,edited)
   app.undo();self.assertEqual(app.doc.source,original);app.redo();self.assertEqual(app.doc.source,edited)
   app.tabs.notebook.event_generate('<MouseWheel>',delta=120);app.update()
   self.assertEqual(app.active_document,11);self.assertEqual(app.doc.source,edited)
   with patch('multidoc.messagebox.askyesnocancel',return_value=None) as confirm:
    app.close_document(11);app.update();confirm.assert_called_once()
   self.assertEqual(len(app.documents),12);self.assertEqual(app.doc.source,edited)
   with patch('multidoc.messagebox.askyesnocancel',return_value=False):
    app.close_document(11);app.update()
   self.assertEqual(len(app.documents),11);self.assertEqual(app.active_document,10)
   self.assertAlmostEqual(app.tabs.viewport.xview()[1],1)
   app.close_document(0);app.update();self.assertEqual(app.active_document,9)
   with patch('multidoc.messagebox.askyesno',return_value=True):app.close_all_tabs()
   app.update()
   self.assertEqual(len(app.tabs.tabs()),1);self.assertEqual(app.active_document,0)
   with patch('multidoc.messagebox.askyesno') as question:
    self.assertTrue(app.discard_ok());question.assert_not_called()
  finally:
   # The full editor also schedules delayed canvas paints; clean up this test's
   # root before the next test creates another Tcl interpreter.
   for job in app.tk.call('after','info'):app.tk.call('after','cancel',job)
   app.destroy()
  self.assertEqual(errors,[])

if __name__=='__main__':unittest.main()
