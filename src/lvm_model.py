import os
import sys
import string
from gtk import TRUE, FALSE
from lvmui_constants import *
from Volume import Volume
from PhysicalVolume import PhysicalVolume
from LogicalVolume import LogicalVolume
from VolumeGroup import VolumeGroup
from ExtentSegment import ExtentSegment
import rhpl.executil
import gettext
_ = gettext.gettext

#Column names for PVS calls
P_NAME_COL=0
P_VG_NAME_COL=1
P_FMT_COL=2
P_ATTR_COL=3
P_SIZE_COL=4
P_FREE_COL=5
P_PE_COUNT_COL=6
P_PE_ALLOC_COL=7

#Column names for PVS calls
L_NAME_COL=0
L_VG_NAME_COL=1
L_ATTR_COL=2
L_SIZE_COL=3

#Column names for lvdisplay calls
LV_PATH_COL=0
LV_VGNAME_COL=1

UNUSED=_("Unused") 
UNUSED_SPACE=_("Unused Space")

#Translator - Linear mapping is another way of saying 'Not Striped' :-)
LINEAR_MAPPING=_("Linear Mapping")
UNMOUNTED=_("Unmounted")
NO_FILESYSTEM=_("No File System")
SEG_START_COL = 2
SEG_END_COL = 4
GIG=1000000000.00
VGS_OPTION_STRING="vg_name,vg_sysid,vg_fmt,vg_attr,vg_size,vg_free,vg_extent_count,vg_free_count,vg_extent_size,max_pv,pv_count,max_lv,lv_count,vg_uuid"

LVS_OPTION_STRING="lv_name,vg_name,lv_size,seg_count,stripes,stripesize,lv_attr,lv_uuid"

PVS_OPTION_STRING="pv_name,vg_name,pv_size,pv_used,pv_free,pv_pe_count,pv_pe_alloc_count,pv_attr,pv_uuid"


VG_NAME=_("Volume Group Name:   ")
VG_SYSID=_("System ID:   ")
VG_FMT=_("Format:   ")
VG_ATTR=_("Attributes:   ")
VG_SIZE=_("Volume Group Size:   ")
VG_FREE=_("Available Space:   ")
VG_EXTENT_COUNT=_("Total Number of Extents:   ")
VG_FREE_COUNT=_("Number of Free Extents:   ")
VG_EXTENT_SIZE=_("Extent Size:   ")
MAX_PV=_("Maximum Allowed Physical Volumes:   ")
PV_COUNT=_("Number of Physical Volumes:   ")
MAX_LV=_("Maximum Allowed Logical Volumes:   ")
LV_COUNT=_("Number of Logical Volumes:   ")
VG_UUID=_("VG UUID:   ")

LV_NAME=_("Logical Volume Name:   ")
LV_SIZE=_("Logical Volume Size:   ")
LV_SEG_COUNT=_("Number of Segments:   ")
LV_STRIPE_COUNT=_("Number of Stripes:   ")
LV_STRIPE_SIZE=_("Stripe Size:   ")
LV_ATTR=_("Attributes:   ")
LV_UUID=_("LV UUID:   ")

UV_PARTITION_TYPE=_("Partition Type:   ")
UV_SIZE=_("Size:   ")
UV_MOUNT_POINT=_("Mount Point:   ")
UV_FILESYSTEM=_("File System:   ")

PV_NAME=_("Physical Volume Name:   ")
PV_SIZE=_("Physical Volume Size:   ")
PV_USED=_("Space Used:   ")
PV_FREE=_("Space Free:   ")
PV_PE_COUNT=_("Total Physical Extents:   ")
PV_PE_ALLOC_COUNT=_("Allocated Physical Extents:   ")
PV_ATTR=_("Attributes:   ")
PV_UUID=_("PV UUID:   ")

VG_NAME_IDX = 0
VG_SYSID_IDX = 1
VG_FMT_IDX = 2
VG_ATTR_IDX = 3
VG_SIZE_IDX = 4
VG_FREE_IDX = 5
VG_EXTENT_COUNT_IDX = 6
VG_FREE_COUNT_IDX = 7
VG_EXTENT_SIZE_IDX = 8
MAX_PV_IDX = 9
PV_COUNT_IDX = 10
MAX_LV_IDX = 11
LV_COUNT_IDX = 12
VG_UUID_IDX = 13

