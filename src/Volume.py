"""This is the base class for PhysicalVolume
   and LogicalVolume. 
"""
__author__ = 'Jim Parsons (jparsons@redhat.com)'

import os
import string
from gtk import TRUE, FALSE
from lvmui_constants import *

class Volume:
  def __init__(self):
    self.name = ""
    self.size = 0.0
    self.is_utilized = TRUE
    self.type = UNINITIALIZED_TYPE
    self.extent_segment_list = list()

  def get_name(self):
    return self.name

  def get_volume_size(self):
    return self.size

  def set_volume_size(self, sz):
    self.size = sz

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
