#!/usr/bin/python

import os
import string
from lvmui_constants import *
from Volume import Volume

class PhysicalVolume(Volume):
  def __init__(self, path, vg, fmt, attr, psize, pfree, initialized, total, alloc):
    Volume.__init__(self)
    self.name = self.extract_name(path)
    self.path = path
    self.vg = vg
    self.size = float(psize) #This is in gigabytes
    self.size_string = self.build_size_string(self.size)
    self.pfree = float(pfree)
    self.format = fmt
    self.is_utilized = initialized
    self.total_extents = int(total)
    self.allocated_extents = int(alloc)
    self.free_extents = self.total_extents - self.allocated_extents

    #If no format string, vol is uninitialized
    if (self.format == "") or (self.format == None):
      self.set_type(UNINITIALIZED_TYPE)
    #If no vg_name, vol is unallocated
    elif self.vg == "":
      self.set_type(UNALLOCATED_TYPE)
    else:
      self.set_type(PHYS_TYPE)


  def extract_name(self, path):
    idx = path.rfind("/")
    idx = idx + 1    #Leave off '/' char
    name = path[idx:] #get substring from idx to end of string
    return name

  def get_path(self):
    return self.path

  def get_vg_name(self):
    return self.vg

  def get_extent_values(self):
    return self.total_extents,self.free_extents,self.allocated_extents

