import os
import string
from gtk import TRUE, FALSE
from CommandError import CommandError
from lvm_model import lvm_model
import rhpl.executil

from lvmui_constants import *

import gettext
_ = gettext.gettext

###TRANSLATOR: The first word in each string below is
###an lvm command line command phrase.
VGEXTEND_FAILURE=_("vgextend command failed. Command attempted: \"%s\" - System Error Message: %s")
PVCREATE_FAILURE=_("pvcreate command failed. Command attempted: \"%s\" - System Error Message: %s")
PVREMOVE_FAILURE=_("pvremove command failed. Command attempted: \"%s\" - System Error Message: %s")
LVREMOVE_FAILURE=_("lvremove command failed. Command attempted: \"%s\" - System Error Message: %s")
VGREMOVE_FAILURE=_("vgremove command failed. Command attempted: \"%s\" - System Error Message: %s")
VGCREATE_FAILURE=_("vgcreate command failed. Command attempted: \"%s\" - System Error Message: %s")
VGCHANGE_FAILURE=_("vgchange command failed. Command attempted: \"%s\" - System Error Message %s")
VGREDUCE_FAILURE=_("vgreduce command failed. Command attempted: \"%s\" - System Error Message: %s")
PVMOVE_FAILURE=_("pvmove command failed. Command attempted: \"%s\" - System Error Message: %s")
LV_UMOUNT_FAILURE=_("umount command failed. Command attempted: \"%s\" - System Error Message: %s")
FSCREATE_FAILURE=_("mkfs command failed. Command attempted: \"%s\" - System Error Message: %s")
MNTCREATE_FAILURE=_("mount command failed. Command Attempted: %s  - System Error Message: \"%s\"")

class CommandHandler:

  def __init__(self):
    pass

  def new_lv(self, cmd_args_dict):
    model_factory = lvm_model()
    #first set up lvcreate args

    arglist = list()
    arglist.append("/usr/sbin/lvcreate")
    arglist.append("-n")
    lvname = cmd_args_dict[NEW_LV_NAME_ARG]
    arglist.append(lvname)
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
    vgname = cmd_args_dict[NEW_LV_VGNAME_ARG]
    arglist.append(vgname)

    result_string,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/lvcreate",arglist)

    ###next command

    #Now make filesystem if necessary
    if cmd_args_dict[NEW_LV_MAKE_FS_ARG] == TRUE:
      lvpath = model_factory.get_logical_volume_path(lvname,vgname)

      fs_type = cmd_args_dict[NEW_LV_FS_TYPE_ARG] 
      args = list()
      args.append("/sbin/mkfs")
      args.append("-t")
      args.append(fs_type)
      args.append(lvpath)
      cmdstr = ' '.join(args)
      o,e,r = rhpl.executil.execWithCaptureErrorStatus("/sbin/mkfs",args)
      if r != 0:
        raise CommandError('FATAL', FSCREATE_FAILURE % (cmdstr,e))

      if cmd_args_dict[NEW_LV_MAKE_MNT_POINT_ARG] == TRUE:
        mnt_point =  cmd_args_dict[NEW_LV_MNT_POINT_ARG]

        cmd_args = list()
        cmd_args.append("/bin/mount")
        cmd_args.append(lvpath)
        cmd_args.append(mnt_point)
        cmdstr = ' '.join(cmd_args)
        out,err,res = rhpl.executil.execWithCaptureErrorStatus("/bin/mount",cmd_args)
        if res != 0:
          raise CommandError('FATAL', MNTCREATE_FAILURE % (cmdstr,err))


  def initialize_entity(self, entity):
    command_args = list()
    command_args.append("/usr/sbin/pvcreate")
    command_args.append("-M2")
    command_args.append(entity)
    commandstring = ' '.join(command_args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/pvcreate",command_args)
    if res != 0:
      raise CommandError('FATAL', PVCREATE_FAILURE % (commandstring,err))

  def add_unalloc_to_vg(self, pv, vg):
    args = list()
    args.append("/usr/sbin/vgextend")
    args.append(vg)
    args.append(pv)
    cmdstr = ' '.join(args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/vgextend",args)
    if res != 0:
      raise CommandError('FATAL', VGEXTEND_FAILURE % (cmdstr,err))

  def create_new_vg(self, name, max_phys, max_log, extent_size, is_unit_megs,
                    pv):

    if is_unit_megs:
      units_arg = 'm'
    else:
      units_arg = 'k'

    size_arg = extent_size + units_arg
    
    args = list()
    args.append("/usr/sbin/vgcreate")
    args.append("-M2")
    args.append("-l")
    args.append(max_log)
    args.append("-p")
    args.append(max_phys)
    args.append("-s")
    args.append(size_arg)
    args.append(name)
    args.append(pv)
    cmdstr = ' '.join(args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/vgcreate",args)
    if res != 0:
      raise CommandError('FATAL', VGCREATE_FAILURE % (cmdstr,err))

  def remove_vg(self, vgname):
    args = list()
    args.append("/usr/sbin/vgchange")
    args.append("-a")
    args.append("n")
    args.append(vgname)
    cmdstr = ' '.join(args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/vgchange",args)
    if res != 0:
      raise CommandError('FATAL', VGCHANGE_FAILURE % (cmdstr,err))
      return

    commandstring = "/usr/sbin/vgremove " + vgname
    args_list = list()
    args_list.append("/usr/sbin/vgremove")
    args_list.append(vgname)
    cmdstring = ' '.join(args)
    outs,errs,result = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/vgremove",args_list)
    if result != 0:
      raise CommandError('FATAL', VGREMOVE_FAILURE % (cmdstring,errs))

  def remove_pv(self, pvname):
    args = list()
    args.append("/usr/sbin/pvremove")
    args.append(pvname)
    cmdstr = ' '.join(args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/pvremove",args)
    if res != 0:
      raise CommandError('FATAL', PVREMOVE_FAILURE % (cmdstr,err))

  def remove_lv(self, lvname):
    args = list()
    args.append("/usr/sbin/lvremove")
    args.append("--force")
    args.append(lvname)
    cmdstr = ' '.join(args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/lvremove",args)
    if res != 0:
      raise CommandError('FATAL', LVREMOVE_FAILURE % (cmdstr,err))

  def unmount_lv(self, lvname):
    args = list()
    args.append("/bin/umount")
    args.append(lvname)
    cmdstr = ' '.join(args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/bin/umount",args)
    if res != 0:
      raise CommandError('FATAL', LV_UMOUNT_FAILURE % (cmdstr,err))

  def reduce_vg(self, vg, pv):
    args = list()
    args.append("/usr/sbin/vgreduce")
    args.append(vg)
    args.append(pv)
    cmdstr = ' '.join(args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/vgreduce",args)
    if res != 0:
      raise CommandError('FATAL', VGREDUCE_FAILURE % (cmdstr,err))

  def move_pv(self, pv):
    args = list()
    args.append("/usr/sbin/pvmove")
    args.append(pv)
    cmdstr = ' '.join(args)
    out,err,res = rhpl.executil.execWithCaptureErrorStatus("/usr/sbin/pvmove",args)
    if res != 0:
      raise CommandError('FATAL', PVMOVE_FAILURE % (cmdstr,err))

  def is_lv_mounted(self, lvname):
    is_mounted = FALSE
    mount_point = ""
    filesys = ""
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
        mount_point = text_words[1]
        filesys = text_words[2]
        break
    return is_mounted,mount_point,filesys

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

      
