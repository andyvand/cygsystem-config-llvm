"""This class represents the primary controller interface
   for the LVM UI application.
"""
__author__ = 'Jim Parsons (jparsons@redhat.com)'


from gtk import TRUE, FALSE
import string
import os
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

######################################################
##Note: the enum below and the list that follows MUST#
##remain related. A  chhange in one requires a change# 
##in the other                                       #
NO_FILESYSTEM_FS = 0                                 #
EXT2_FS = 1                                          #
EXT3_FS = 2                                          #
REISER_FS = 3                                        #
XFS_FS = 4                                           #
JFS_FS = 5                                           #
                                                     #
FILE_SYSTEM_TYPE_LIST = [" ","ext2","ext3","reiser","xfs","jfs"]
                                                     #
######################################################

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

CONFIRM_PV_VG_REMOVE=_("Are you quite certain that you wish to remove %s from the %s Volume Group?")
CONFIRM_LV_REMOVE=_("Are you quite certain that you wish to remove the Logical Volume %s?")
NOT_ENOUGH_SPACE_VG=_("Volume Group %s does not have enough space to move the data stored on %s")
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
    self.new_vg_autobak_cbox = self.glade_xml.get_widget('checkbutton8')
    self.new_vg_resize_cbox = self.glade_xml.get_widget('checkbutton7')

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
    phys_extent_units_meg = TRUE
    autobackup = TRUE
    resizable = TRUE

    selection = self.treeview.get_selection()
    model,iter = selection.get_selected()
    pv_name = model.get_value(iter, PATH_COL)

    proposed_name = self.new_vg_name.get_text().strip()
    if proposed_name == "":
      self.errorMessage(MUST_PROVIDE_VG_NAME)

    #Now check for unique name
    vg_list = self.model_factory.query_VGs()
    for vg in vg_list:
      if vg.get_name() == proposed_name:
        self.new_vg_name.select_region(0, (-1))
        self.errorMessage(NON_UNIQUE_NAME % proposed_name)
        return
    Name_request = proposed_name

    max_pvs_field = self.new_vg_max_pvs.get_text()
    if max_pvs_field.isalnum() == FALSE:
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
    if max_lvs_field.isalnum() == FALSE:
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
    autobackup = self.new_vg_resize_cbox.get_active()
    resizable = self.new_vg_resize_cbox.get_active() 

    try:
      self.command_handler.create_new_vg(Name_request,
                                         str(max_physical_volumes),
                                         str(max_logical_volumes),
                                         ACCEPTABLE_EXTENT_SIZES[extent_idx],
                                         phys_extent_units_meg,
                                         resizable,
                                         autobackup,
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
    self.new_vg_radio_meg.set_active(TRUE)
    self.new_vg_extent_size.set_history(DEFAULT_EXTENT_SIZE_MEG_IDX)
    self.new_vg_autobak_cbox.set_active(FALSE)
    self.new_vg_resize_cbox.set_active(FALSE)

  def change_new_vg_radio(self, button):
    menu = self.new_vg_extent_size.get_menu()
    items = menu.get_children()
    #We don't want to offer the 2 and 4 options for kilo's - min size is 8k
    if self.new_vg_radio_meg.get_active() == TRUE:
      items[0].set_sensitive(TRUE)
      items[1].set_sensitive(TRUE)
      self.new_vg_extent_size.set_history(DEFAULT_EXTENT_SIZE_MEG_IDX)
    else:
      items[0].set_sensitive(FALSE)
      items[1].set_sensitive(FALSE)
      self.new_vg_extent_size.set_history(DEFAULT_EXTENT_SIZE_KILO_IDX)

  def on_pv_rm(self, button):
    selection = self.treeview.get_selection()
    model, iter = selection.get_selected()
    name = model.get_value(iter, PATH_COL)
    pvname = name.strip()
    pv = self.model_factory.get_PV(pvname)
    vgname = pv.get_vg_name().strip()
    total,free,alloc = pv.get_extent_values()
    retval = self.warningMessage(CONFIRM_PV_VG_REMOVE % (pvname,vgname))
    if (retval == gtk.RESPONSE_NO):
      return
    else:
      ###FIXME - this just check for 'some' space - it should check for 
      ###enough space by checking free versus needed for pv
      if alloc != 0:
        try:
          self.command_handler.move_pv(pvname)
        except CommandError, e:
          self.errorMessage(e.getMessage())
          return
      #else:
      #  self.errorMessage(NOT_ENOUGH_SPACE_VG % (vgname,pvname))
      #  return

      try:
        self.command_handler.reduce_vg(vgname, pvname)
      except CommandError, e:
        self.errorMessage(e.getMessage())
        return

      args = list()
      args.append(pvname)
      apply(self.reset_tree_model, args)


  def on_lv_rm(self, button):
    selection = self.treeview.get_selection()
    model, iter = selection.get_selected()
    name = model.get_value(iter, PATH_COL)
    lvname = name.strip()
    retval = self.warningMessage(CONFIRM_LV_REMOVE % lvname)
    if (retval == gtk.RESPONSE_NO):
      return
    else:
      #Check if LV is mounted -- if so, unmount
      is_mounted = self.command_handler.is_lv_mounted(lvname)

    if is_mounted == TRUE:
      try:
        self.command_handler.unmount_lv(lvname)
      except CommandError, e:
        errorMessage(e.getMessage())
        return

    try:
      self.command_handler.remove_lv(lvname)
    except CommandError, e:
      errorMessage(e.getMessage())
      return

    #args = list()
    #args.append(lvname)
    #apply(self.reset_tree_model, args)
    apply(self.reset_tree_model)

  def on_rm_select_lvs(self, button):
    if self.section_list == None:
      return
    #check if list > 0
    if len(self.section_list) == 0:
      return 
    #need to check if section is 'unused'
    for item in self.section_list:
      if item.is_vol_utilized == FALSE:
        continue
      lvname = item.get_name().strip()
      retval = self.warningMessage(CONFIRM_LV_REMOVE % lvname)
      if (retval == gtk.RESPONSE_NO):
        continue
      else:
        #Check if LV is mounted -- if so, unmount
        is_mounted = self.command_handler.is_lv_mounted(lvname)

      if is_mounted == TRUE:
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
      if item.is_vol_utilized == FALSE:
        continue
      pvname = item.get_path().strip()
      retval = self.warningMessage(CONFIRM_PV_VG_REMOVE % (pvname,vgname))
      if (retval == gtk.RESPONSE_NO):
        continue
      else:
        #Check if PV has alloc ated extents - if so, move
        total,free,alloc = item.get_extent_values()
        if alloc != 0:
          try:
            self.command_handler.move_pv(pvname)
          except CommandError, e:
            self.errorMessage(e.getMessage())
            continue

          try:
            self.command_handler.reduce_vg(vgname, pvname)
          except CommandError, e:
            self.errorMessage(e.getMessage())
            continue



    self.clear_highlighted_sections()
    #args = list()
    #args.append(vgname)
    #apply(self.reset_tree_model,args)
    apply(self.reset_tree_model)

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
    self.new_lv_fstab_cbox = self.glade_xml.get_widget('fstab_cbox')

    self.prep_new_lv_dlg()

  def on_new_lv(self, button):
    self.prep_new_lv_dlg()
    self.new_lv_dlg.show()

  def prep_new_lv_dlg(self):
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
        self.unused_space_label2.set_text(REMAINING_SPACE_MEGABYTES % free_space)
      else:
        self.free_space_bytes = 0
        self.free_space = 0
        self.unused_space_label1.set_text("")
        self.unused_space_label2.set_text("")
        
    self.new_lv_name.set_text("")
    self.new_lv_size.set_text("")
    self.new_lv_size_unit.set_history(MEGABYTE_IDX)

    #set radiobutton group to linear
    self.new_lv_linear_radio.set_active(TRUE) 
    self.new_lv_stripe_size.set_history(DEFAULT_STRIPE_SIZE_IDX)
    self.new_lv_stripe_spinner.set_value(2.0)

    #set filesystem option menu to 'no filesystem, and deactivate
    #mount point field
    self.new_lv_fs_menu.set_history(NO_FILESYSTEM_FS)
    self.new_lv_mnt_point.set_text("")

    self.change_new_lv_fs(None, None)
    self.change_new_lv_radio(None)

  def on_ok_new_lv_button(self, button):
    Name_request = ""
    VG_Name = ""
    Size_request = 0
    Unit_index = (-1)
    Striped = FALSE
    Stripe_size = 64
    Num_stripes = 2
    Make_filesystem = FALSE
    FS_type = ""
    Mount_filesystem = FALSE
    Mount_point = ""
    FSTAB_entry = FALSE
    
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
    proposed_size = float(prop_size)
    #Normalize size depending on size_unit index
    Unit_index = self.new_lv_size_unit.get_history()
    Size_request = prop_size
    if Unit_index == EXTENT_IDX:
      if int(self.free_extents) < int(prop_size):
        self.errorMessage((EXCEEDS_FREE_SPACE % vgname) + 
                          (REMAINING_SPACE_EXTENTS % self.free_extents)) 
        self.new_lv_size.set_text("")
        return
      normalized_size = int(prop_size)

    else:
      if Unit_index == MEGABYTE_IDX:
        normalized_size = proposed_size * MEGA_MULTIPLIER
        remaining_string = REMAINING_SPACE_MEGABYTES
      elif Unit_index == GIGABYTE_IDX:
        normalized_size = proposed_size * GIGA_MULTIPLIER
        remaining_string = REMAINING_SPACE_GIGABYTES
      elif Unit_index == KILOBYTE_IDX:
        normalized_size = proposed_size * KILO_MULTIPLIER
        remaining_string = REMAINING_SPACE_KILOBYTES

      if float(self.free_space_bytes) < normalized_size:
        self.errorMessage((EXCEEDS_FREE_SPACE % vgname) + 
                          (remaining_string % self.free_space)) 
        self.new_lv_size.set_text("")
        return

    Size_request = proposed_size  #in bytes
   
    #Handle stripe request
    if self.new_lv_striped_radio.get_active() == TRUE:
      Striped = TRUE
      num_stripes_str = str(self.new_lv_stripe_spinner.get_text())
      if num_stripes_str.isalnum():
        Num_stripes = int(num_stripes_str)
      else:
        print "The val from stripe spinner is --->%s<--" % num_stripes_str
        self.errorMessage(NUMBERS_ONLY % NUM_STRIPES_FIELD)
        self.new_lv_stripe_spinner.set_value(2.0)
        return

      stripe_size_index = self.new_lv_stripe_size.get_history()
      Stripe_size = ACCEPTABLE_STRIPE_SIZES[stripe_size_index]


    #Finally, address file system issues
    fs_idx = self.new_lv_fs_menu.get_history()
    if fs_idx > 0:
      Make_filesystem = TRUE
      FS_type = FILE_SYSTEM_TYPE_LIST[fs_idx] 
      if self.new_lv_mnt_point.get_text() != "":
        Mount_filesystem = TRUE
        Mount_point = self.new_lv_mnt_point.get_text()
        if os.path.exists(Mount_point) == FALSE:  ###stat mnt point
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
        if self.new_lv_fstab_cbox.get_active() == TRUE:
          FSTAB_entry = TRUE

    #Build command args
    new_lv_command_set = {}
    new_lv_command_set[NEW_LV_NAME_ARG] = Name_request
    new_lv_command_set[NEW_LV_VGNAME_ARG] = VG_Name
    new_lv_command_set[NEW_LV_UNIT_ARG] = Unit_index
    new_lv_command_set[NEW_LV_SIZE_ARG] = Size_request
    new_lv_command_set[NEW_LV_IS_STRIPED_ARG] = Striped
    if Striped == TRUE:
      new_lv_command_set[NEW_LV_STRIPE_SIZE_ARG] = Stripe_size
      new_lv_command_set[NEW_LV_NUM_STRIPES_ARG] = Num_stripes
    new_lv_command_set[NEW_LV_MAKE_FS_ARG] = Make_filesystem
    if Make_filesystem == TRUE:
      new_lv_command_set[NEW_LV_FS_TYPE_ARG] = FS_type
    new_lv_command_set[NEW_LV_MAKE_MNT_POINT_ARG] = Mount_filesystem
    if Mount_filesystem == TRUE:
      new_lv_command_set[NEW_LV_MNT_POINT_ARG] = Mount_point
      if FSTAB_entry == TRUE:
        new_lv_command_set[NEW_FSTAB_ARG] = FSTAB_entry
    
    try:    
      self.command_handler.new_lv(new_lv_command_set)
    except CommandError, e:
      self.errorMessage(e.getMessage())

    #Add confirmation dialog here... 
    self.new_lv_dlg.hide()
    args = list()
    args.append(Name_request)
    apply(self.reset_tree_model, args)

  def on_cancel_new_lv_button(self, button):
    self.new_lv_dlg.hide()

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
    self.new_lv_fstab_cbox.set_sensitive(fs_idx_val)
    

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
          self.new_lv_linear_radio.set_active(TRUE)
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
      errorMessage(e.getMessage())
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
                        SIZE_COL, item.get_volume_size())
    
    selection = self.treeview.get_selection()
    main_model, iter_val = selection.get_selected()
    pname = main_model.get_value(iter_val, PATH_COL)
    pathname = pname.strip()
    label_string = ADD_PV_TO_VG_LABEL % pathname
    self.add_pv_to_vg_label.set_text(label_string)
    self.add_pv_to_vg_treeview.set_model(model)
    self.add_pv_to_vg_dlg.show()

  def on_ok_add_pv_to_vg(self, button):
    selection = self.treeview.get_selection()
    main_model, iter_val = selection.get_selected()
    pname = main_model.get_value(iter_val, PATH_COL)
    pathname = pname.strip()

    selection = self.add_pv_to_vg_treeview.get_selection()
    model, iter = selection.get_selected()
    name = model.get_value(iter, NAME_COL)
    vgname = name.strip()
    try:
      self.command_handler.add_unalloc_to_vg(pathname, vgname)
    except CommandError, e:
      errorMessage(e.getMessage)
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
      try:
        self.command_handler.initialize_entity(entity_name)
      except CommandError, e:
        errorMessage(e.getMessage())
        return

    try:
      self.command_handler.add_unalloc_to_vg(entity_name, vgname)
    except CommandError, e:
      errorMessage(e.getMessage())
      return 

    self.extend_vg_form.hide()
    apply(self.reset_tree_model)
    self.treeview.expand_to_path(main_path)

    
  def on_cancel_extend_vg(self, button):
    self.extend_vg_form.hide()
    

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
                        SIZE_COL, vol.get_volume_size(),
                        PATH_COL, uv_string,
                        VOL_TYPE_COL, UNALLOC_VOL)

    uninitialized_list = self.model_factory.query_uninitialized()
    if len(uninitialized_list) > 0:
      for item in uninitialized_list:
        iter = model.append()
        model.set(iter, NAME_COL, item.get_path(),
                        SIZE_COL, item.get_volume_size(),
                        PATH_COL, iv_string,
                        VOL_TYPE_COL,UNINIT_VOL)

    selection = self.treeview.get_selection()
    main_model,iter_val = selection.get_selected()
    vgname = main_model.get_value(iter_val, PATH_COL)
    self.extend_vg_label.set_text(ADD_VG_LABEL % vgname)


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
        errorMessage(e.getMessage())
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
    return rc
                                                                                
  def register_highlighted_sections(self, section_type, section_list):
    self.section_type = section_type
    self.section_list = section_list

  def clear_highlighted_sections(self):
    self.section_type = UNSELECTABLE_TYPE
    self.section_list = None
