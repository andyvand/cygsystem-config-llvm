import os
import string

class ExtentSegment:
  def __init__(self, name, start, size, utilized):
    self.name = name
    self.start = start
    self.size = size   #in extents, of course
    self.utilized = utilized
    self.annotation = ""

  def get_name(self):
    return self.name

  def get_annotation(self):
    return self.annotation

  def set_annotation(self, annotation):
    self.annotation = annotation

  def get_start_size(self):
    return self.start,self.size

  def is_utilized(self):
    return self.utilized
