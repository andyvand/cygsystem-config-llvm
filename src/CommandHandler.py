import os
import string
from gtk import TRUE, FALSE
from CommandError import CommandError
import rhpl.executil

from lvmui_constants import *

import gettext
_ = gettext.gettext


VGEXTEND_FAILURE=_("vgextend command failed. Command attempted: \"%s\"")
PVCREATE_FAILURE=_("pvcreate command failed. Command attempted: \"%s\"")
PVREMOVE_FAILURE=_("pvremove command failed. Command attempted: \"%s\"")
VGCREATE_FAILURE=_("vgcreate command failed. Command attempted: \"%s\"")

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
      arglist.append(cmd_args_dict[NEW_LV_SIZE_ARG])
    else:
      arglist.append("-L")
    if cmd_args_dict[NEW_LV_UNIT_ARG] == KILOBYTE_IDX:
      arglist.append(str(cmd_args_dict[NEW_LV_SIZE_ARG]) + "k")
    elif cmd_args_dict[NEW_LV_UNIT_ARG] == MEGABYTE_IDX:
      arglist.append(str(cmd_args_dict[NEW_LV_SIZE_ARG]) + "m")
    elif cmd_args_dict[NEW_LV_UNIT_ARG] == GIGABYTE_IDX:
      arglist.append(int(cmd_args_dict[NEW_LV_SIZE_ARG]) + "g")

    if cmd_args_dict[NEW_LV_IS_STRIPED_ARG] == TRUE:
      arglist.append("-i")
      arglist.append(cmd_args_dict[NEW_LV_NUM_STRIPES_ARG])
      arglist.append("-I")
      arglist.append(cmd_args_dict[NEW_LV_STRIPE_SIZE_ARG])

    result_string = rhpl.executil.execWithCapture("/usr/sbin/lvcreate",arglist)
    #run command

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
                    is_resizable, is_autobackup, pv):
    if is_resizable:
      resizable_arg = 'y'
    else:
      resizable_arg = 'n'

    if is_autobackup:
      autobackup_arg = 'y'
    else:
      autobackup_arg = 'n'

    if is_unit_megs:
      units_arg = 'm'
    else:
      units_arg = 'k'
    
    commandstring = "/usr/sbin/vgcreate -M2 -l " + max_log + " -p " + max_phys + " -s " + extent_size + units_arg + " -A " + autobackup_arg + " " + name + " " + pv
    msg =  VGCREATE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)

  def remove_pv(self, pvname):
    commandstring = "/usr/sbin/pvremove " + pvname
    msg = PVREMOVE_FAILURE % commandstring
    retval = os.system(commandstring)
    if retval != 0:
      raise CommandError('FATAL', msg)
