#!/usr/bin/python

import os
import string
from gtk import TRUE, FALSE
import rhpl.executil
from Volume import Volume

class VolumeGroup(Volume):
  def __init__(self, name, attr, lsize ):
    Volume.__init__(self)
    self.name = name
    self.vg = name 
    self.size = float(lsize)
    self.attr = attr
    self.is_utilized = TRUE

