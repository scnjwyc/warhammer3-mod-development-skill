import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from model import Document
from rendering import ZoomImageCache,raster
class ZoomImagesTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.path=Path(self.temp.name)/'test.png'
  Image.new('RGBA',(12,10),(160,90,30,230)).save(self.path)
  self.metrics=Document('<layout><hierarchy/><components/><image colour="#FFFFFFFF"/></layout>').nodes[-1]
 def test_two_canvases_and_return_to_zoom_reuse_tk_image(self):
  cache=ZoomImageCache()
  with patch('PIL.ImageTk.PhotoImage',side_effect=lambda *a,**k:object()) as create:
   a=cache.photo(self.path,24,20,self.metrics,(240,200),None)
   self.assertIs(a,cache.photo(self.path,24,20,self.metrics,(240,200),None))
   cache.end();cache.begin();cache.photo(self.path,24,20,self.metrics,(120,100),None)
   self.assertIs(a,cache.photo(self.path,24,20,self.metrics,(240,200),None));self.assertEqual(create.call_count,2)
 def test_lru_memory_bound_and_large_frame_sharing(self):
  cache=ZoomImageCache(limit=1000)
  with patch('PIL.ImageTk.PhotoImage',side_effect=lambda *a,**k:object()) as create:
   first=cache.photo(self.path,12,10,self.metrics,(100,100),None)
   self.assertIs(first,cache.photo(self.path,12,10,self.metrics,(100,100),None));self.assertEqual(cache.bytes,0)
   cache.end();cache.begin();cache.photo(self.path,12,10,self.metrics,(100,100),None);self.assertEqual(create.call_count,2)
   for size in ((10,10),(12,12),(14,14)):cache.photo(self.path,12,10,self.metrics,size,None)
   self.assertLessEqual(cache.bytes,cache.limit)
 def test_zoom_uses_base_pixels_without_smoothing(self):
  im=Image.new('RGBA',(12,10))
  for y in range(10):
   for x in range(12):im.putpixel((x,y),(x*20,y*24,80,50+x*16))
  im.save(self.path)
  expected=raster(self.path,24,20,self.metrics).resize((72,60),Image.Resampling.NEAREST)
  with patch('PIL.ImageTk.PhotoImage',side_effect=lambda im,**k:im.copy()):actual=ZoomImageCache().photo(self.path,24,20,self.metrics,(72,60),None)
  self.assertEqual(actual.tobytes(),expected.tobytes())
 def test_changed_asset_is_not_stale(self):
  cache=ZoomImageCache()
  with patch('PIL.ImageTk.PhotoImage',side_effect=lambda *a,**k:object()) as create:
   cache.photo(self.path,12,10,self.metrics,(12,10),None);Image.new('RGBA',(15,14),'blue').save(self.path)
   cache.photo(self.path,12,10,self.metrics,(12,10),None);self.assertEqual(create.call_count,2)
 def test_crop_limits_pixels_and_matches_full_render(self):
  from rendering import visible_crop
  self.assertIsNone(visible_crop(300,300,(100,100),(0,0,200,200)))
  self.assertEqual(visible_crop(-50,-20,(100,80),(0,0,200,200)),(50,20,100,80))
  cache=ZoomImageCache()
  with patch('PIL.ImageTk.PhotoImage',side_effect=lambda im,**k:im.copy()):
   result=cache.photo(self.path,24,20,self.metrics,(2400,2000),None,crop=(100,100,300,250))
  self.assertEqual(result.size,(200,150));self.assertEqual(cache.bytes,200*150*4)
 def test_cropped_detail_retains_full_image_pixels(self):
  from PIL import ImageChops
  im=Image.new('RGBA',(32,32))
  for y in range(32):
   for x in range(32):im.putpixel((x,y),(x*7,y*7,(x+y)*3,180+x*2))
  im.save(self.path);crop=(50,40,150,140);size=(256,256)
  expected=raster(self.path,32,32,self.metrics).resize(size,Image.Resampling.NEAREST).crop(crop)
  with patch('PIL.ImageTk.PhotoImage',side_effect=lambda im,**k:im.copy()):actual=ZoomImageCache().photo(self.path,32,32,self.metrics,size,None,crop=crop)
  self.assertEqual(actual.tobytes(),expected.tobytes())

 def test_zoom_never_reopens_cached_source_or_smooths(self):
  base=raster(self.path,12,10,self.metrics)
  with patch('PIL.Image.open',side_effect=AssertionError('source decoded again')),patch('PIL.ImageTk.PhotoImage',side_effect=lambda im,**k:im.copy()):
   cache=ZoomImageCache()
   for size in ((7,5),(95,83),(4096,4096),(12,10)):
    actual=cache.photo(self.path,12,10,self.metrics,size,None)
    self.assertEqual(set(actual.getdata()),set(base.getdata()))