LV_NAME_IDX = 0
LV_VG_NAME_IDX = 1
LV_SIZE_IDX = 2
LV_SEG_COUNT_IDX = 3
LV_STRIPE_COUNT_IDX = 4
LV_STRIPE_SIZE_IDX = 5
LV_ATTR_IDX = 6
LV_UUID_IDX = 7

PV_NAME_IDX = 0
PV_VG_NAME_IDX = 1
PV_SIZE_IDX = 2
PV_USED_IDX = 3
PV_FREE_IDX = 4
PV_PE_COUNT_IDX = 5
PV_PE_ALLOC_COUNT_IDX = 6
PV_ATTR_IDX = 7
PV_UUID_IDX = 8


class lvm_model:
  def __init__(self):
    pass

  def query_PEs(self):
    pelist = list()
    uncertainlist = list()
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("pvs")
    arglist.append("-a")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    arglist.append("--units")
    arglist.append("g")
    arglist.append("--separator")
    arglist.append(",")

    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    lines = result_string.splitlines()
    for line in lines:
      words = line.split(",")
      if words[2] == "":  #No entry in column 3 means not initialized
        initialized = FALSE
      else:
        initialized = TRUE
      pv = PhysicalVolume(words[0],words[1], words[2], words[3], words[4], words[5],initialized,0,0)
      if initialized:
        pelist.append(pv)
      else:
        uncertainlist.append(pv)
      #try and determine sizes and if vol is swap or extended

    arg_list = list()
    arg_list.append("/sbin/fdisk")
    arg_list.append("-l")
    result  = rhpl.executil.execWithCapture("/sbin/fdisk", arg_list)
    textlines = result.splitlines()

    #At this point, all of the visible partitions initialized for LVM usage
    #are listed in pelist. There are, however, usually other
    #partitions that are either uninitialized or not to be included in a list
    #that allows initialization for lvm, such as swap partitions.
    #this code examines the uncertain list and moves appropriate
    #physical extents to the pelist.

    for item in uncertainlist:
      p = item.get_path()
      path = p.strip()
      for textline in textlines:
        if textline == "":
          continue
        text_words = textline.split()
        simple_text = text_words[0].strip()
        if simple_text == path:
          #fdisk 2.12 with the -l switch produces 7 columns
          #column 2 is Boot, and signifies a boot partition if there
          #is an asterisk in this column. If there is not, this column
          #holds white space, hence the length of non-boot partitions
          #will always be 6, and boot partitions will be 7
          cols = len(text_words)
          if cols == 7:  #A boot partition or swap partition
            break;
          if text_words[cols - 2] == "83":
            sz_str = text_words[cols - 3]
            val = sz_str.find("+")
            if val >= 0:  #There is a '+' at end of string...
              adj_sz_str = sz_str[:val]  #strip plus sign
            else:
              adj_sz_str = sz_str
            #item.set_volume_size(float(adj_sz_str) / GIG)
            ###FIX need to be smarter about size conversions here
            ###FIX use lvmdiskscan here
            item.set_volume_size(float(adj_sz_str) / 1000000.0) 
            pelist.append(item)
            break

    return pelist

  def get_PV(self,pathname):
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("pvs")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    arglist.append("--units")
    arglist.append("g")
    arglist.append("--separator")
    arglist.append(",")
    arglist.append("-o")
    arglist.append("+pv_pe_count,pv_pe_alloc_count")
    arglist.append(pathname)
                                                                                
    line = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    if (line == None) or (len(line) < 1):
      ###FIXME - Throw exception here, if no result is returned
      return None
    words = line.split(",")
    pv = PhysicalVolume(words[P_NAME_COL],
                        words[P_VG_NAME_COL],
                        words[P_FMT_COL],
                        words[P_ATTR_COL],
                        words[P_SIZE_COL],
                        words[P_FREE_COL],
                        TRUE,
                        words[P_PE_COUNT_COL],
                        words[P_PE_ALLOC_COL])

    if pv.get_type() == PHYS_TYPE:
      #Add extent segments
      self.get_extents_for_PV(pv)
    return pv

  def query_PVs(self):
    pvlist = list()
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("pvs")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    arglist.append("--units")
    arglist.append("g")
    arglist.append("--separator")
    arglist.append(",")
    arglist.append("-o")
    arglist.append("+pv_pe_count,pv_pe_alloc_count")

    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    lines = result_string.splitlines()
    for line in lines:
      words = line.split(",")
      pv = PhysicalVolume(words[P_NAME_COL],
                          words[P_VG_NAME_COL],
                          words[P_FMT_COL], 
                          words[P_ATTR_COL], 
                          words[P_SIZE_COL], 
                          words[P_FREE_COL],
                          TRUE, 
                          words[P_PE_COUNT_COL], 
                          words[P_PE_ALLOC_COL])

      if pv.get_type() == PHYS_TYPE:
        #Add extent segments
        self.get_extents_for_PV(pv)

      pvlist.append(pv)
    return pvlist

  def query_PVs_for_VG(self, vg_name):
    name = vg_name.strip()
    hotlist = list()
    pv_s = self.query_PVs()
    for pv in pv_s:
      if pv.get_vg_name() == name:
        hotlist.append(pv)

    return hotlist

  def query_VGs(self):
    vglist = list()
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("vgs")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    arglist.append("--units")
    arglist.append("g")
    arglist.append("--separator")
    arglist.append(",")
                                                                                
    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    lines = result_string.splitlines()
    for line in lines:
      line.strip()
      words = line.split(",")
      vg = VolumeGroup(words[0], words[4], words[5])
      vglist.append(vg)
    return vglist

  def get_VG(self, vgname):
    vg_name = vgname.strip()
    vglist = self.query_VGs()
    for vg in vglist:
      if vg.get_name().strip() == vg_name:
        return vg

    return None
                                                                                
  def get_VG_for_PV(self, pv):
    pass

  def get_LV(self,pathname):
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("lvs")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    arglist.append("--units")
    arglist.append("g")
    arglist.append("--separator")
    arglist.append(",")
    arglist.append(pathname)
 
    line = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    if (line == None) or (len(line) < 1):
      ###FIXME - Throw exception here, if no result is returned
      return None
    words = line.split(",")
    lv = LogicalVolume(words[L_NAME_COL],
                        pathname,
                        words[L_VG_NAME_COL],
                        words[L_ATTR_COL],
                        words[L_SIZE_COL],
                        TRUE)

    return lv

  def query_LVs_for_VG(self, vg_name):
    lvlist = list()
    arglist = list()
    vgname = vg_name.strip()
    arglist.append("/sbin/lvm")
    arglist.append("lvs")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    arglist.append("--units")
    arglist.append("g")
    arglist.append("--separator")
    arglist.append(",")
    arglist.append(vgname)

    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    lines = result_string.splitlines()
    for line in lines:
      words = line.split(",")
      name = words[0].strip()
      path = self.get_logical_volume_path(name, vgname)
      lv = LogicalVolume(name, path, words[1],words[2], words[3])
      lvlist.append(lv)

    #Now check if there is free space in Volume Group with name vg_name.
    #If there is free space, add an LV marked as 'unused' for that available
    # space, so that it can be rendered properly
    vg_arglist = list()
    vg_arglist.append("/sbin/lvm")
    vg_arglist.append("vgs")
    vg_arglist.append("--nosuffix")
    vg_arglist.append("--noheadings")
    vg_arglist.append("--units")
    vg_arglist.append("g")
    vg_arglist.append("--separator")
    vg_arglist.append(",")
    vg_arglist.append(vg_name)

    result_string = rhpl.executil.execWithCapture("/sbin/lvm",vg_arglist)
    lines = result_string.splitlines()
    for line in lines:
      words = line.split(",")
      if words[6] > 0.0:
       lv = LogicalVolume(UNUSED, None, words[1],None, words[6], FALSE)
       lvlist.append(lv)

    return lvlist

  def get_logical_volume_path(self, lname, vgname):
    lvlist = list()
    arglist = list()
    lv_name = lname.strip()
    vg_name = vgname.strip()
    arglist.append("/usr/sbin/lvdisplay") #lvs does not give path info
    arglist.append("-c")
                                                                                
    result_string = rhpl.executil.execWithCapture("/usr/sbin/lvdisplay",arglist)
    lines = result_string.splitlines()
    #The procedure below does the following:
    #The output of the command is examined line by line for a volume 
    #group name match in the second column.
    #If the volume group name matches, check if the LV name can be found 
    #within the first column string. If so, the column[0] string is the path.
    for line in lines:
      words = line.split(":")
      vgnm = words[LV_VGNAME_COL].strip()
      if vgnm == vg_name:
        candidate_path = words[LV_PATH_COL].strip()
        if candidate_path.find(lv_name) >= 0:
          return candidate_path

    ###FIXME Raise exception here because true path is not being returned,
    ###But rather the lname arg is being returned.
    return name

  def query_uninitialized(self):
    pe_list = self.query_PEs()
    uninit_list = list()
    for pe in pe_list:
      if pe.get_type() == UNINITIALIZED_TYPE:
        uninit_list.append(pe)

    return uninit_list

  def get_UV(self, pathname):
    uv_list = self.query_uninitialized()
    for uv in uv_list:
      uvpath = uv.get_path().strip()
      if uvpath == pathname:
        return(uv) 

  def query_unallocated(self):
    pv_list = self.query_PVs()
    unalloc_list = list()
    for pv in pv_list:
      if pv.get_type() == UNALLOCATED_TYPE:
        unalloc_list.append(pv)

    return unalloc_list

  def get_free_space_on_VG(self, vgname, unit):
    vg_name = vgname.strip()
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("vgs")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    arglist.append("--units")
    arglist.append(unit)
    arglist.append("--separator")
    arglist.append(",")
    arglist.append("-o")
    arglist.append("vg_free,vg_free_count")
    arglist.append(vg_name)

    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    lines = result_string.splitlines()

    if (lines[0].find("not found")) >= 0:
      return None,None

    words = lines[0].split(",")

    return words[0],words[1]

  def get_max_LVs_PVs_on_VG(self, vgname):
    vg_name = vgname.strip()
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("vgs")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    arglist.append("--separator")
    arglist.append(",")
    arglist.append("-o")
    arglist.append("max_lv,lv_count,max_pv,pv_count")
    arglist.append(vg_name)

    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)

    words = result_string.split(",")

    #max LVs, number of LVs, max PVs, number of PVs
    if words[0] == "0":
      words[0] = "256"
    if words[2] == "0":
      words[2] = "256"
    
    max_lvs = int(words[0])
    lvs = int(words[1])
    max_pvs = int(words[2])
    pvs = int(words[3])
    return max_lvs,lvs,max_pvs,pvs

  def get_data_for_VG(self, vgname):
    name = vgname.strip()
    text_list = list()
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("vgs")
    arglist.append("--nosuffix")
    arglist.append("--noheadings")
    #arglist.append("--units")
    #arglist.append("g")
    arglist.append("--separator")
    arglist.append(",")
    arglist.append("-o")
    arglist.append(VGS_OPTION_STRING)
    arglist.append(name)

    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    lines = result_string.splitlines()
    words = lines[0].split(",")
    text_list.append(VG_NAME)
    text_list.append(words[VG_NAME_IDX])
    text_list.append(VG_SYSID)
    text_list.append(words[VG_SYSID_IDX])
    text_list.append(VG_FMT)
    text_list.append(words[VG_FMT_IDX])
    text_list.append(VG_ATTR)
    text_list.append(words[VG_ATTR_IDX])
    text_list.append(VG_SIZE)
    text_list.append(words[VG_SIZE_IDX])
      
    text_list.append(VG_FREE)
    text_list.append(words[VG_FREE_IDX])
      
    text_list.append(VG_EXTENT_COUNT)
    text_list.append(words[VG_EXTENT_COUNT_IDX])
      
    text_list.append(VG_FREE_COUNT)
    text_list.append(words[VG_FREE_COUNT_IDX])
      
    text_list.append(VG_EXTENT_SIZE)
    text_list.append(words[VG_EXTENT_SIZE_IDX])
      
    text_list.append(MAX_PV)
    #lvs reports 0 for sys max
    if words[MAX_PV_IDX] == "0":
      text_list.append("256")
    else:
      text_list.append(words[MAX_PV_IDX])
      
    text_list.append(PV_COUNT)
    text_list.append(words[PV_COUNT_IDX])
      
    text_list.append(MAX_LV)
    if words[MAX_LV_IDX] == "0":
      text_list.append("256")
    else:
      text_list.append(words[MAX_LV_IDX])
      
    text_list.append(LV_COUNT)
    text_list.append(words[LV_COUNT_IDX])
      
    text_list.append(VG_UUID)
    text_list.append(words[VG_UUID_IDX])
      
    return text_list

  def get_data_for_UV(self, p):
    partition_type = ""
    is_mounted = ""
    filesys_type = ""
    size_string = ""
    path = p.strip()
    arglist = list()
    arglist.append("/sbin/fdisk")
    arglist.append("-l")
    result  = rhpl.executil.execWithCapture("/sbin/fdisk", arglist)
    textlines = result.splitlines()
    #First determine partition type
    for textline in textlines:
      if textline == "":
        continue
      text_words = textline.split()
      possible_path = text_words[0].strip()
      if possible_path == path:
        cols = len(text_words)
        if text_words[cols - 2] == "83":
          partition_type = "Linux Partition"
        else:
          partition_type = text_words[cols - 2]
        break

    #Now determine size
    arglist = list()
    arglist.append("/usr/sbin/lvmdiskscan")
    result  = rhpl.executil.execWithCapture("/usr/sbin/lvmdiskscan", arglist)
    textlines = result.splitlines()
    for textline in textlines:
      text_words = textline.split()
      possible_path = text_words[0].strip()
      #If we find our path, we need to extract the size info from line
      #Size info resides between two square brackets
      #Here is a typical output line from lvmdiskscan:
      #  /dev/sda10 [      784.39 MB] LVM physical volume
      if possible_path == path:
        start_idx = textline.find("[")
        start_idx = start_idx + 1   #loose '['
        first_part = textline[start_idx:]
        end_idx = first_part.find("]")
        final_part = first_part[:end_idx]
        size_string = final_part.strip()
        break

    #Next, check if partition is mounted
    arglist = list()
    arglist.append("/bin/cat")
    arglist.append("/proc/mounts")
    result  = rhpl.executil.execWithCapture("/bin/cat", arglist)
    textlines = result.splitlines()
    for textline in textlines:
      text_words = textline.split()
      possible_path = text_words[0].strip()
      if possible_path == path:
        is_mounted = text_words[1]
        break
    if is_mounted == "":
      is_mounted = UNMOUNTED

    #Finally, check for file system
    arglist = list()
    arglist.append("/usr/bin/file")
    arglist.append("-s")
    arglist.append(path)
    result = rhpl.executil.execWithCapture("/usr/bin/file", arglist)
    words = result.split()
    if len(words) < 3:  #No file system
      filesys_type = NO_FILESYSTEM
    elif words[2].strip() == "rev":
      filesys_type = words[4]
    else:
      filesys_type = words[2]

    #Finish up by returning data
    textlist = list()
    textlist.append(UV_SIZE)
    textlist.append(size_string)
    textlist.append(UV_PARTITION_TYPE)
    textlist.append(partition_type)
    textlist.append(UV_FILESYSTEM)
    textlist.append(filesys_type)
    textlist.append(UV_MOUNT_POINT)
    textlist.append(is_mounted)

    return textlist
   
  def get_data_for_LV(self, p):
    path = p.strip()
    text_list = list()
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("lvs")
    arglist.append("--noheadings")
    arglist.append("--separator")
    arglist.append(",")
    arglist.append("-o")
    arglist.append(LVS_OPTION_STRING)
    arglist.append(path)

    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    lines = result_string.splitlines()
    words = lines[0].split(",")
    text_list.append(LV_NAME)
    text_list.append(words[LV_NAME_IDX])
    text_list.append(VG_NAME)
    text_list.append(words[LV_VG_NAME_IDX])
    text_list.append(LV_SIZE)
    text_list.append(words[LV_SIZE_IDX])
    text_list.append(LV_SEG_COUNT)
    text_list.append(words[LV_SEG_COUNT_IDX])

    if int(words[LV_STRIPE_COUNT_IDX]) > 1:
      text_list.append(LV_STRIPE_COUNT)
      text_list.append(words[LV_STRIPE_COUNT_IDX])
      text_list.append(LV_STRIPE_SIZE)
      text_list.append(words[LV_STRIPE_SIZE_IDX])
    text_list.append(LV_ATTR)
    text_list.append(words[LV_ATTR_IDX])
    text_list.append(LV_UUID)
    text_list.append(words[LV_UUID_IDX])

    return text_list
                                                                                

  def get_data_for_PV(self, p):
    path = p.strip()
    text_list = list()
    arglist = list()
    arglist.append("/sbin/lvm")
    arglist.append("pvs")
    arglist.append("--noheadings")
    arglist.append("--separator")
    arglist.append(",")
    arglist.append("-o")
    arglist.append(PVS_OPTION_STRING)
    arglist.append(path)
    
    result_string = rhpl.executil.execWithCapture("/sbin/lvm",arglist)
    lines = result_string.splitlines()
    words = lines[0].split(",")
    text_list.append(PV_NAME)
    text_list.append(words[PV_NAME_IDX])

    if words[PV_VG_NAME_IDX] == "":
      text_list.append(VG_NAME)
      text_list.append("---")
    else:
      text_list.append(VG_NAME)
      text_list.append(words[PV_VG_NAME_IDX])

    text_list.append(PV_SIZE)
    text_list.append(words[PV_SIZE_IDX])
    text_list.append(PV_USED)
    text_list.append(words[PV_USED_IDX])
    text_list.append(PV_FREE)
    text_list.append(words[PV_FREE_IDX])
    text_list.append(PV_PE_COUNT)
    text_list.append(words[PV_PE_COUNT_IDX])
    text_list.append(PV_PE_ALLOC_COUNT)
    text_list.append(words[PV_PE_ALLOC_COUNT_IDX])
    text_list.append(PV_ATTR)
    text_list.append(words[PV_ATTR_IDX])
    text_list.append(PV_UUID)
    text_list.append(words[PV_UUID_IDX])
                                                                                
    return text_list
 

  ###This method adds complete/contiguous extent lists to PVs -- no holes
  def get_extents_for_PV(self, pv ):
    extentlist = list()
    pathname = pv.get_path().strip()
    #Cases:
    ##1) vgname == "", add one extent 'free' using all extents
    ##2) query_LVs_for_VG returns empty list, same as 1
    ##3) extents are used, build list and fill in free holes 

    #1
    vgname = pv.get_vg_name().strip()
    if vgname == "":
      total,free,alloc = pv.get_extent_values()
      es = ExtentSegment(FREE,0,total,FALSE)
      es.set_annotation(UNUSED_SPACE)
      pv.add_extent_segment(es)
      return 

    if vgname == None:
      total,free,alloc = pv.get_extent_values()
      es = ExtentSegment(FREE,0,total,FALSE)
      es.set_annotation(UNUSED_SPACE)
      pv.add_extent_segment(es)
      return 

    #2
    lvlist = self.query_LVs_for_VG(vgname)
    #if lvlist is empty, add one extent_segment for the empty space, then return
    if len(lvlist) == 1:  #Could be an 'unused' section or fully used section
      if lvlist[0].is_vol_utilized == FALSE: 
        total,free,alloc = pv.get_extent_values()
        es = ExtentSegment(FREE,0,total,FALSE)
        es.set_annotation(UNUSED_SPACE)
        pv.add_extent_segment(es)
        return 
      else:
        total,free,alloc = pv.get_extent_values()
        es = ExtentSegment(lvlist[0].get_name(),0,total,TRUE)
        pv.add_extent_segment(es)
        return 
        
    #The cases above all result in one extent segment per PV.
    #When a PV has multiple extent segments, we must build a list
    #of them, sort them, and make sure it is contiguous
    for lv in lvlist:
      if lv.is_vol_utilized() == FALSE:
        continue
      path = lv.get_path()
      arglist = list()
      arglist.append("/usr/sbin/lvdisplay")
      arglist.append("-m")
      arglist.append(path)
      result_string = rhpl.executil.execWithCapture("/usr/sbin/lvdisplay",arglist)
      ##For ease of maintenance, here is an explanation of what is
      ##going on here...the lvmdisplay command is run above for
      ##each Logical Volume in the pv's volumegroup. The command
      ##is run with the '-m' switch which supplies mapping info
      ##between the LV and its PVs.
      ##The first chunk of data that is returned from this command is
      ##general info about the LV -- there is no chance that the 
      ##PV's path (such as /dev/sda7) will be in the first big 
      ##chunk. The second chunk is the mapping info, which is appended
      ##onto the first chunk. It looks like this if linear:
      ##
      ##  --- Segments ---
      ##  Logical extent 0 to 249:
      ##    Type                linear
      ##    Physical volume     /dev/sda7
      ##    Physical extents    0 to 249
      ##
      ## And looks like this if striped:
      ##
      ##  --- Segments ---
      ##  Logical extent 0 to 25:
      ##    Type                striped
      ##    Stripes             2
      ##    Stripe size         64 KB
      ##    Stripe 0:
      ##      Physical volume   /dev/sda7
      ##      Physical extents  250 to 262
      ##    Stripe 1:
      ##      Physical volume   /dev/sda11
      ##      Physical extents  0 to 12
      ## So the code below searches for the full PV path
      ## on each line, and when it finds it, it
      ## splits the following line (i + 1) into substrings
      ## using whitespace is the sep char, and then looks
      ## for the values for words[3] and words[5] to get the
      ## start and ending extents. Hopefully, this map info
      ## will be included in lvs soon, so this dangerous
      ## parsing code can be removed.
      ########

      lines = result_string.splitlines()
      #search for pathname in each string with while loop
      for i in range(0, len(lines)):
        if lines[i].find(pathname) != (-1):  #we found our PV in mapping table
          ### FIXME Wrap this in an exception handler in case format is wrong
          words = lines[i+1].split()
          start = int(words[SEG_START_COL])
          end = int(words[SEG_END_COL])
          span = end - start + 1
          extent = ExtentSegment(lv.get_name(), start, span, TRUE)
          #Now let's determine if this segment is striped or linear,
          #and note this in the new extent...
          typestring = lines[i - 1]
          if typestring.find("linear") != (-1):
            extent.set_annotation(LINEAR_MAPPING)
          elif typestring.find("Stripe") != (-1):
            typestr = typestring.strip()
            idx = typestr.find(":")
            extent.set_annotation(typestr[:idx])
          extentlist.append(extent)
          break

    ##Now, sort 
    extentlist.sort(self.sortMe)         

    ##Now fill in holes -- for each gap, create a 'free' seg block
    ##This is set up as a double loop because inserting a new val
    ##in a list probably hoses the loop iterator, so to be safe,
    ##the for loop iterator is recreated after each list insertion
    need_to_continue = TRUE
    while need_to_continue == TRUE:
      need_to_continue = FALSE
      for j in range(0, len(extentlist) - 1):
        st,sz = extentlist[j].get_start_size()
        st_next,sz_next = extentlist[j + 1].get_start_size()
        if (st + sz) == st_next:
          continue
        else:
          new_st = st + sz
          new_sz = st_next - new_st
          ex = ExtentSegment(FREE, new_st, new_sz, FALSE)
          ex.set_annotation(UNUSED_SPACE)
          extentlist.insert(0, ex)
          extentlist.sort(self.sortMe)
          need_to_continue = TRUE
          break

    #Add final free segment if necessary
    total,free,alloc = pv.get_extent_values()
    if total == free:  #Nothing in this PV is used...
      ex = ExtentSegment(FREE, 0, free, FALSE)
      ex.set_annotation(UNUSED_SPACE)
      extentlist.append(ex)
    else:
      st,sz = extentlist[len(extentlist) - 1].get_start_size()
      if (st + sz) != total:
        new_start = st + sz
        new_size = total - new_start
        ex = ExtentSegment(FREE, new_start, new_size, FALSE)
        ex.set_annotation(UNUSED_SPACE)
        extentlist.append(ex)
    
    for es in extentlist:
      pv.add_extent_segment(es)

  def sortMe(self, es1, es2):
    start1,size1 = es1.get_start_size()
    start2,size2 = es2.get_start_size()
    if start1 > start2:
      return 1
    elif start1 == start2:
      return 0
    else:
      return (-1)


