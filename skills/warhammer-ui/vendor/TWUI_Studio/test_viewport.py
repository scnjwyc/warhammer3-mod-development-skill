import unittest,tempfile
from pathlib import Path
from viewport import stable_region,clipped_label
from inspector import suggestions,resource_relative
class ViewTests(unittest.TestCase):
 def test_panned_view_survives_smaller_content_bounds(self):
  old=(-1000,-800,2000,1800);left,top=-450,-320
  new=stable_region(old,(0,0,200,100),left,top,700,400)
  self.assertEqual(new,old)
  self.assertEqual(new[0]+(left-new[0])/(new[2]-new[0])*(new[2]-new[0]),left)
 def test_label_never_exceeds_limit(self):
  for limit in range(1,200):self.assertLessEqual(len(clipped_label('header_slaves_expense',len,limit)),limit)
 def test_cco_suggestions_and_mapping(self):
  self.assertEqual(suggestions('CcoCampaign',['CcoBattle','CcoCampaignFaction']),['CcoCampaignFaction'])
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'ui/skins/default/test.png'
   self.assertEqual(resource_relative(p,[Path(d)]),'ui/skins/default/test.png')
   self.assertIsNone(resource_relative(Path(d)/'outside.png',[Path(d)/'ui']))
if __name__=='__main__':unittest.main()

class FitGridTests(unittest.TestCase):
 def test_fit_leaves_margin(self):
  from viewport import fit_zoom
  z=fit_zoom(800,600,(200,100,400,200))
  self.assertLessEqual(400*z,800*.72);self.assertLessEqual(200*z,600*.72)
 def test_grid_scales_and_retains_origin(self):
  from viewport import grid_positions
  for z in (.5,1,2):
   values=grid_positions(-100,500,z)
   self.assertAlmostEqual(values[1]-values[0],24*z)
   self.assertIn(32,values)
