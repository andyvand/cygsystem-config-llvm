#!/usr/bin/python
                                                                                
import sys
import types
import select
import math
import operator
import signal
import gobject
import string
import rhpl.executil
import os
from gtk import TRUE, FALSE
from renderer import volume_renderer
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

    ##Set up list structure
    self.treeview = self.glade_xml.get_widget('treeview1')
    self.treemodel = self.treeview.get_model()
    self.treemodel = gtk.TreeStore (gobject.TYPE_STRING,
                                    gobject.TYPE_INT,
                                    gobject.TYPE_STRING)
    self.treeview.set_model(self.treemodel)
    self.treeview.set_headers_visible(FALSE)

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
    self.pixmap = self.glade_xml.get_widget('drawingarea1')
    self.props_layout_area = self.glade_xml.get_widget('drawingarea3')
    self.scroller = self.glade_xml.get_widget('scrolledwindow4')
    self.scroller.connect('scroll-event', self.on_scroll_event)
    self.layout_pixmap = self.glade_xml.get_widget('drawingarea3')
    color = gtk.gdk.colormap_get_system().alloc_color("white", 1,1)
    self.layout_pixmap.modify_bg(gtk.STATE_NORMAL, color) 
    self.pixmap.modify_bg(gtk.STATE_NORMAL, color) 
    self.vr = volume_renderer(self.pixmap, self.pixmap.window)
    self.lr = Properties_Renderer(self.layout_pixmap, self.layout_pixmap.window)

    self.pixmap.connect('expose-event', self.on_expose_event)
    self.pixmap.connect('scroll-event', self.on_scroll_event)
    self.pixmap.connect('size-allocate', self.on_size_allocate)
    self.pixmap.add_events(gtk.gdk.POINTER_MOTION_MASK)
    self.pixmap.add_events(gtk.gdk.BUTTON_PRESS_MASK)
    self.pixmap.connect("motion_notify_event",self.on_motion_event)
    #self.pixmap.connect("button_press_event",self.vr.highlight_section_persist)
    self.pixmap.connect("button_press_event",self.on_mouse_button_press)
    self.props_layout_area.connect('expose-event', self.on_props_expose_event)

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
    self.phys_panel = self.glade_xml.get_widget('phys_panel')
    self.phys_panel.hide()
    self.log_panel = self.glade_xml.get_widget('log_panel')
    self.log_panel.hide()

    


                                                                                
    self.gc = self.pixmap.window.new_gc()
    self.prepare_tree()
                                                                                
  def reset_tree_model(self, args=None):
    self.prepare_tree()
    if args != None:
      name_to_be_selected = args
      model = self.treeview.get_model()
      model.foreach(self.check_tree_items, name_to_be_selected)
      

  def check_tree_items(self, model, path, iter, name_selection):
    selection = self.treeview.get_selection()
    nv = model.get_value(iter, PATH_COL)
    if nv != None:
      name_val = nv.strip()
    else:
      name_val = nv
    if name_val == name_selection:
      self.treeview.expand_to_path(path)
      selection.select_range(path, path)
      

  def prepare_tree(self):
    treemodel = self.treeview.get_model()
    treemodel.clear()

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
                        PATH_COL, pv.get_path())

        lv_list = self.model_factory.query_LVs_for_VG(vg_name)
        for lv in lv_list:
          if lv.is_vol_utilized():
            iter = treemodel.append(log_iter)
            log_string = "<span foreground=\"#43ACF6\">" + lv.get_name() + "</span>"
            treemodel.set(iter, 
                          NAME_COL, log_string, 
                          TYPE_COL, LOG_TYPE,
                          PATH_COL, lv.get_path())
      #Expand if there are entries 
      self.treeview.expand_row(treemodel.get_path(vg_iter),FALSE)

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
                            PATH_COL, item.get_path())

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
                            PATH_COL, item.get_path())

    #self.treeview.expand_all()
    self.clear_all_buttonpanels()

  def on_expose_event(self,widget,event):
    self.on_tree_selection_changed(None)

  def on_props_expose_event(self, widget, event):
    self.lr.do_render()

  def on_size_allocate(self, widget, allocation):
    #self.width = allocation.width
    #self.height = allocation.height
    pass


  def on_tree_selection_changed(self, *args):
    selection = self.treeview.get_selection()
    model,iter = selection.get_selected()
    if iter == None:
      self.vr.render_noselection()
      return

    treepath = model.get_path(iter)
    
    type = model.get_value(iter, TYPE_COL)
    if type == VG_PHYS_TYPE:
      parent_iter = model.iter_parent(iter)
      nme = model.get_value(parent_iter, NAME_COL)
      vg_name = nme.strip()
      pv_list = self.model_factory.query_PVs_for_VG(vg_name)
      self.vr.render(pv_list, 0)
      vg_data = self.model_factory.get_data_for_VG(vg_name)
      self.lr.render_to_layout_area(vg_data, vg_name, type)
      self.treeview.expand_row(treepath, FALSE)
      self.clear_all_buttonpanels()
      self.phys_vol_view_panel.show()
    elif type == VG_LOG_TYPE:
      parent_iter = model.iter_parent(iter)
      nme = model.get_value(parent_iter, NAME_COL)
      vg_name = nme.strip()
      lv_list = self.model_factory.query_LVs_for_VG(vg_name)
      self.vr.render(lv_list, 2)
      vg_data = self.model_factory.get_data_for_VG(vg_name)
      self.lr.render_to_layout_area(vg_data, vg_name, type)
      self.treeview.expand_row(treepath, FALSE)
      self.clear_all_buttonpanels()
      self.log_vol_view_panel.show()
    elif type == VG_TYPE:
      nme = model.get_value(iter, NAME_COL)
      vg_name = nme.strip()
      lv_list = self.model_factory.query_LVs_for_VG(vg_name)
      pv_list = self.model_factory.query_PVs_for_VG(vg_name)
      vg_data = self.model_factory.get_data_for_VG(vg_name)
      self.lr.render_to_layout_area(vg_data, vg_name, type)
      self.clear_all_buttonpanels()
      self.treeview.expand_row(treepath, FALSE)
      self.vr.render_dual(pv_list, lv_list)
    elif type == PHYS_TYPE:
      pathname = model.get_value(iter, PATH_COL)
      pv_name = pathname.strip()
      pv = self.model_factory.get_PV(pv_name)
      pv_data = self.model_factory.get_data_for_PV(pv_name)
      self.lr.render_to_layout_area(pv_data, pv_name, type)
      self.clear_all_buttonpanels()
      self.phys_panel.show()
      self.vr.render_single_volume(pv, type) 
    elif type == LOG_TYPE:
      pathname = model.get_value(iter, PATH_COL)
      lv_name = pathname.strip()
      lv = self.model_factory.get_LV(lv_name)
      lv_data = self.model_factory.get_data_for_LV(lv_name)
      self.lr.render_to_layout_area(lv_data, lv_name, type)
      self.clear_all_buttonpanels()
      self.log_panel.show()
      self.vr.render_single_volume(lv, type) 
    elif type == UNALLOCATED_TYPE:
      pathname = model.get_value(iter, PATH_COL)
      pv_name = pathname.strip()
      pv = self.model_factory.get_PV(pv_name)
      self.vr.render_single_volume(pv, type) 
      pv_data = self.model_factory.get_data_for_PV(pv_name)
      self.lr.render_to_layout_area(pv_data, pv_name, type)
      self.clear_all_buttonpanels()
      self.unalloc_panel.show()
    elif type == UNINITIALIZED_TYPE:
      pathname = model.get_value(iter, PATH_COL)
      uv_name = pathname.strip()
      uv = self.model_factory.get_UV(uv_name)
      uv_data = self.model_factory.get_data_for_UV(uv_name)
      self.lr.render_to_layout_area(uv_data, uv_name, type)
      self.vr.render_single_volume(uv, type) 
      self.clear_all_buttonpanels()
      self.uninit_panel.show()
    else:
      self.clear_all_buttonpanels()
      self.vr.render_noselection()
      self.lr.clear_layout_area()
      

  def on_scroll_event(self, *args):
    self.on_tree_selection_changed(None)
    return TRUE  

  def on_mouse_button_press(self, widget, event, *args):
    selection = self.treeview.get_selection()
    model,iter = selection.get_selected()
    if iter == None:
      return

    type = model.get_value(iter, TYPE_COL)
    if type == VG_TYPE:
      self.vr.dual_highlight_section_persist(event)
    elif type == VG_PHYS_TYPE:
      self.vr.highlight_section_persist(event)
    elif type == VG_LOG_TYPE:
      self.vr.highlight_section_persist(event)
    elif type == PHYS_TYPE:
      self.vr.single_highlight_extent_persist(event)
      #return
    elif type == LOG_TYPE:
      return
    elif type == UNALLOCATED_TYPE:
      return
    elif type == UNINITIALIZED_TYPE:
      return

  def on_motion_event(self, widget, event, *args):
    return
    layout = self.vr.highlight_section(widget, event, *args)
    self.lr.render_selection(layout)

  def on_row_expand_collapse(self, treeview, logical,expand, openall, *params):
    treeview.get_model()
    selection = treeview.get_selection()
    model, iter = selection.get_selected()
#    if model.iter_parent(iter) == None:  #Top level
    return TRUE
#    else:
#    return FALSE

  def clear_all_buttonpanels(self):
    self.unalloc_panel.hide()
    self.uninit_panel.hide()
    self.log_vol_view_panel.hide()
    self.phys_vol_view_panel.hide()
    self.log_panel.hide()
    self.phys_panel.hide()

