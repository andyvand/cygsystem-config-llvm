#!/usr/bin/python

import os
import string

class PhysicalExtent:
  def __init__(self, name, blocks, major, minor):
    self.name = name
    self.blocks = blocks
    self.major = major
    self.minor = minor

