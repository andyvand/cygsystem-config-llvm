import os
import string
from gtk import TRUE, FALSE
from CommandError import CommandError
import rhpl.executil

from lvmui_constants import *

import gettext
_ = gettext.gettext

###TRANSLATOR: The first word in each string below is
###an lvm command line command phrase.
VGEXTEND_FAILURE=_("vgextend command failed. Command attempted: \"%s\"")
PVCREATE_FAILURE=_("pvcreate command failed. Command attempted: \"%s\"")
PVREMOVE_FAILURE=_("pvremove command failed. Command attempted: \"%s\"")
LVREMOVE_FAILURE=_("lvremove command failed. Command attempted: \"%s\"")
VGREMOVE_FAILURE=_("vgremove command failed. Command attempted: \"%s\"")
VGCREATE_FAILURE=_("vgcreate command failed. Command attempted: \"%s\"")
VGCHANGE_FAILURE=_("vgchange command failed. Command attempted: \"%s\"")
VGREDUCE_FAILURE=_("vgreduce command failed. Command attempted: \"%s\"")
PVMOVE_FAILURE=_("pvmove command failed. Command attempted: \"%s\"")
LV_UMOUNT_FAILURE=_("umount command failed. Command attempted: \"%s\"")

class CommandHandler:

  def __init__(self):
    pass

  def new_lv(self, cmd_args_dict):
    #first set up lvcreate args

    arglist = list()
    arglist.append("/usr/sbin/lvcreate")
    arglist.append("-n")
    arglist.append(cmd_args_dict[NEW_LV_NAME_ARG])
    if cmd_args_dict[NEW_LV_UNIT_ARG] == EXTENT_IDX:
      arglist.append("-l")
      arglist.append(str(cmd_args_dict[NEW_LV_SIZE_ARG]))
    else:
      arglist.append("-L")
      if cmd_args_dict[NEW_LV_UNIT_ARG] == KILOBYTE_IDX:
        arglist.append(str(cmd_args_dict[NEW_LV_SIZE_ARG]) + "k")
      elif cmd_args_dict[NEW_LV_UNIT_ARG] == MEGABYTE_IDX:
        arglist.append(str(cmd_args_dict[NEW_LV_SIZE_ARG]) + "m")
      elif cmd_args_dict[NEW_LV_UNIT_ARG] == GIGABYTE_IDX:
        arglist.append(str(cmd_args_dict[NEW_LV_SIZE_ARG]) + "g")

    if cmd_args_dict[NEW_LV_IS_STRIPED_ARG] == TRUE:
      arglist.append("-i")
      arglist.append(str(cmd_args_dict[NEW_LV_NUM_STRIPES_ARG]))
      arglist.append("-I")
      arglist.append(str(cmd_args_dict[NEW_LV_STRIPE_SIZE_ARG]))

    #MUST be last arg for this command block
    arglist.append(cmd_args_dict[NEW_LV_VGNAME_ARG])

    result_string = rhpl.executil.execWithCapture("/usr/sbin/lvcreate",arglist)

    ###next command

    #Now make filesystem if necessary
    if cmd_args_dict[NEW_LV_MAKE_FS_ARG] == TRUE:
      pass


  def initialize_entity(self, entity):
    commandstring = "/usr/sbin/pvcreate -M2 " + entity
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', PVCREATE_FAILURE % commandstring)

  def add_unalloc_to_vg(self, pv, vg):
    commandstring = "/usr/sbin/vgextend " + vg + " " + pv
    msg =  VGEXTEND_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def create_new_vg(self, name, max_phys, max_log, extent_size, is_unit_megs,
                    pv):

    if is_unit_megs:
      units_arg = 'm'
    else:
      units_arg = 'k'
    
    commandstring = "/usr/sbin/vgcreate -M2 -l " + max_log + " -p " + max_phys + " -s " + extent_size + units_arg + " " + name + " " + pv
    msg =  VGCREATE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def remove_vg(self, vgname):
    commandstring = "/usr/sbin/vgchange -a n " + vgname
    msg = VGCHANGE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)
      return

    commandstring = "/usr/sbin/vgremove " + vgname
    msg = VGREMOVE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def remove_pv(self, pvname):
    commandstring = "/usr/sbin/pvremove " + pvname
    msg = PVREMOVE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def remove_lv(self, lvname):
    commandstring = "/usr/sbin/lvremove --force " + lvname
    msg = LVREMOVE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def unmount_lv(self, lvname):
    commandstring = "/bin/umount " + lvname
    msg = LV_UMOUNT_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def reduce_vg(self, vg, pv):
    commandstring = "/usr/sbin/vgreduce " + vg + " " + pv
    msg = VGREDUCE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def move_pv(self, pv):
    commandstring = "/usr/sbin/pvmove " + pv
    msg = PVMOVE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def is_lv_mounted(self, lvname):
    is_mounted = FALSE
    arglist = list()
    arglist.append("/bin/cat")
    arglist.append("/proc/mounts")
    result  = rhpl.executil.execWithCapture("/bin/cat", arglist)
    textlines = result.splitlines()
    for textline in textlines:
      text_words = textline.split()
      possible_path = text_words[0].strip()
      if possible_path == lvname:
        is_mounted = TRUE
        break
    return is_mounted

  def is_dm_mirror_loaded(self):
    arglist = list()
    arglist.append("/sbin/dmsetup")
    arglist.append("targets")
    result  = rhpl.executil.execWithCapture("/sbin/dmsetup", arglist)
    textlines = result.splitlines()
    for textline in textlines:
      text_words = textline.split()
      possible_target = text_words[0].strip()
      if possible_target == "mirror":
        return TRUE

    return FALSE

