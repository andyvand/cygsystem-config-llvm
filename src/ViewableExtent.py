import string
import pango
import gettext
_ = gettext.gettext

from ExtentSegment import ExtentSegment

PHYSICAL_EXTENTS=("physical extents")

class ViewableExtent:
  def __init__(self, extent, pc):
    self.extent = extent
    self.pango_context = pc
    self.start_pixel = 0
    self.span = 0
    self.is_selected = 0
    self.layout = None
    
  def get_extent_count(self):
    start,size = self.extent.get_start_size()
    return size

  def get_extent_start(self):
    start,size = self.extent.get_start_size()
    return start

  def set_start_pixel(self, starter):
    self.start_pixel = starter

  def get_start_pixel(self):
    return self.start_pixel

  def set_span(self, span):
    self.span = span

  def get_span(self):
    return self.span

  def set_start_span(self, starter, span):
    self.start_pixel = starter
    self.span = span

  def get_start_span(self):
    return self.start_pixel,self.span

  def set_is_selected(self, selected):
    self.is_selected = selected

  def get_is_selected(self):
    return self.is_selected
   
  def check_name(self, ename):
    name = ename.strip()
    nm = self.extent.get_name().strip()
    if nm == name:
      return True
    else:
      return False 

  #def get_horizontal_layout(self, size):
  #  pc = self.pango_context
  #  desc = pc.get_font_description()
  #  desc.set_size(1024 * size)
  #  pc.set_font_description(desc)
  #  layout = pango.Layout(pc)
  #  layout.set_text(self.extent.get_name())
  #  return layout

  def get_horizontal_layout(self, size):
    pc = self.pango_context
    desc = pc.get_font_description()
    desc.set_size(1024 * size)
    pc.set_font_description(desc)
    layout = pango.Layout(pc)
    layout_str1 = self.extent.get_name() + "\n"
    layout_str2 = self.extent.get_annotation() + "\n"
    start,size = self.extent.get_start_size()
    layout_str3 = str(size) + " " + PHYSICAL_EXTENTS + "\n"
    layout_text = layout_str1 + layout_str2 + layout_str3 
    layout.set_text(layout_text)
    return layout

