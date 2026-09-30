import unittest
from transform import resized,points,fixed2,offset_delta
from types import SimpleNamespace
class TransformTests(unittest.TestCase):
 def test_nine_handles(self):self.assertEqual(len(points((0,0,100,80))),9)
 def test_opposite_fixed(self):
  for i,j in points((0,0,100,80)):
   if (i,j)==(1,1):continue
   x,y,w,h=resized((10,20,100,80),(i,j),15,12)
   if i==0:self.assertEqual(x+w,110)
   if i==2:self.assertEqual(x,10)
   if j==0:self.assertEqual(y+h,100)
   if j==2:self.assertEqual(y,20)
 def test_center_fixed(self):
  x,y,w,h=resized((10,20,100,80),(0,0),10,12,alt=True)
  self.assertEqual((x+w/2,y+h/2),(60,60))
 def test_shift_and_locks(self):
  self.assertEqual(resized((0,0,100,80),(2,2),20,10,shift=True),(0,0,120,80))
  self.assertEqual(resized((0,0,100,80),(2,2),20,10,allow_x=False),(0,0,100,90))
  self.assertEqual(resized((0,0,100,80),(0,0),20,10,allow_x=False,allow_y=False),(0,0,100,80))
 def test_docking_anchor(self):
  c={'docking':'Center','component_anchor_point':'0.5,0.5'}
  self.assertEqual(offset_delta(c,(10,20,100,80),(0,10,120,100)),(0,0))
 def test_truncate(self):
  self.assertEqual(fixed2('11.11999'),'11.11');self.assertEqual(fixed2('-11.119'),'-11.11');self.assertEqual(fixed2('5'),'5.00')
  with self.assertRaises(ValueError):fixed2('abc')
