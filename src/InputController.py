"""This class represents the primary controller interface
   for the LVM UI application.
"""
__author__ = 'Jim Parsons (jparsons@redhat.com)'


import string
import os
import stat
import os.path
import gobject
from lvm_model import lvm_model
from CommandHandler import CommandHandler
from lvmui_constants import *
from CommandError import CommandError
import gettext
_ = gettext.gettext

### gettext first, then import gtk (exception prints gettext "_") ###
try:
    import gtk
    import gtk.glade
except RuntimeError, e:
    print _("""
  Unable to initialize graphical environment. Most likely cause of failure
  is that the tool was not run using a graphical environment. Please either
  start your graphical user interface or set your DISPLAY variable.
                                                                                
  Caught exception: %s
""") % e
    sys.exit(-1)
                                                                                
import gnome
import gnome.ui

SIZE_COL = TYPE_COL
VOL_TYPE_COL = 3

UNALLOC_VOL = 0
UNINIT_VOL = 1

###TRANSLATOR: The string below is seen when adding a new Physical
###Volume to an existing Volume Group.
ADD_PV_TO_VG_LABEL=("Select a Volume Group to add %s to:")

MEGA_MULTIPLIER = 1000000.0
GIGA_MULTIPLIER = 1000000000.0
KILO_MULTIPLIER = 1000.0

DEFAULT_STRIPE_SIZE_IDX = 4

MAX_PHYSICAL_VOLS = 256
MAX_LOGICAL_VOLS = 256
DEFAULT_EXTENT_SIZE = 4
DEFAULT_EXTENT_SIZE_MEG_IDX = 1
DEFAULT_EXTENT_SIZE_KILO_IDX = 2

#######################################################
## Note, please: The two hash maps below are related. #
## When adding or removing a filesystem type, both    #
## hashes must be updated. The values in the first,   #
## are the keys of the second.                        #
## The FS type names are globalized strings in        #
## lvmui_constants.py                                 #
                                                      #
MKFS_HASH = { 'mkfs.ext2':EXT2_T,                     #
              'mkfs.ext3':EXT3_T,                     #
#              'mkfs.jfs':JFS_T,                      #
#              'mkfs.msdos':MSDOS_T,                  #
#              'mkfs.reiserfs':REISERFS_T,            #
#              'mkfs.vfat':VFAT_T,                    #
#              'mkfs.xfs':XFS_T,                      #
#              'mkfs.cramfs':CRAMFS_T                 #
            }                                         #
                                                      #
FS_HASH = { EXT2_T:'ext2',                            #
            EXT3_T:'ext3',                            #
#            JFS_T:'jfs',                             #
#            MSDOS_T:'msdos',                         #
#            REISERFS_T:'reiserfs',                   #
#            VFAT_T:'vfat',                           #
#            XFS_T:'xfs',                             #
#            CRAMFS_T:'cramfs'                        #
           }                                          #
                                                      #
#######################################################

NO_FILESYSTEM_FS = 0

ACCEPTABLE_STRIPE_SIZES = [4,8,16,32,64,128,256,512]

ACCEPTABLE_EXTENT_SIZES = ["2","4","8","16","32","64","128","256","512","1024"]

###TRANSLATOR: The two strings below refer to the name and type of
###available disk entities on the system. There are two types --
###The first is an 'unallocated physical volume' which is a disk or
###partition that has been initialized for use with LVM, by writing
###a special label onto the first block of the partition. The other type
###is an 'uninitialized entity', which is an available disk or partition
###that is NOT yet initialized to be used with LVM. Hope this helps give
###some context.
ENTITY_NAME=_("Name")
ENTITY_SIZE=_("Size")
ENTITY_TYPE=_("Entity Type")

UNALLOCATED_PV=_("Unallocated Physical Volume")
UNINIT_DE=_("Uninitialized Disk Entity") 
ADD_VG_LABEL=_("Select a disk entity to add to the %s Volume Group:")

CANT_STRIPE_MESSAGE=_("A Volume Group must be made up of two or more Physical Volumes to support striping. This Volume Group does not meet that requirement.")

NON_UNIQUE_NAME=_("A Logical Volume with the name %s already exists in this Volume Group. Please choose a unique name.")

NON_UNIQUE_VG_NAME=_("A Volume Group with the name %s already exists. Please choose a unique name.")

MUST_PROVIDE_NAME=_("A Name must be provided for the new Logical Volume")

MUST_PROVIDE_VG_NAME=_("A Name must be provided for the new Volume Group")

BAD_MNT_POINT=_("The specified mount point, %s, does not exist. Do you wish to create it?")

BAD_MNT_CREATION=_("The creation of mount point %s unexpectedly failed.")

NOT_IMPLEMENTED=_("This capability is not yet implemented in this version")

EXCEEDED_MAX_PVS=_("The number of Physical Volumes in this Volume Group has reached its maximum limit.")

EXCEEDED_MAX_LVS=_("The number of Logical Volumes in this Volume Group has reached its maximum limit.")

TYPE_CONVERSION_ERROR=_("Undefined type conversion error in model factory. Unable to complete task.")

NUMERIC_CONVERSION_ERROR=_("There is a problem with the value entered in the Size field. The value should be a numeric value with no alphabetical characters or symbols of any other kind.")

MOUNTED_WARNING=_("BIG WARNING: Logical Volume %s has an %s file system on it and is currently mounted on %s. Are you absolutely certain that you wish to discard the data on this mounted filesystem?")

###TRANSLATOR: An extent below is an abstract unit of storage. The size
###of an extent is user-definable.
REMAINING_SPACE_VGNAME=_("Unused space on %s")
REMAINING_SPACE_MEGABYTES=_("%s megabytes")
REMAINING_SPACE_KILOBYTES=_("%s kilobytes")
REMAINING_SPACE_GIGABYTES=_("%s gigabytes")
REMAINING_SPACE_EXTENTS=_("%s extents")

EXCEEDS_FREE_SPACE=_("The size requested for the new Logical Volume exceeds the available free space on Volume Group %s. The available space is: ")

NUMBERS_ONLY=_("The %s should only contain number values")
NUMBERS_ONLY_MAX_PVS=_("The  Maximum Physical Volumes field should contain only integer values between 1 and 256")
NUMBERS_ONLY_MAX_LVS=_("The  Maximum Logical Volumes field should contain only integer values between 1 and 256")

