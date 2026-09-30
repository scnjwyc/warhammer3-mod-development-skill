import unittest
from tree_columns import fit_columns,move_divider
class ColumnTests(unittest.TestCase):
 def test_second_divider_only_changes_right_pair(self):
  self.assertEqual(move_divider((140,80,60),1,15),(140,95,45))
  self.assertEqual(move_divider((140,80,60),1,1000),(140,104,36))
 def test_first_divider_shrinks_both(self):
  a,b,c=move_divider((140,80,60),0,40)
  self.assertEqual(a,180);self.assertLess(b,80);self.assertLess(c,60)
  self.assertEqual(move_divider((140,80,60),0,1000),(208,36,36))
 def test_invariants(self):
  for total in (196,280,400,800):
   widths=fit_columns(total,(145,65,48))
   for divider in (0,1):
    for delta in (-1000,-30,0,30,1000):
     result=move_divider(widths,divider,delta)
     self.assertEqual(sum(result),total)
     self.assertTrue(all(a>=b for a,b in zip(result,(80,36,36))))
if __name__=='__main__':unittest.main()
