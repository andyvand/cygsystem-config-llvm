"""This is the base class for PhysicalVolume
   and LogicalVolume. 
"""
__author__ = 'Jim Parsons (jparsons@redhat.com)'

import os
import string
from lvmui_constants import *

class Volume:
  def __init__(self):
    self.name = ""
    self.size = 0.0  #This is a floating point number
    self.size_string = "0.0M" #This is a rep of size with unit initial appended
    self.is_utilized = True
    self.type = UNINITIALIZED_TYPE
    self.extent_segment_list = list()

  def get_name(self):
    return self.name

  def get_volume_size(self):
    return self.size

  def set_volume_size(self, sz):
    self.size = sz
    self.size_string = self.build_size_string(self.size)

  def get_volume_size_string(self):
    return self.size_string

  def is_vol_utilized(self):
    return self.is_utilized

  def set_is_vol_utilized(self, is_utilized):
    """This method is used to set whether or not a volume
    represents free space in a Volume Group.
    """   
    self.is_utilized = is_utilized

  def get_extent_segments(self):
    return self.extent_segment_list

  def add_extent_segment(self, extent_segment):
    self.extent_segment_list.append(extent_segment)

  def set_type(self, type):
    self.type = type

  def get_type(self):
    return self.type

  def build_size_string(self, size):
    #incoming size is a string representation in gig. we need to evaluate
    #it and append an appropriate unit suffix.
    fsize = size
    if fsize > 1.0:
      return "%.2f"%fsize + GIG_SUFFIX
    else:
      fsize = fsize * 1000.0  #move unit into meg range
      if fsize > 1.0:
        return "%.2f"%fsize + MEG_SUFFIX
      else:
        fsize = fsize * 1000.0  #move unit into kilo range
        if fsize > 1.0:
          return "%.2f"%fsize + KILO_SUFFIX
        else:
          return "%.2f"%fsize + BYTE_SUFFIX

