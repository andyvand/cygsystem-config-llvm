#!/usr/bin/python

import sys
import types
import select
import math
import operator
import signal
import gobject
import string
import os
from renderer import volume_renderer

from renderer_new import *

from Properties_Renderer import Properties_Renderer
from lvm_model import lvm_model
from InputController import InputController
from lvmui_constants import *
import stat
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

VOLUME_GROUPS=_("Volume Groups")
UNALLOCATED_VOLUMES=_("Unallocated Volumes")
UNINITIALIZED_ENTITIES=_("Uninitialized Entities")
PHYSICAL_VIEW=_("Physical View")
LOGICAL_VIEW=_("Logical View")

                                                                                
#############################################################
class Volume_Tab_View:
  def __init__(self, glade_xml, model_factory, app):
                                                                                
    self.model_factory = model_factory
                                                                                
    self.main_win = app
    self.width = 0
    self.height = 0
    self.glade_xml = glade_xml
    self.found_selection = False  #sentinel for foreach loop

    ##Set up list structure
    self.treeview = self.glade_xml.get_widget('treeview1')
    self.treemodel = self.treeview.get_model()
    self.treemodel = gtk.TreeStore (gobject.TYPE_STRING,
                                    gobject.TYPE_INT,
                                    gobject.TYPE_STRING,
                                    gobject.TYPE_STRING,
                                    gobject.TYPE_PYOBJECT)
    self.treeview.set_model(self.treemodel)
    self.treeview.set_headers_visible(False)

    self.input_controller = InputController(self.reset_tree_model,
                                            self.treeview, 
                                            self.model_factory, 
                                            self.glade_xml)
    
    #Change Listener
    selection = self.treeview.get_selection()
    selection.connect('changed', self.on_tree_selection_changed)

    #self.treeview.connect('expand-collapse-cursor-row',self.on_row_expand_collapse)
    #self.treeview.connect('row-collapsed',self.on_row_expand_collapse)
    
    self.icon_ellipse_hashtable = {}
    
    renderer1 = gtk.CellRendererText()
    column1 = gtk.TreeViewColumn("Volumes",renderer1,markup=0)
    self.treeview.append_column(column1)
    
    #Time to set up draw area
    window1 = self.glade_xml.get_widget("drawingarea1")
    window1.set_size_request(700, 500)
    window2 = self.glade_xml.get_widget("drawingarea2")
    window2.set_size_request(700, 500)
    window3 = self.glade_xml.get_widget("drawingarea3")
    window3.set_size_request(700, 500)
    window4 = self.glade_xml.get_widget("drawingarea4")
    window4.set_size_request(700, 500)
    
    pr_upper = Properties_Renderer(window3, window3.window)
    #pr_lower = Properties_Renderer(window4, window4.window)
    self.display_view = DisplayView(self.input_controller.register_highlighted_sections, window1, pr_upper, None, None)
    #self.display_view = DisplayView(self.input_controller.register_highlighted_sections, window1, pr_upper, window2, pr_lower)
    
    
    #############################
    ##Highly experimental
    self.box = self.glade_xml.get_widget('vbox12')
    self.uninit_panel = self.glade_xml.get_widget('uninit_panel')
    self.uninit_panel.hide()
    self.unalloc_panel = self.glade_xml.get_widget('unalloc_panel')
    self.unalloc_panel.hide()
    self.phys_vol_view_panel = self.glade_xml.get_widget('phys_vol_view_panel')
    self.phys_vol_view_panel.hide()
    self.log_vol_view_panel = self.glade_xml.get_widget('log_vol_view_panel')
    self.log_vol_view_panel.hide()
    self.on_rm_select_lvs_button = self.glade_xml.get_widget('on_rm_select_lvs')
    self.phys_panel = self.glade_xml.get_widget('phys_panel')
    self.phys_panel.hide()
    self.log_panel = self.glade_xml.get_widget('log_panel')
    self.log_panel.hide()

    
    self.prepare_tree()
                                                                                
  def reset_tree_model(self, *in_args):
    args = list()
    for a in in_args:
      args.append(a)
  
    self.prepare_tree()
    if len(args) != 0:
      model = self.treeview.get_model()
      self.found_selection = False
      model.foreach(self.check_tree_items, args)
      

  def check_tree_items(self, model, path, iter, *args):
    name_selection_argss = list()
    for a in args:
      name_selection_argss.append(a)
    if self.found_selection == True:
      return

    name_selection_args = name_selection_argss[0]
    name_selection = name_selection_args[0]
    vgname = None
    if len(name_selection_args) > 1:
      vgname = name_selection_args[1]

    selection = self.treeview.get_selection()

    #Here we need to check PVs and LVs differently.
    #LVs have a special model column.
    nv = model.get_value(iter, PATH_COL)
    lvn = model.get_value(iter, SIMPLE_LV_NAME_COL)
    
    if nv != None:
      pvname_val = nv.strip()
    else:
      pvname_val = nv
    
    if lvn != None:
      lvname_val = lvn.strip()
    else:
      lvname_val = lvn
    
    if pvname_val == name_selection:
      self.treeview.expand_to_path(path)
      self.found_selection = True #prevents vgname selection in multiple places
      selection.select_path(path)

    if lvname_val == name_selection:
      if vgname == None:
        self.treeview.expand_to_path(path)
        self.found_selection = True #prevents LVs with same name in diff VGs 
        selection.select_path(path)
      else:
        #get parent path in model
        parent_iter = model.iter_parent(iter)
        name_string = model.get_value(parent_iter, NAME_COL)
        result = name_string.find(vgname)
        if result != (-1):
          self.treeview.expand_to_path(path)
          self.found_selection = True  
          selection.select_path(path)
        else:
          return
      

  def prepare_tree(self):
    treemodel = self.treeview.get_model()
    treemodel.clear()

    self.model_factory.reload()
    
    vg_list = self.model_factory.query_VGs()
    if len(vg_list) > 0:
      vg_iter = treemodel.append(None)
      vg_string = "<span size=\"11000\"><b>" + VOLUME_GROUPS + "</b></span>"
      treemodel.set(vg_iter, NAME_COL, vg_string, 
                             TYPE_COL, UNSELECTABLE_TYPE)
      for vg in vg_list:
        vg_child_iter = treemodel.append(vg_iter)
        vg_name = vg.get_name().strip()
        treemodel.set(vg_child_iter, NAME_COL, vg_name, 
                                     TYPE_COL, VG_TYPE,
                                     PATH_COL, vg_name)

        phys_iter = treemodel.append(vg_child_iter)
        log_iter = treemodel.append(vg_child_iter)
        pview_string = vg_name + "<span foreground=\"#ED1C2A\"><i>  " + PHYSICAL_VIEW + "</i></span>"
        treemodel.set(phys_iter, NAME_COL, pview_string,
                                 TYPE_COL, VG_PHYS_TYPE,
                                 PATH_COL, vg_name)
        lview_string = vg_name + "<span foreground=\"#43ACF6\"><i>  " + LOGICAL_VIEW + "</i></span>"
        treemodel.set(log_iter, NAME_COL, lview_string,
                                TYPE_COL, VG_LOG_TYPE,
                                PATH_COL, vg_name)
        pv_list = self.model_factory.query_PVs_for_VG(vg_name)
        for pv in pv_list:
          iter = treemodel.append(phys_iter)
          phys_string = "<span foreground=\"#ED1C2A\">" + pv.get_name() + "</span>"
          treemodel.set(iter, 
                        NAME_COL, phys_string, 
                        TYPE_COL, PHYS_TYPE,
                        PATH_COL, pv.get_path(),
                        OBJ_COL, pv)

        lv_list = self.model_factory.query_LVs_for_VG(vg_name)
        for lv in lv_list:
          if lv.is_vol_utilized():
            iter = treemodel.append(log_iter)
            log_string = "<span foreground=\"#43ACF6\">" + lv.get_name() + "</span>"
            treemodel.set(iter, 
                          NAME_COL, log_string, 
                          TYPE_COL, LOG_TYPE,
                          PATH_COL, lv.get_path(),
                          SIMPLE_LV_NAME_COL, lv.get_name())
      #Expand if there are entries 
      self.treeview.expand_row(treemodel.get_path(vg_iter),False)

    unalloc_list = self.model_factory.query_unallocated()
    if len(unalloc_list) > 0:
      unallocated_iter = treemodel.append(None)
      unalloc_string = "<span size=\"11000\"><b>" + UNALLOCATED_VOLUMES + "</b></span>"
      treemodel.set(unallocated_iter, NAME_COL, unalloc_string, 
                                      TYPE_COL, UNSELECTABLE_TYPE)
      for item in unalloc_list:
        iter = treemodel.append(unallocated_iter)
        p_string = "<span foreground=\"#ED1C2A\">" + item.get_name() + "</span>"
        treemodel.set(iter, NAME_COL, p_string, 
                            TYPE_COL, UNALLOCATED_TYPE,
                            PATH_COL, item.get_path(),
                            OBJ_COL, item)

    uninit_list = self.model_factory.query_uninitialized()
    if len(uninit_list) > 0:
      uninitialized_iter = treemodel.append(None)
      uninit_string = "<span size=\"11000\"><b>" + UNINITIALIZED_ENTITIES + "</b></span>"
      treemodel.set(uninitialized_iter, NAME_COL, uninit_string, 
                                        TYPE_COL, UNSELECTABLE_TYPE)
      for item in uninit_list:
        iter = treemodel.append(uninitialized_iter)
        treemodel.set(iter, NAME_COL, item.get_name(), 
                            TYPE_COL, UNINITIALIZED_TYPE,
                            PATH_COL, item.get_path(),
                            OBJ_COL, item)

    #self.treeview.expand_all()
    self.clear_all_buttonpanels()
  
  def on_tree_selection_changed(self, *args):
    selection = self.treeview.get_selection()
    model,iter = selection.get_selected()
    if iter == None:
      self.display_view.render_no_selection()
      return

    treepath = model.get_path(iter)
    
    type = model.get_value(iter, TYPE_COL)
    if type == VG_PHYS_TYPE:
      parent_iter = model.iter_parent(iter)
      nme = model.get_value(parent_iter, NAME_COL)
      vg_name = nme.strip()
      pv_list = self.model_factory.query_PVs_for_VG(vg_name)
      vg = self.model_factory.get_VG(vg_name)
      self.treeview.expand_row(treepath, False)
      self.input_controller.clear_highlighted_sections()
      self.clear_all_buttonpanels()
      self.phys_vol_view_panel.show()
      self.display_view.render_pvs(vg, pv_list)
    elif type == VG_LOG_TYPE:
      parent_iter = model.iter_parent(iter)
      nme = model.get_value(parent_iter, NAME_COL)
      vg_name = nme.strip()
      lv_list = self.model_factory.query_LVs_for_VG(vg_name)
      vg = self.model_factory.get_VG(vg_name)
      self.treeview.expand_row(treepath, False)
      self.input_controller.clear_highlighted_sections()
      self.clear_all_buttonpanels()
      self.show_log_vol_view_panel(lv_list)
      self.display_view.render_lvs(vg, lv_list)
    elif type == VG_TYPE:
      nme = model.get_value(iter, NAME_COL)
      vg_name = nme.strip()
      lv_list = self.model_factory.query_LVs_for_VG(vg_name)
      pv_list = self.model_factory.query_PVs_for_VG(vg_name)
      vg = self.model_factory.get_VG(vg_name)
      self.clear_all_buttonpanels()
      self.treeview.expand_row(treepath, False)
      self.input_controller.clear_highlighted_sections()
      self.display_view.render_vg(vg, lv_list, pv_list)
    elif type == LOG_TYPE:
      pathname = model.get_value(iter, PATH_COL)
      lv_name = pathname.strip()
      lv = self.model_factory.get_LV(lv_name)
      self.input_controller.clear_highlighted_sections()
      self.clear_all_buttonpanels()
      self.log_panel.show()
      self.display_view.render_lv(lv)
    elif type == PHYS_TYPE:
      pv = model.get_value(iter, OBJ_COL)
      self.input_controller.clear_highlighted_sections()
      self.clear_all_buttonpanels()
      self.phys_panel.show()
      self.display_view.render_pv(pv)
    elif type == UNALLOCATED_TYPE:
      pv = model.get_value(iter, OBJ_COL)
      self.input_controller.clear_highlighted_sections()
      self.clear_all_buttonpanels()
      self.unalloc_panel.show()
      self.display_view.render_unalloc_pv(pv)
    elif type == UNINITIALIZED_TYPE:
      uv = model.get_value(iter, OBJ_COL)
      self.input_controller.clear_highlighted_sections()
      self.clear_all_buttonpanels()
      button = self.input_controller.init_entity_button
      if uv.initializable:
          button.set_sensitive(True)
      else:
          button.set_sensitive(False)
      self.uninit_panel.show()
      self.display_view.render_uninit_pv(uv)
    else:
      self.input_controller.clear_highlighted_sections()
      self.clear_all_buttonpanels()
      self.display_view.render_no_selection()
  
  def on_row_expand_collapse(self, treeview, logical,expand, openall, *params):
    treeview.get_model()
    selection = treeview.get_selection()
    model, iter = selection.get_selected()
#    if model.iter_parent(iter) == None:  #Top level
    return True
#    else:
#    return False

  def show_log_vol_view_panel(self,lv_list):
    #This is a wrapper for self.log_vol_view_panel.show()
    #If the VG has no LVs, then a proxy LV is returned as an 'Unused' LV.
    #We do not want to allow the deletion of this unused LV.
    #So we'll gray out the button.
    self.on_rm_select_lvs_button.set_sensitive(True)
    x = len(lv_list)
    if x == 1:
      if lv_list[0].is_vol_utilized() == False:
        self.on_rm_select_lvs_button.set_sensitive(False)

    self.log_vol_view_panel.show()

  def clear_all_buttonpanels(self):
    self.unalloc_panel.hide()
    self.uninit_panel.hide()
    self.log_vol_view_panel.hide()
    self.phys_vol_view_panel.hide()
    self.log_panel.hide()
    self.phys_panel.hide()

