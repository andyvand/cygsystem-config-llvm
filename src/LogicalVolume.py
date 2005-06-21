#!/usr/bin/python

import os
import string
from lvmui_constants import *
from Volume import Volume

class LogicalVolume(Volume):
  def __init__(self, name, path, vg, attr, lsize, used=True):
    Volume.__init__(self)
    self.name = name.strip()
    self.path = path
    self.vg = vg
    self.size = float(lsize)
    self.size_extents = 0
    self.attr = attr
    self.set_is_vol_utilized(used)
    self.set_type(LOG_TYPE)
    
    self.snapshot_origin = None
    self.snapshot_usage = 0 # percents
    
    self.has_snapshots = False
    self.snapshots = []
    
  
  def get_path(self):
    return self.path
  
  def get_vg_name(self):
    return self.vg
  
  def set_snapshot_origin(self, lv_name, usage):
    self.snapshot_origin = lv_name
    self.snapshot_usage = usage
  def get_snapshot_origin(self):
    return self.snapshot_origin
  def get_snapshot_usage(self):
    return self.snapshot_usage
  
  def set_has_snapshots(self, bool):
    self.has_snapshots = bool
  def get_has_snapshots(self):
    return self.has_snapshots
  def add_snapshot(self, snapshot):
    self.snapshots.append(snapshot)
  def get_snapshots(self):
    return self.snapshots
