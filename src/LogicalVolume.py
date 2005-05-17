#!/usr/bin/python

import os
import string
from lvmui_constants import *
from Volume import Volume

class LogicalVolume(Volume):
  def __init__(self, name, path, vg, attr, lsize, used=True):
    Volume.__init__(self)
    self.name = name
    self.path = path
    self.vg = vg
    self.size = float(lsize)
    self.attr = attr
    self.is_utilized = used
    self.set_type(LOG_TYPE)

  def get_path(self):
    return self.path

  def get_vg_name(self):
    return self.vg
