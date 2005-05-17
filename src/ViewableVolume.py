"""This class provides view support for a volume model object.

   It is responsible for determining if a mouse selection
   was made for the volume it wraps. It also produces a 
   pango label describing the wrapped volume model object.

   ViewableVolumes can also have a list of ViewableExtents
   associated with it. This list is used to represent
   extent sections within a physical volume mapped to 
   logical volumes.
"""
__author__ = 'Jim Parsons (jparsons@redhat.com)'

import string
import pango

from Volume import Volume

class ViewableVolume:
  def __init__(self, vol, pc):
    """init method params:

       vol -- volume object that this class provides view support for
       pc -- pango context of the drawing area the label for this
             class is destined for.
    """
    self.volume = vol
    self.pango_context = pc
    self.start_pixel = 0
    self.span = 0
    self.is_selected = 0
    self.layout = None
    self.viewable_extents = list()

    #Build pango layout label

    self.prepare_label()
    

  def get_size(self):
    return float(self.volume.get_volume_size())

  def set_start_pixel(self, starter):
    """The start pixel is the pixel that denotes the beginning
    of the volume group section that represents this volume.
    """
    self.start_pixel = starter

  def get_start(self):
    return self.start_pixel

  def get_span(self):
    """span is the number of pixels used to 
    represent the size of this volume.
    """
    return self.span

  def set_span(self, span):
    self.span = span

  def set_start_span(self, starter, span):
    self.start_pixel = starter
    self.span = span

  def set_is_selected(self, selected):
    self.is_selected = selected

  def get_is_selected(self):
    return self.is_selected

  def prepare_label(self, size=(-1)):
    if size <= (0):
      self.layout = pango.Layout(self.pango_context)
      text = self.build_label()
      self.layout.set_text(text)
    else:
      pc = self.pango_context
      desc = pc.get_font_description()
      desc.set_size(1024 * size)
      pc.set_font_description(desc)
      self.layout = pango.Layout(pc)
      text = self.build_label()
      self.layout.set_text(text)

  def build_label(self):
    text = list()
    name = self.volume.get_name()
    for i in range(0, len(name)):
      if i == 0:
        text.append(name[i])
      else:
        text.append("\n")
        text.append(name[i])
    text_str = "".join(text)
    return text_str

  def get_layout(self):
    return self.layout

  def get_vertical_layout(self, size):
    self.prepare_label(size)
    return self.layout

  def get_horizontal_layout(self, size):
    pc = self.pango_context
    desc = pc.get_font_description()
    desc.set_size(1024 * size)
    pc.set_font_description(desc)
    layout = pango.Layout(pc)
    layout.set_text(self.volume.get_name())
    return layout

  def get_volume(self):
    return self.volume

  def add_viewable_extent(self, extent):
    self.viewable_extents.append(extent)

  def get_viewable_extents(self):
    return self.viewable_extents

  def clear_extent_selections(self):
    for e in self.viewable_extents:
      e.set_is_selected(False)
