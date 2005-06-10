#!/usr/bin/python

import os
import string
from Volume import Volume

class VolumeGroup(Volume):
  def __init__(self, name, attr, lsize):
    VolumeGroup.__init__(self, name, attr, lsize, 0, 0)
  
  def __init__(self, name, attr, lsize, extent_size, free_extents):
    Volume.__init__(self)
    self.name = name
    self.vg = name 
    self.size = float(lsize)
    self.size_string = self.build_size_string(self.size)
    self.attr = attr
    self.is_utilized = True
    self.extent_size_bytes = extent_size # bytes
    self.free_extents = free_extents