###TRANSLATOR: Striping writes data to multiple physical devices 
###concurrently, with the objective being redundance and/or speed
STRIPE_SIZE_FIELD=_("Stripe Size field")
NUM_STRIPES_FIELD=_("Number of Stripes field")

CONFIRM_PVREMOVE=_("Are you quite certain that you wish to remove %s from Logical Volume Management?")

SOLO_PV_IN_VG=_("The Physical Volume named %s, that you wish to remove, has data from active Logical Volume(s) mapped to its extents. Because it is the only Physical Volume in the Volume Group, there is no place to move the data. Recommended action is either to add a new Physical Volume before removing this one, or else remove the Logical Volumes that are associated with this Physical Volume.") 
CONFIRM_PV_VG_REMOVE=_("Are you quite certain that you wish to remove %s from the %s Volume Group?")
CONFIRM_VG_REMOVE=_("Removing Physical Volume %s from the Volume Group %s will leave the Volume group empty, and it will be removed as well. Do you wish to proceed?")
CONFIRM_LV_REMOVE=_("Are you quite certain that you wish to remove the Logical Volume %s?")
NOT_ENOUGH_SPACE_VG=_("Volume Group %s does not have enough space to move the data stored on %s. A possible solution would be to add an additional Physical Volume to the Volume Group.")
NO_DM_MIRROR=_("The dm-mirror module is either not loaded in your kernel, or your kernel does not support the dm-mirror target. If it is supported, try running \"modprobe dm-mirror\". Otherwise, operations that require moving data on Physical Extents are unavailable.")
###########################################################
class InputController:
  def __init__(self, reset_tree_model, treeview, model_factory, glade_xml):
    self.reset_tree_model = reset_tree_model
    self.treeview = treeview
    self.model_factory = model_factory
    self.glade_xml = glade_xml

    self.command_handler = CommandHandler()
    self.section_list = list()
    self.section_type = UNSELECTABLE_TYPE
    self.use_remaining = 0 #This global :( is used as a flag for the new lv form
    self.loaded_field = 0  #This one too

    self.setup_dialogs()

  def setup_dialogs(self):
    self.init_entity_button = self.glade_xml.get_widget('uninit_button')
    self.init_entity_button.connect("clicked", self.on_init_entity)

    self.setup_new_vg_form()
    #self.setup_pv_rm_migrate()
    #self.setup_pv_rm()

    ###################
    ##This form adds an unallocated PV to a VG
    self.add_pv_to_vg_dlg = self.glade_xml.get_widget('add_pv_to_vg_form')
    self.add_pv_to_vg_dlg.connect("delete_event",self.add_pv_to_vg_delete_event)
    self.add_pv_to_vg_button = self.glade_xml.get_widget('add_pv_to_vg_button')
    self.add_pv_to_vg_button.connect("clicked",self.on_add_pv_to_vg)
    self.add_pv_to_vg_treeview = self.glade_xml.get_widget('add_pv_to_vg_treeview')
    self.ok_add_pv_to_vg_button = self.glade_xml.get_widget('ok_add_pv_to_vg_button')
    self.ok_add_pv_to_vg_button.connect("clicked",self.on_ok_add_pv_to_vg)
    self.cancel_add_pv_to_vg_button = self.glade_xml.get_widget('cancel_add_pv_to_vg_button')
    self.cancel_add_pv_to_vg_button.connect("clicked",self.on_cancel_add_pv_to_vg)
    self.add_pv_to_vg_label = self.glade_xml.get_widget('add_pv_to_vg_label')
    model = gtk.ListStore (gobject.TYPE_STRING,
                           gobject.TYPE_STRING)
    self.add_pv_to_vg_treeview.set_model(model)
    renderer1 = gtk.CellRendererText()
    column1 = gtk.TreeViewColumn("Volume Groups",renderer1, text=0)
    self.add_pv_to_vg_treeview.append_column(column1)
    renderer2 = gtk.CellRendererText()
    column2 = gtk.TreeViewColumn("Size",renderer2, text=1)
    self.add_pv_to_vg_treeview.append_column(column2)

    self.setup_new_lv_form()
    self.setup_extend_vg_form()
    self.setup_misc_widgets()

  ##################
  ##This form adds a new VG
  def setup_new_vg_form(self):
    self.new_vg_dlg = self.glade_xml.get_widget('new_vg_form')
    self.new_vg_dlg.connect("delete_event",self.new_vg_delete_event)
    self.new_vg_button = self.glade_xml.get_widget('new_vg_button')
    self.new_vg_button.connect("clicked", self.on_new_vg)
    self.ok_new_vg_button = self.glade_xml.get_widget('ok_new_vg_button')
    self.ok_new_vg_button.connect("clicked",self.ok_new_vg)
    self.cancel_new_vg_button = self.glade_xml.get_widget('cancel_new_vg_button')
    self.cancel_new_vg_button.connect("clicked", self.cancel_new_vg)

    ##Buttons and fields...
    self.new_vg_name = self.glade_xml.get_widget('new_vg_name')
    self.new_vg_max_pvs = self.glade_xml.get_widget('new_vg_max_pvs')
    self.new_vg_max_lvs = self.glade_xml.get_widget('new_vg_max_lvs')
    self.new_vg_extent_size = self.glade_xml.get_widget('new_vg_extent_size')
    self.new_vg_radio_meg = self.glade_xml.get_widget('radiobutton1')
    self.new_vg_radio_meg.connect('clicked', self.change_new_vg_radio)
    self.new_vg_radio_kilo = self.glade_xml.get_widget('radiobutton2')

  def on_new_vg(self, button):
    self.prep_new_vg_dlg()
    self.new_vg_dlg.show()
                                                                                
  def cancel_new_vg(self, button):
    self.new_vg_dlg.hide()

  def ok_new_vg(self, button):
    Name_request = ""
    max_physical_volumes = 256
    max_logical_volumes = 256
    phys_extent_size = 8
    phys_extent_units_meg = True
    autobackup = True
    resizable = True

    selection = self.treeview.get_selection()
    model,iter = selection.get_selected()
    pv_name = model.get_value(iter, PATH_COL)

    proposed_name = self.new_vg_name.get_text().strip()
    if proposed_name == "":
      self.errorMessage(MUST_PROVIDE_VG_NAME)
      return

    #Now check for unique name
    vg_list = self.model_factory.query_VGs()
    for vg in vg_list:
      if vg.get_name().strip() == proposed_name:
        self.new_vg_name.select_region(0, (-1))
        self.errorMessage(NON_UNIQUE_VG_NAME % proposed_name)
        return
    Name_request = proposed_name

    max_pvs_field = self.new_vg_max_pvs.get_text()
    if max_pvs_field.isalnum() == False:
      self.errorMessage(NUMBERS_ONLY_MAX_PVS)
      self.new_vg_max_pvs.set_text(str(MAX_PHYSICAL_VOLS))
      return
    else:
      max_pvs = int(max_pvs_field)
      if (max_pvs < 1) or (max_pvs > MAX_PHYSICAL_VOLS):
        self.errorMessage(NUMBERS_ONLY_MAX_PVS)
        self.new_vg_max_pvs.set_text(str(MAX_PHYSICAL_VOLS))
        return
      max_physical_volumes = max_pvs

    max_lvs_field = self.new_vg_max_lvs.get_text()
    if max_lvs_field.isalnum() == False:
      self.errorMessage(NUMBERS_ONLY_MAX_LVS)
      self.new_vg_max_lvs.set_text(str(MAX_LOGICAL_VOLS))
      return
    else:
      max_lvs = int(max_lvs_field)
      if (max_lvs < 1) or (max_lvs > MAX_LOGICAL_VOLS):
        self.errorMessage(NUMBERS_ONLY_MAX_LVS)
        self.new_vg_max_lvs.set_text(str(MAX_LOGICAL_VOLS))
        return
      max_logical_volumes = max_lvs

    extent_idx = self.new_vg_extent_size.get_history()
    phys_extent_units_meg =  self.new_vg_radio_meg.get_active()

    try:
      self.command_handler.create_new_vg(Name_request,
                                         str(max_physical_volumes),
                                         str(max_logical_volumes),
                                         ACCEPTABLE_EXTENT_SIZES[extent_idx],
                                         phys_extent_units_meg,
                                         pv_name)
    except CommandError, e:
      self.errorMessage(e.getMessage())

    self.new_vg_dlg.hide()

    args = list()
    args.append(pv_name.strip())
    apply(self.reset_tree_model, args)

  def prep_new_vg_dlg(self):
    self.new_vg_name.set_text("")
    self.new_vg_max_pvs.set_text(str(MAX_PHYSICAL_VOLS))
    self.new_vg_max_lvs.set_text(str(MAX_LOGICAL_VOLS))
    self.new_vg_radio_meg.set_active(True)
    self.new_vg_extent_size.set_history(DEFAULT_EXTENT_SIZE_MEG_IDX)

  def change_new_vg_radio(self, button):
    menu = self.new_vg_extent_size.get_menu()
    items = menu.get_children()
    #We don't want to offer the 2 and 4 options for kilo's - min size is 8k
    if self.new_vg_radio_meg.get_active() == True:
      items[0].set_sensitive(True)
      items[1].set_sensitive(True)
      self.new_vg_extent_size.set_history(DEFAULT_EXTENT_SIZE_MEG_IDX)
    else:
      items[0].set_sensitive(False)
      items[1].set_sensitive(False)
      self.new_vg_extent_size.set_history(DEFAULT_EXTENT_SIZE_KILO_IDX)

  def on_pv_rm(self, button):
    self.remove_pv()

  def remove_pv(self, pvname=None):
    #The following cases must be considered in this method:
    #1) a PV is to be removed that has extents mapped to an LV:
    #  1a) if there are other PVs, call pvmove on the PV to migrate the 
    #      data to other  PVs in the VG
    #      i) If there is sufficient room, pvmove the extents, then vgreduce
    #      ii) If there is not room, inform the user to add more storage and
    #           try again later
    #  1b) If there are not other PVs, state that either more PVs must
    #      be added so that the in use extents can be migrated, or else
    #      present a list of LVs that must be removed in order to 
    #      remove the PV
    #2) a PV is to be removed that has NO LVs mapped to its extents:
    #  2a) If there are more than one PV in the VG, just vgreduce away the PV
    #  2b) If the PV is the only one, then vgremove the VG
    #
    mapped_lvs = True
    solo_pv = False
    reset_tree = False
    if pvname == None:
      reset_tree = True #This says that tree reset will not be handled by caller
      selection = self.treeview.get_selection()
      model, iter = selection.get_selected()
      name = model.get_value(iter, PATH_COL)
      pvname = name.strip()

    ###FIX This method call needs to be handled for exception
    pv = self.model_factory.get_PV(pvname)
    extent_list = pv.get_extent_segments()

    vgname = pv.get_vg_name().strip()
    total,free,alloc = pv.get_extent_values()
    pv_list = self.model_factory.query_PVs_for_VG(vgname)
    if len(pv_list) <= 1: #This PV is the only one in the VG
      solo_pv = True
    else:
      solo_pv = False

    if len(extent_list) == 1: #There should always be at least one extent seg
      #We now know either the entire PV is used by one LV, or else it is
      #an unutilized PV. If the latter, we can just vgreduce it away 
      seg_name = extent_list[0].get_name()
      if (seg_name == FREE) or (seg_name == UNUSED):
        mapped_lvs = False
      else:
        mapped_lvs = True
    else:
      mapped_lvs = True

    #Cases:
    if mapped_lvs == False:
      if solo_pv == True:
        #call vgremove
        retval = self.warningMessage(CONFIRM_VG_REMOVE % (pvname,vgname))
        if (retval == gtk.RESPONSE_NO):
          return
        try:
          self.command_handler.remove_vg(vgname)
        except CommandError, e:
          self.errorMessage(e.getMessage())
          return

      else: #solo_pv is False, more than one PV...
        retval = self.warningMessage(CONFIRM_PV_VG_REMOVE % (pvname,vgname))
        if (retval == gtk.RESPONSE_NO):
          return
        try:
          self.command_handler.reduce_vg(vgname, pvname)
        except CommandError, e:
          self.errorMessage(e.getMessage())
          return
    else:
      #Two cases here: if solo_pv, bail, else check for size needed
      if solo_pv == True:
        self.errorMessage(SOLO_PV_IN_VG % pvname)
        return
      else: #There are additional PVs. We need to check space 
        size, ext_count = self.model_factory.get_free_space_on_VG(vgname, "m")
        actual_free_exts = int(ext_count) - free
        if alloc <= actual_free_exts:
          if self.command_handler.is_dm_mirror_loaded() == False:
            self.errorMessage(NO_DM_MIRROR)
            return
          retval = self.warningMessage(CONFIRM_PV_VG_REMOVE % (pvname,vgname))
          if (retval == gtk.RESPONSE_NO):
            return
          try:
            self.command_handler.move_pv(pvname)
          except CommandError, e:
            self.errorMessage(e.getMessage())
            return

          try:
            self.command_handler.reduce_vg(vgname, pvname)
          except CommandError, e:
            self.errorMessage(e.getMessage())
            return

        else:
          self.errorMessage(NOT_ENOUGH_SPACE_VG % (vgname,pvname))
          return


    if reset_tree == True:
      args = list()
      args.append(vgname)
      apply(self.reset_tree_model, args)
    else:
      return vgname

  def on_lv_rm(self, button):
    self.remove_lv()

  def remove_lv(self, lvname=None):
    reset_tree = False
    if lvname == None:
      reset_tree = True
      selection = self.treeview.get_selection()
      model, iter = selection.get_selected()
      name = model.get_value(iter, PATH_COL)
      lvname = name.strip()

    retval = self.warningMessage(CONFIRM_LV_REMOVE % lvname)
    if (retval == gtk.RESPONSE_NO):
      return

    else:
      #Check if LV is mounted -- if so, unmount
      is_mounted,mnt_point,filesys = self.command_handler.is_lv_mounted(lvname)


    if is_mounted == True:
      retval = self.warningMessage(MOUNTED_WARNING % (lvname,filesys,mnt_point))
      if (retval == gtk.RESPONSE_NO):
        return

      try:
        self.command_handler.unmount_lv(lvname)
      except CommandError, e:
        self.errorMessage(e.getMessage())
        return

    try:
      self.command_handler.remove_lv(lvname)
    except CommandError, e:
      self.errorMessage(e.getMessage())
      return

    #args = list()
    #args.append(lvname)
    #apply(self.reset_tree_model, args)
    if reset_tree == True:
      apply(self.reset_tree_model)

  def on_rm_select_lvs(self, button):
    if self.section_list == None:
      return
    #check if list > 0
    if len(self.section_list) == 0:
      return 
    #need to check if section is 'unused'
    for item in self.section_list:
      if item.is_vol_utilized == False:
        continue
      lvname = item.get_path().strip()
      self.remove_lv(lvname)


      #args = list()
      #args.append(lvname)
      #apply(self.reset_tree_model, args)
    self.clear_highlighted_sections()
    apply(self.reset_tree_model)

  def on_rm_select_pvs(self, button):
    if self.section_list == None:
      return
    #need tto check if list > 0
    if len(self.section_list) == 0:
      return 
    selection = self.treeview.get_selection()
    model,iter = selection.get_selected()
    vgname = model.get_value(iter, PATH_COL).strip()
    #need to check if section is 'unused'
    for item in self.section_list:
      pvname = item.get_path().strip()
      self.remove_pv(pvname)

    self.clear_highlighted_sections()
    args = list()
    args.append(vgname)
    apply(self.reset_tree_model,args)
    #apply(self.reset_tree_model)

  ###################
  ##This form adds a new Logical Volume
  def setup_new_lv_form(self):
    self.new_lv_dlg = self.glade_xml.get_widget('new_lv_form')
    self.new_lv_button = self.glade_xml.get_widget('new_lv_button')
    self.new_lv_button.connect("clicked",self.on_new_lv)
    self.ok_new_lv_button = self.glade_xml.get_widget('ok_new_lv_button')
    self.ok_new_lv_button.connect("clicked",self.on_ok_new_lv_button)
    self.cancel_new_lv_button = self.glade_xml.get_widget('cancel_new_lv_button')
    self.cancel_new_lv_button.connect("clicked",self.on_cancel_new_lv_button)

    ##Fields and menus
    self.new_lv_name = self.glade_xml.get_widget('new_lv_name')
    self.new_lv_size = self.glade_xml.get_widget('new_lv_size')
    self.new_lv_size.connect('changed',self.unset_use_remaining_flag)
    self.new_lv_size_unit = self.glade_xml.get_widget('new_lv_size_unit')
    self.new_lv_size_unit.connect('changed', self.change_new_lv_size_unit)
    self.unused_space_label1 = self.glade_xml.get_widget('unused_space_label1')
    self.unused_space_label2 = self.glade_xml.get_widget('unused_space_label2')
    self.new_lv_remaining_space = self.glade_xml.get_widget('new_lv_remaining_space')
    self.new_lv_remaining_space.connect("clicked",self.on_new_lv_remaining_space)
    self.new_lv_linear_radio = self.glade_xml.get_widget('radiobutton5')
    self.new_lv_linear_radio.connect("clicked",self.change_new_lv_radio)
    self.new_lv_striped_radio = self.glade_xml.get_widget('radiobutton6')
    self.new_lv_num_stripes_label =  self.glade_xml.get_widget('new_lv_num_stripes_label')
    self.new_lv_stripe_spinner = self.glade_xml.get_widget('stripe_spinner')
    self.new_lv_stripe_size = self.glade_xml.get_widget('new_lv_stripe_size')
    self.new_lv_stripe_size_label = self.glade_xml.get_widget('new_lv_stripe_size_label')
    self.new_lv_kilobytes_label = self.glade_xml.get_widget('kilobytes_label')
    self.new_lv_fs_menu = self.glade_xml.get_widget('fs_menu')
    self.new_lv_fs_menu.connect('changed', self.change_new_lv_fs)
    self.new_lv_mnt_point = self.glade_xml.get_widget('new_lv_mnt_point')
    self.new_lv_mnt_point_label = self.glade_xml.get_widget('new_lv_mnt_point_label')

    self.prep_new_lv_dlg()

  def on_new_lv(self, button):
    main_selection = self.treeview.get_selection()
    main_model,main_iter = main_selection.get_selected()
    main_path = main_model.get_path(main_iter)
    vgname = main_model.get_value(main_iter,PATH_COL).strip()
    try:
      max_lvs,lvs,max_pvs,pvs = self.model_factory.get_max_LVs_PVs_on_VG(vgname)
    except ValueError, e:
      self.errorMessage(TYPE_CONVERSION_ERROR % e)
      return
    if max_lvs == lvs:
      self.errorMessage(EXCEEDED_MAX_LVS)
      return

    self.prep_new_lv_dlg()
    self.new_lv_dlg.show()

  def prep_new_lv_dlg(self):
    self.use_remaining = 0
    self.loaded_field = 0
    #Get available space on vg and set as label
    selection = self.treeview.get_selection()
    model, iter = selection.get_selected()
    if iter != None:
      vgname = model.get_value(iter, PATH_COL).strip()
      free_space,free_extents = self.model_factory.get_free_space_on_VG(vgname,"m")
      free_space_bytes,free_ex = self.model_factory.get_free_space_on_VG(vgname,"b")
      if free_extents != None:
        self.free_space_bytes = free_space_bytes
        self.free_space = free_space
        self.free_extents = free_ex
        self.unused_space_label1.set_text(REMAINING_SPACE_VGNAME % vgname)
        self.unused_space_label2.set_text(REMAINING_SPACE_EXTENTS % free_ex)
      else:
        self.free_space_bytes = 0
        self.free_space = 0
        self.unused_space_label1.set_text("")
        self.unused_space_label2.set_text("")
        
    self.new_lv_name.set_text("")
    self.new_lv_size.set_text("")
    self.new_lv_size_unit.set_history(EXTENT_IDX)

    #set radiobutton group to linear
    self.new_lv_linear_radio.set_active(True) 
    self.new_lv_stripe_size.set_history(DEFAULT_STRIPE_SIZE_IDX)
    self.new_lv_stripe_spinner.set_value(2.0)

    #set up filesystem menu
    self.prep_filesystem_menu()

    #deactivate #mount point field
    self.new_lv_mnt_point.set_text("")

    self.change_new_lv_fs(None, None)
    self.change_new_lv_radio(None)

  def prep_filesystem_menu(self):
    menu = gtk.Menu()
    #First item must be 'No Filesystem' option
    m = gtk.MenuItem(NO_FILESYSTEM)
    m.show()
    menu.append(m)

    mkfs_list = MKFS_HASH.keys()
    for item in mkfs_list:
      stat_string = "/sbin/" + item
      try:
        mode = os.stat(stat_string)[stat.ST_MODE]
      except OSError, e:
        continue  #Means we did not find the mkfs varient in item present
      m = gtk.MenuItem(MKFS_HASH[item])
      m.show()
      menu.append(m)

    self.new_lv_fs_menu.set_menu(menu)

    self.new_lv_fs_menu.set_history(NO_FILESYSTEM_FS)

  def on_ok_new_lv_button(self, button):
    Name_request = ""
    VG_Name = ""
    Size_request = 0
    Unit_index = (-1)
    Striped = False
    Stripe_size = 64
    Num_stripes = 2
    Make_filesystem = False
    FS_type = ""
    Mount_filesystem = False
    Mount_point = ""
    FSTAB_entry = False
    
    #Validation Ladder:
    #Name must be unique for this VG
    proposed_name = self.new_lv_name.get_text().strip()
    if proposed_name == "":
      self.errorMessage(MUST_PROVIDE_NAME)
      return 
    selection = self.treeview.get_selection()
    model, iter = selection.get_selected()
    if iter != None:
      vgname = model.get_value(iter, PATH_COL).strip()
      self.model_factory.get_VG(vgname)
      lv_list = self.model_factory.query_LVs_for_VG(vgname)
      for lv in lv_list:
        if lv.get_name() == proposed_name:
          self.new_lv_name.select_region(0, (-1))
          self.errorMessage(NON_UNIQUE_NAME % proposed_name)
          return

    VG_Name = vgname
    Name_request = proposed_name

    #ok - name is ok. size must be below available space
    prop_size = self.new_lv_size.get_text()
    try:  ##In case gibberish is entered into the size field...
      float_proposed_size = float(prop_size)
      int_proposed_size = int(float_proposed_size)
    except ValueError, e: 
      self.errorMessage(NUMERIC_CONVERSION_ERROR % e)
      self.new_lv_size.set_text("")
      return

    #Now we have an integer representation of our size field,
    #and a floating point rep
    #Normalize size depending on size_unit index
    Unit_index = self.new_lv_size_unit.get_history()
    Size_request = 0

    if self.use_remaining > 0: #This means the 'use remaining space button' used
      Unit_index = EXTENT_IDX
      Size_request = self.use_remaining
    else:
      if Unit_index == EXTENT_IDX:
        if int(self.free_extents) < int_proposed_size:
          self.errorMessage((EXCEEDS_FREE_SPACE % vgname) + 
                            (REMAINING_SPACE_EXTENTS % self.free_extents)) 
          self.new_lv_size.set_text("")
          return
        Size_request = int_proposed_size

      elif Unit_index == MEGABYTE_IDX:
          normalized_size = float_proposed_size * MEGA_MULTIPLIER
          if float(self.free_space_bytes) < normalized_size:
            self.errorMessage((EXCEEDS_FREE_SPACE % vgname) +
                              (REMAINING_SPACE_MEGABYTES % self.free_space))
            self.new_lv_size.set_text("")
            return
          Size_request = float_proposed_size
          
      elif Unit_index == GIGABYTE_IDX:
          normalized_size = float_proposed_size * GIGA_MULTIPLIER
          if float(self.free_space_bytes) < normalized_size:
            self.errorMessage((EXCEEDS_FREE_SPACE % vgname) +
                              (REMAINING_SPACE_GIGABYTES % self.free_space))
            self.new_lv_size.set_text("")
            return
          Size_request = float_proposed_size
          
      elif Unit_index == KILOBYTE_IDX:
          normalized_size = float_proposed_size * KILO_MULTIPLIER
          if float(self.free_space_bytes) < normalized_size:
            self.errorMessage((EXCEEDS_FREE_SPACE % vgname) +
                              (REMAINING_SPACE_KILOBYTES % self.free_space))
            self.new_lv_size.set_text("")
            return
          Size_request = float_proposed_size
          


    #Handle stripe request
    if self.new_lv_striped_radio.get_active() == True:
      Striped = True
      num_stripes_str = str(self.new_lv_stripe_spinner.get_text())
      if num_stripes_str.isalnum():
        Num_stripes = int(num_stripes_str)
      else:
        self.errorMessage(NUMBERS_ONLY % NUM_STRIPES_FIELD)
        self.new_lv_stripe_spinner.set_value(2.0)
        return

      stripe_size_index = self.new_lv_stripe_size.get_history()
      Stripe_size = ACCEPTABLE_STRIPE_SIZES[stripe_size_index]


    #Finally, address file system issues
    fs_idx = self.new_lv_fs_menu.get_history()
    desired_fs_type = self.new_lv_fs_menu.get_children()[0].get()
    if fs_idx > 0:
      Make_filesystem = True
      #FS_type = FILE_SYSTEM_TYPE_LIST[fs_idx] 
      FS_type = FS_HASH[desired_fs_type] 
      if self.new_lv_mnt_point.get_text() != "":
        Mount_filesystem = True
        Mount_point = self.new_lv_mnt_point.get_text()
        if os.path.exists(Mount_point) == False:  ###stat mnt point
          rc = self.infoMessage(BAD_MNT_POINT % Mount_point)
          if (rc == gtk.RESPONSE_YES):  #create mount point
            try:
              os.mkdir(Mount_point)
            except OSError, e:
              self.errorMessage(BAD_MNT_CREATION % Mount_point)
              self.new_lv_mnt_point.set_text("")
              return 
          else:
            self.new_lv_mnt_point.select_region(0, (-1))
            return

    #Build command args
    new_lv_command_set = {}
    new_lv_command_set[NEW_LV_NAME_ARG] = Name_request
    new_lv_command_set[NEW_LV_VGNAME_ARG] = VG_Name
    new_lv_command_set[NEW_LV_UNIT_ARG] = Unit_index
    new_lv_command_set[NEW_LV_SIZE_ARG] = Size_request
    new_lv_command_set[NEW_LV_IS_STRIPED_ARG] = Striped
    if Striped == True:
      new_lv_command_set[NEW_LV_STRIPE_SIZE_ARG] = Stripe_size
      new_lv_command_set[NEW_LV_NUM_STRIPES_ARG] = Num_stripes
    new_lv_command_set[NEW_LV_MAKE_FS_ARG] = Make_filesystem
    if Make_filesystem == True:
      new_lv_command_set[NEW_LV_FS_TYPE_ARG] = FS_type
    new_lv_command_set[NEW_LV_MAKE_MNT_POINT_ARG] = Mount_filesystem
    if Mount_filesystem == True:
      new_lv_command_set[NEW_LV_MNT_POINT_ARG] = Mount_point
      if FSTAB_entry == True:
        new_lv_command_set[NEW_FSTAB_ARG] = FSTAB_entry
    
    try:    
      self.command_handler.new_lv(new_lv_command_set)
    except CommandError, e:
      self.errorMessage(e.getMessage())

    #Add confirmation dialog here... 
    args = list()
    args.append(Name_request)
    args.append(VG_Name)
    self.new_lv_dlg.hide()
    apply(self.reset_tree_model, args)

  def on_cancel_new_lv_button(self, button):
    self.new_lv_dlg.hide()

  #The following two methods are related. Here is how:
  #There is a button on the new_lv_dlg form that allows
  #the user to use all of the remaining space on the VG
  #for their new LV. This is implemented by setting the size
  #text entry field with the remaining space value, in whatever unit
  #you happen to be working in according to the unit selection menu.
  #Sending this value as a param to lvcreate when it is a floating
  #point value, though, is problematic; so we will use a discrete value 
  #(free extents) instead. By setting the flag 'self.use_remaining'
  #to the amount of extents available, we can check in the on_ok
  #method for a value greater than zero, and send the size in 
  #extents to the command handler. A problem can occur, though,
  #when the user presses the 'use remaining space' button, and 
  #then modify's the amount in the text field. The handler method
  #immediately below resets the flag to 0, if chars in the text
  #field are deleted, or new ones inserted.
  #
  #Of course, the act of loading the max value into the field is 
  #considered a 'change' so this must be trapped, and is what the 
  #self.loaded_field flag is for. It can only be set by the 
  #button handler.
  def unset_use_remaining_flag(self, *args):
    if self.loaded_field == 0:
      self.use_remaining = 0
    else:
      self.loaded_field = 0

  def on_new_lv_remaining_space(self,button):
    unit_index = self.new_lv_size_unit.get_history()
    if unit_index == MEGABYTE_IDX:
      unit_str = "m"
    elif unit_index == KILOBYTE_IDX:
      unit_str = "k"
    elif unit_index == GIGABYTE_IDX:
      unit_str = "g"
    else:
      unit_str = "m"
    selection = self.treeview.get_selection()
    model, iter = selection.get_selected()
    if iter != None:
      vgname = model.get_value(iter, PATH_COL).strip()
      free_space,free_extents = self.model_factory.get_free_space_on_VG(vgname,unit_str)
      free_space_bytes,free_extents = self.model_factory.get_free_space_on_VG(vgname,"b")
      self.free_space_bytes = free_space_bytes
      self.free_space = free_space
      self.free_extents = free_extents
      self.use_remaining = free_extents
      self.loaded_field = 1

    if unit_index == EXTENT_IDX:
      self.new_lv_size.set_text(free_extents)
    else:
      self.new_lv_size.set_text(free_space)
    

  def change_new_lv_radio(self, button):
    self.make_new_lv_stripe_radio_active(self.new_lv_striped_radio.get_active())

  def change_new_lv_size_unit(self, optionmenu, *args):
    #change units label
    unit_index = self.new_lv_size_unit.get_history()
    if unit_index == MEGABYTE_IDX:
      unit_str = "m"
      label_str = REMAINING_SPACE_MEGABYTES
    elif unit_index == KILOBYTE_IDX:
      unit_str = "k"
      label_str = REMAINING_SPACE_KILOBYTES
    elif unit_index == GIGABYTE_IDX:
      unit_str = "g"
      label_str = REMAINING_SPACE_GIGABYTES
    else:
      unit_str = "m"
      label_str = REMAINING_SPACE_EXTENTS
    selection = self.treeview.get_selection()
    model, iter = selection.get_selected()
    if iter != None:
      vgname = model.get_value(iter, PATH_COL).strip()
      free_space,free_extents = self.model_factory.get_free_space_on_VG(vgname,unit_str)
      free_space_bytes,free_ex = self.model_factory.get_free_space_on_VG(vgname,"b")
      if free_extents != None:
        self.free_space_bytes = free_space_bytes
        self.free_space = free_space
        self.free_extents = free_ex
        self.unused_space_label1.set_text(REMAINING_SPACE_VGNAME % vgname)
        if unit_index == EXTENT_IDX:
          self.unused_space_label2.set_text(label_str % free_extents)
        else:
          self.unused_space_label2.set_text(label_str % free_space)

    self.new_lv_size.set_text("")

  def change_new_lv_fs(self, optionmenu, *args):
    fs_idx_val = self.new_lv_fs_menu.get_history()
    self.new_lv_mnt_point.set_sensitive(fs_idx_val)
    self.new_lv_mnt_point_label.set_sensitive(fs_idx_val)
    

  def make_new_lv_stripe_radio_active(self,val):
    #First check if there are more than 1 PVs in volume
    #if not, put up message dialog and reset radiobuttons to linear
    if(val):
      selection = self.treeview.get_selection()
      model, iter = selection.get_selected()
      if iter != None:
        vgname = model.get_value(iter, PATH_COL).strip()
        pv_list = self.model_factory.query_PVs_for_VG(vgname)
        if len(pv_list) < 2:  #striping is not an option
          self.errorMessage(CANT_STRIPE_MESSAGE)
          self.new_lv_linear_radio.set_active(True)
          return

    self.new_lv_stripe_spinner.set_sensitive(val)
    self.new_lv_stripe_size.set_sensitive(val)
    self.new_lv_num_stripes_label.set_sensitive(val)
    self.new_lv_stripe_size_label.set_sensitive(val)
    self.new_lv_kilobytes_label.set_sensitive(val)
      
                                                                                
  def on_init_entity(self, button):
    selection = self.treeview.get_selection()
    model,iter = selection.get_selected()
    name = model.get_value(iter, PATH_COL)
    #message = INIT_ENTITY_1 + name + INIT_ENTITY_2
    message = INIT_ENTITY % name 
    rc = self.warningMessage(message)
    if (rc == gtk.RESPONSE_NO):
      return

    try:
      self.command_handler.initialize_entity(name)
    except CommandError, e:
      self.errorMessage(e.getMessage())
      return

    args = list()
    args.append(name.strip())
    apply(self.reset_tree_model, args)
                                                                                

  def on_add_pv_to_vg(self, button):
    model = self.add_pv_to_vg_treeview.get_model()
    if model != None:
      model.clear()

    vg_list = self.model_factory.query_VGs()
    if len(vg_list) > 0:
      for item in vg_list:
        iter = model.append()
        model.set(iter, NAME_COL, item.get_name(), 
                        SIZE_COL, item.get_volume_size_string())
    
    selection = self.treeview.get_selection()
    main_model, iter_val = selection.get_selected()
    pname = main_model.get_value(iter_val, PATH_COL)
    pathname = pname.strip()
    label_string = ADD_PV_TO_VG_LABEL % pathname
    self.add_pv_to_vg_label.set_text(label_string)
    self.add_pv_to_vg_treeview.set_model(model)
    self.add_pv_to_vg_dlg.show()

  def add_pv_to_vg_delete_event(self, *args):
    self.add_pv_to_vg_dlg.hide()
    return True

  def on_ok_add_pv_to_vg(self, button):
    selection = self.treeview.get_selection()
    main_model, iter_val = selection.get_selected()
    pname = main_model.get_value(iter_val, PATH_COL)
    pathname = pname.strip()

    selection = self.add_pv_to_vg_treeview.get_selection()
    model, iter = selection.get_selected()
    name = model.get_value(iter, NAME_COL)
    vgname = name.strip()

    #Check if this VG allows an Additional PV
    try:
      max_lvs,lvs,max_pvs,pvs = self.model_factory.get_max_LVs_PVs_on_VG(vgname)
    except ValueError, e:
      self.errorMessage(TYPE_CONVERSION_ERROR % e)
      return
    if max_pvs == pvs:
      self.errorMessage(EXCEEDED_MAX_PVS)
      self.add_pv_to_vg_dlg.hide()
      return

    try:
      self.command_handler.add_unalloc_to_vg(pathname, vgname)
    except CommandError, e:
      self.errorMessage(e.getMessage())
      return

    args = list()
    args.append(pathname)
    apply(self.reset_tree_model, args)

    self.add_pv_to_vg_dlg.hide()

  def on_cancel_add_pv_to_vg(self,button):
    self.add_pv_to_vg_dlg.hide()

  def setup_extend_vg_form(self):
    self.on_extend_vg_button = self.glade_xml.get_widget('on_extend_vg_button')
    self.on_extend_vg_button.connect("clicked",self.on_extend_vg)
    self.extend_vg_form = self.glade_xml.get_widget('extend_vg_form')
    self.extend_vg_form.connect("delete_event",self.extend_vg_delete_event)
    self.extend_vg_tree = self.glade_xml.get_widget('extend_vg_tree')
    self.extend_vg_label = self.glade_xml.get_widget('extend_vg_label')
    self.glade_xml.get_widget('on_ok_extend_vg').connect('clicked', self.on_ok_extend_vg)
    self.glade_xml.get_widget('on_cancel_extend_vg').connect('clicked',self.on_cancel_extend_vg)
    #set up columns for tree
    model = gtk.ListStore (gobject.TYPE_STRING,
                           gobject.TYPE_STRING,
                           gobject.TYPE_STRING,
                           gobject.TYPE_INT)

    self.extend_vg_tree.set_model(model)
    renderer1 = gtk.CellRendererText()
    column1 = gtk.TreeViewColumn(ENTITY_NAME,renderer1, text=0)
    self.extend_vg_tree.append_column(column1)
    renderer2 = gtk.CellRendererText()
    column2 = gtk.TreeViewColumn(ENTITY_SIZE,renderer2, text=1)
    self.extend_vg_tree.append_column(column2)
    renderer3 = gtk.CellRendererText()
    column3 = gtk.TreeViewColumn(ENTITY_TYPE,renderer3, markup=2)
    self.extend_vg_tree.append_column(column3)


  def on_extend_vg(self, button):
    main_selection = self.treeview.get_selection()
    main_model,main_iter = main_selection.get_selected()
    main_path = main_model.get_path(main_iter)
    vgname = main_model.get_value(main_iter,PATH_COL).strip()
    try:
      max_lvs,lvs,max_pvs,pvs = self.model_factory.get_max_LVs_PVs_on_VG(vgname)
    except ValueError, e:
      self.errorMessage(TYPE_CONVERSION_ERROR % e)
      return
    if max_pvs == pvs:
      self.errorMessage(EXCEEDED_MAX_PVS)
      return

    self.rebuild_extend_vg_tree()
    self.extend_vg_form.show()

  def on_ok_extend_vg(self, button):
    selection = self.extend_vg_tree.get_selection()
    if selection == None:
      self.extend_vg_form.hide() #cancel opp if OK clicked w/o selection

    model,iter = selection.get_selected()
    entity_name = model.get_value(iter, NAME_COL).strip()
    entity_type = model.get_value(iter, VOL_TYPE_COL)
    
    #Now get name of VG to be extended...
    main_selection = self.treeview.get_selection()
    main_model,main_iter = main_selection.get_selected()
    main_path = main_model.get_path(main_iter)
    vgname = main_model.get_value(main_iter,PATH_COL).strip()

    if entity_type == UNINIT_VOL:  #First, initialize if necessary
      warn_message = INIT_ENTITY % entity_name
      rc = self.warningMessage(warn_message)
      if (rc == gtk.RESPONSE_NO):
        return

      try:
        self.command_handler.initialize_entity(entity_name)
      except CommandError, e:
        self.errorMessage(e.getMessage())
        return

    try:
      self.command_handler.add_unalloc_to_vg(entity_name, vgname)
    except CommandError, e:
      self.errorMessage(e.getMessage())
      return 

    self.extend_vg_form.hide()
    apply(self.reset_tree_model)
    self.treeview.expand_to_path(main_path)

    
  def on_cancel_extend_vg(self, button):
    self.extend_vg_form.hide()

  def extend_vg_delete_event(self, *args):
    self.extend_vg_form.hide()
    return True
    

  def rebuild_extend_vg_tree(self):
    uv_string = "<span foreground=\"#ED1C2A\"><b>" + UNALLOCATED_PV + "</b></span>"
    iv_string = "<span foreground=\"#BBBBBB\"><b>" + UNINIT_DE + "</b></span>"
    model = self.extend_vg_tree.get_model()
    if model != None:
      model.clear()

    unallocated_vols = self.model_factory.query_unallocated()
    if len(unallocated_vols) > 0:
      for vol in unallocated_vols:
        iter = model.append()
        model.set(iter, NAME_COL, vol.get_path(),
                        SIZE_COL, vol.get_volume_size_string(),
                        PATH_COL, uv_string,
                        VOL_TYPE_COL, UNALLOC_VOL)

    uninitialized_list = self.model_factory.query_uninitialized()
    if len(uninitialized_list) > 0:
      for item in uninitialized_list:
        iter = model.append()
        model.set(iter, NAME_COL, item.get_path(),
                        SIZE_COL, item.get_volume_size_string(),
                        PATH_COL, iv_string,
                        VOL_TYPE_COL,UNINIT_VOL)

    selection = self.treeview.get_selection()
    main_model,iter_val = selection.get_selected()
    vgname = main_model.get_value(iter_val, PATH_COL)
    self.extend_vg_label.set_text(ADD_VG_LABEL % vgname)

  def new_vg_delete_event(self, *args):
    self.new_vg_dlg.hide()
    return True

  def setup_misc_widgets(self):
    self.remove_unalloc_pv = self.glade_xml.get_widget('remove_unalloc_pv')
    self.remove_unalloc_pv.connect("clicked",self.on_remove_unalloc_pv)
    self.on_pv_rm_button = self.glade_xml.get_widget('on_pv_rm_button')
    self.on_pv_rm_button.connect("clicked",self.on_pv_rm)
    self.on_lv_rm_button = self.glade_xml.get_widget('on_lv_rm_button')
    self.on_lv_rm_button.connect("clicked",self.on_lv_rm)
    self.on_rm_select_lvs_button = self.glade_xml.get_widget('on_rm_select_lvs')
    self.on_rm_select_lvs_button.connect("clicked",self.on_rm_select_lvs)
    self.on_rm_select_pvs_button = self.glade_xml.get_widget('on_rm_select_pvs')
    self.on_rm_select_pvs_button.connect("clicked",self.on_rm_select_pvs)
    self.migrate_exts_button = self.glade_xml.get_widget('button27')
    self.migrate_exts_button.connect("clicked",self.on_migrate_exts)
    self.extend_lv_button = self.glade_xml.get_widget('button31')
    self.extend_lv_button.connect("clicked",self.on_extend_lv)

  def on_remove_unalloc_pv(self, button):
    selection = self.treeview.get_selection()
    model, iter = selection.get_selected()
    name = model.get_value(iter, PATH_COL)
    pvname = name.strip()
    retval = self.warningMessage(CONFIRM_PVREMOVE % pvname)
    if (retval == gtk.RESPONSE_NO):
      return

    else:
      try:
        self.command_handler.remove_pv(pvname)
      except CommandError, e:
        self.errorMessage(e.getMessage())
        return
      apply(self.reset_tree_model)

  def on_migrate_exts(self, button):
    retval = self.simpleInfoMessage(NOT_IMPLEMENTED)
    return

  def on_extend_lv(self, button):
    retval = self.simpleInfoMessage(NOT_IMPLEMENTED)
    return


  #######################################################
  ###Convenience Dialogs
                                                                                
  def warningMessage(self, message):
    dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
                            message)
    dlg.show_all()
    rc = dlg.run()
    dlg.destroy()
    if (rc == gtk.RESPONSE_NO):
      return gtk.RESPONSE_NO
    if (rc == gtk.RESPONSE_DELETE_EVENT):
      return gtk.RESPONSE_NO
    if (rc == gtk.RESPONSE_CLOSE):
      return gtk.RESPONSE_NO
    if (rc == gtk.RESPONSE_CANCEL):
      return gtk.RESPONSE_NO
 
    return rc
                                                                                
  def errorMessage(self, message):
    dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                            message)
    dlg.show_all()
    rc = dlg.run()
    dlg.destroy()
    return rc
                                                                                
  def infoMessage(self, message):
    dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_YES_NO,
                            message)
    dlg.show_all()
    rc = dlg.run()
    dlg.destroy()
    return rc
                                                                                
  def simpleInfoMessage(self, message):
    dlg = gtk.MessageDialog(None, 0, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                            message)
    dlg.show_all()
    rc = dlg.run()
    dlg.destroy()
    if (rc == gtk.RESPONSE_NO):
      return gtk.RESPONSE_NO
    if (rc == gtk.RESPONSE_DELETE_EVENT):
      return gtk.RESPONSE_NO
    if (rc == gtk.RESPONSE_CLOSE):
      return gtk.RESPONSE_NO
    if (rc == gtk.RESPONSE_CANCEL):
      return gtk.RESPONSE_NO
    return rc
                                                                                
  def register_highlighted_sections(self, section_type, section_list):
    self.section_type = section_type
    self.section_list = section_list

  def clear_highlighted_sections(self):
    self.section_type = UNSELECTABLE_TYPE
    self.section_list = None
                           
