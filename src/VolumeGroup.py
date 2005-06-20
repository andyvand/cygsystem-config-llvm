#!/usr/bin/python

import os
import string
from Volume import Volume
from lvmui_constants import VG_TYPE


class VolumeGroup(Volume):
  def __init__(self, name, attr, lsize, extent_size=0, free_extents=0):
    Volume.__init__(self)
    self.name = name
    self.vg = name 
    self.size = float(lsize)
    self.size_string = self.build_size_string(self.size)
    self.attr = attr
    self.is_utilized = True
    self.extent_size_bytes = extent_size # bytes
    self.free_extents = free_extents
    self.set_type(VG_TYPE)
