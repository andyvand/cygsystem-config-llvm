
import os
import string
from lvmui_constants import *
from fdisk_wrapper import ID_EMPTY


from Volume import Volume


class PhysicalVolume(Volume):
  def __init__(self, name, fmt, attr, psize, pfree, initialized, total, alloc):
    Volume.__init__(self, name, [], initialized, attr)
    
    # pv properties
    self.size = float(psize) #This is in gigabytes
    #self.size_string = self.build_size_string(self.size)
    self.pfree = float(pfree)
    
    self.format = fmt
    
    self.set_extent_count(total, alloc)
    
    self.extent_blocks = []
    
    # type will get changed at set_vg call
    self.type = UNINITIALIZED_TYPE
    
    # general properties
    self.devname = None
    self.part = None
    self.initializable = True
    
  
  def get_size_total_string(self):
    if self.get_type() == PHYS_TYPE:
      size = self.get_size_total_used_free_string()[0]
    else:
      return "%.2f" % self.size + GIG_SUFFIX
  
  def get_type(self):
    return self.type
  
  def add_extent_block(self, extent_block):
    self.extent_blocks.append(extent_block)
    self.__sort_extent_blocks()
  def get_extent_blocks(self):
    return self.extent_blocks
  def __sort_extent_blocks(self):
    blocks = self.extent_blocks
    for i in range(len(blocks) - 1, 0, -1):
      for j in range(i, 0, -1):
        start1, size1 = blocks[j-1].get_start_size()
        start2, size2 = blocks[j].get_start_size()
        if start2 < start1:
          tmp = blocks[j-1]
          blocks[j-1] = blocks[j]
          blocks[j] = tmp
  
  def extract_name(self, path):
    idx = path.rfind("/")
    idx = idx + 1    #Leave off '/' char
    name = path[idx:] #get substring from idx to end of string
    return name
  
  def set_vg(self, vg):
    Volume.set_vg(self, vg)
    if vg == None:
      self.type = UNALLOCATED_TYPE
    else:
      self.type = PHYS_TYPE
  
  def setPartition(self, (devname, part)):
    devname = devname.strip()
    if part.id == ID_EMPTY:
      path = devname
      self.add_path(path)
      self.set_name(self.extract_name(path) + ' ' + FREE_SPACE)
    else:
      path = devname + str(part.num)
      self.add_path(path)
      self.set_name(self.extract_name(path))
    #self.set_volume_size(part.getSizeBytes()/1024.0/1024/1024)
    self.devname = devname
    self.part = part
  def getPartition(self):
    return (self.devname, self.part)
  
  def needsFormat(self):
    if self.part == None:
      return False
    return self.part.id == ID_EMPTY

  def wholeDevice(self): # part occupies whole device
    if self.part == None:
      return False
    return self.part.wholeDevice
  
  
  
  def print_out(self, padding):
    print padding + 'PV: ' + self.get_name()
    print padding + 'extents:'
    for extent in self.get_extent_blocks():
      extent.print_out(padding + '  ')
