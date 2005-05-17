"""This class performs the heavy lifting tasks of rendering the volume
   groups.
"""

__author__ = 'Jim Parsons (jparsons@redhat.com)'

 
import sys
import math
import operator
import types
import select
import signal
import gobject
import pango
import string
import os
import gettext 
_ = gettext.gettext

from Volume import Volume
from ViewableVolume import ViewableVolume
from ViewableExtent import ViewableExtent
from ExtentSegment import ExtentSegment
from lvmui_constants import *
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

PIXMAP_DIR = "./pixmaps/"
INSTALLDIR = "/usr/share/system-config-lvm/"
                                                                                
X_BOUND = 30  
X_BOUND_RADIUS = 15
Y_BOUND = 76
Y_BOUND_RADIUS = 38
X_BOUND_DUAL = 20
X_BOUND_DUAL_RADIUS = 10
Y_BOUND_DUAL = 50
Y_BOUND_DUAL_RADIUS = 25
X_BOUND_SINGLE = 40
X_BOUND_SINGLE_RADIUS = 20
Y_BOUND_SINGLE = 100
Y_BOUND_SINGLE_RADIUS = 50
Y_EXTENT_LABEL = 60
EXTENT_LABEL_OFFSET = 33 #Step offset size for lower labels
LEGEND_X = 30
LEGEND_Y = 50
LEGEND_X_OFFSET = 10
LEGEND_Y_OFFSET = 255
GRADIENT_PV = "#ED1C2A"
GRADIENT_VG = "#2D6C23"
GRADIENT_LV = "#43ACE2"
GRADIENT_UV = "#404040"
MAX_X = 300
SINGLE_MAX_X = 200
HORIZONTAL_ORIENTATION = 0
VERTICAL_ORIENTATION = 1
PV_RENDERMETHOD = 0
VG_RENDERMETHOD = 1
LV_RENDERMETHOD = 2
X_PIXMAP_OFFSET = 120
Y_PIXMAP_OFFSET = 160
X_SINGLE_PIXMAP_OFFSET = 120
Y_SINGLE_PIXMAP_OFFSET = 100
X_DUAL_L_PIXMAP_OFFSET = 120
X_DUAL_P_PIXMAP_OFFSET = 120
Y_DUAL_L_PIXMAP_OFFSET = 70
Y_DUAL_P_PIXMAP_OFFSET = 180
DUAL_LABEL_FONT_SIZE = 8
LABEL_NUDGE_FACTOR = 5
LABEL_X = 300
LABEL_Y = 300
LABEL_HEIGHT_NAMES = 150
PHYSICAL_VIEW = 1
LOGICAL_VIEW = 2

                                                                                
UNINITIALIZED_MESSAGE=_("This extent has not yet been \n initialized for use with LVM.")
UNSELECTED_MESSAGE=_("No Volume Selected")
UNALLOCATED_MESSAGE=_("This Volume has not been allocated \n to a Volume Group yet.") 
LOGICAL_VOL_STR=_("Logical Volume")
PHYSICAL_VOL_STR=_("Physical Volume")
VOLUME_GRP_STR=_("Volume Group")
LOGICAL_VIEW_STR=_("Logical View")
PHYSICAL_VIEW_STR=_("Physical View")
UNALLOCATED_STR=_("Unallocated")
UNINITIALIZED_STR=_("Uninitialized")
DISK_ENTITY_STR=_("Disk Entity")
EXTENTS_STR=_("extents")
MEGABYTES_STR=_("Megabytes")
##############################################################

class volume_renderer:
  def __init__(self, area, widget):
    self.main_window = widget
    self.area = area  #actual widget, used for getting style, hence bgcolor

    self.area.set_size_request(700, 500)

    self.gc = self.main_window.new_gc()
    self.pango_context = self.area.get_pango_context()

    if not os.path.exists(PIXMAP_DIR):
      PIXMAPS = INSTALLDIR + PIXMAP_DIR
    else:
      PIXMAPS = PIXMAP_DIR
    self.base_pv_pixbuf = gtk.gdk.pixbuf_new_from_file(PIXMAPS + "PV.xpm")
    self.base_vg_pixbuf = gtk.gdk.pixbuf_new_from_file(PIXMAPS + "VG.xpm")
    self.base_lv_pixbuf = gtk.gdk.pixbuf_new_from_file(PIXMAPS + "grad3.xpm")
    self.base_uv_pixbuf = gtk.gdk.pixbuf_new_from_file(PIXMAPS + "UV.xpm")

    self.base_pixbuf = self.base_lv_pixbuf

    self.gradient_color = GRADIENT_LV
    self.x_length = MAX_X  #length of visual volume
    self.y_length = Y_BOUND
    self.section_count = 0
    self.render_method = LV_RENDERMETHOD

    self.initialize_label_layouts()

    self.generate_hash_tables()    

  def render(self, volume_list, render_method=2):

    self.x_length = MAX_X  #Reset this value here before dividing volume

    self.make_render_choices(render_method)

    self.volume_list = volume_list

    #These calls determine spans for each volume, and init for rendering
    self.viewable_vols = self.prep_volume_list(volume_list)
    self.divide_volume(self.viewable_vols)

    self.do_render()

  def render_with_name(self, volume_list, name, render_method=2):

    self.x_length = MAX_X  #Reset this value here before dividing volume

    self.make_render_choices(render_method)

    self.volume_list = volume_list

    #These calls determine spans for each volume, and init for rendering
    self.viewable_vols = self.prep_volume_list(volume_list)
    self.divide_volume(self.viewable_vols)
    for vv in self.viewable_vols:
      if vv.get_volume().get_name() == name:
        vv.set_is_selected(True)

    self.do_render()

  def do_render(self):
    scaled_pixbuf = self.base_pixbuf.scale_simple(self.x_length + X_BOUND_RADIUS, self.y_length, gtk.gdk.INTERP_BILINEAR)
    pixmap_width = self.x_length + X_BOUND
    pixmap_height = self.y_length
    pixmap = gtk.gdk.Pixmap(self.main_window, pixmap_width, pixmap_height)

    #Pre-fill pixmap with bg color
    self.set_color_to_BG_color()
    pixmap.draw_rectangle(self.gc, 1, 0, 0, pixmap_width, pixmap_height)
   
    #Now load pixmap with pixbuf 
    pixmap.draw_pixbuf(self.gc, scaled_pixbuf, 0, 0, X_BOUND_RADIUS, 0, -1, -1)

    #Now draw filled arc for start
    self.set_color(self.gradient_color)
    pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND, Y_BOUND, 5760, 11520)
    pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND, Y_BOUND, 17280, 11520)

    #Arc for end must match gradient
    self.set_color_to_BG_color()

    #self.generate_ellipse_hashtable()
    
    #The pixmap extends right to end with a square end. Now we need
    #to 'erase' those pixels beyond where the ellipse ends. The 
    #ellipse_hashtable will tell us where to start when added to
    #the x offset
    for y in range(0, Y_BOUND):
      x_small_offset = self.ellipse_hashtable[y]
      x_offset = x_small_offset + self.x_length + X_BOUND_RADIUS - 1
      for x in range(x_offset, pixmap_width):
        pixmap.draw_point(self.gc, x, y)

    self.draw_arcs(pixmap)

    self.main_pixmap = pixmap #Copy used for foundation

    self.draw_highlighted_sections()

    self.draw_labels(pixmap)

    self.main_window.draw_drawable(self.gc, pixmap, 0, 0, X_PIXMAP_OFFSET, Y_PIXMAP_OFFSET, -1, -1)


  def render_dual(self, p_volume_list, l_volume_list, render_method=2):

    self.make_render_choices(render_method)

    self.x_length = MAX_X

    self.p_volume_list = p_volume_list
    self.l_volume_list = l_volume_list

    #These calls determine spans for each volume, and init for rendering
    self.p_viewable_vols = self.prep_volume_list(p_volume_list)
    self.l_viewable_vols = self.prep_volume_list(l_volume_list)
    self.divide_volume(self.p_viewable_vols)
    self.divide_volume(self.l_viewable_vols)

    self.clear_drawing_area()

    self.do_dual_render()

  def do_dual_render(self):

    ################Draw Physical Volume
    p_scaled_pixbuf = self.base_pv_pixbuf.scale_simple(MAX_X + X_BOUND_DUAL_RADIUS, Y_BOUND_DUAL, gtk.gdk.INTERP_BILINEAR)
    p_pixmap_width = MAX_X + X_BOUND_DUAL
    p_pixmap_height = Y_BOUND_DUAL
    p_pixmap = gtk.gdk.Pixmap(self.main_window, p_pixmap_width, p_pixmap_height)

    #Pre-fill pixmap with bg color
    self.set_color_to_BG_color()
    p_pixmap.draw_rectangle(self.gc, 1, 0, 0, p_pixmap_width, p_pixmap_height)
   
    #Now load pixmap with pixbuf 
    p_pixmap.draw_pixbuf(self.gc, p_scaled_pixbuf, 0, 0, X_BOUND_DUAL_RADIUS, 0, -1, -1)

    #Now draw filled arc for start
    self.set_color(GRADIENT_PV)
    p_pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND_DUAL, Y_BOUND_DUAL, 5760, 11520)
    p_pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND_DUAL, Y_BOUND_DUAL, 17280, 11520)

    #Arc for end must match gradient
    self.set_color_to_BG_color()

    #self.generate_ellipse_hashtable()
    
    #The pixmap extends right to end with a square end. Now we need
    #to 'erase' those pixels beyond where the ellipse ends. The 
    #ellipse_hashtable will tell us where to start when added to
    #the x offset
    for y in range(0, Y_BOUND_DUAL):
      x_small_offset = self.dual_ellipse_hashtable[y]
      x_offset = x_small_offset + MAX_X + X_BOUND_DUAL_RADIUS - 1
      for x in range(x_offset, p_pixmap_width):
        p_pixmap.draw_point(self.gc, x, y)

    ################Draw Logical Volume
    l_scaled_pixbuf = self.base_lv_pixbuf.scale_simple(MAX_X + X_BOUND_DUAL_RADIUS, Y_BOUND_DUAL, gtk.gdk.INTERP_BILINEAR)
    l_pixmap_width = MAX_X + X_BOUND_DUAL
    l_pixmap_height = Y_BOUND_DUAL
    l_pixmap = gtk.gdk.Pixmap(self.main_window, l_pixmap_width, l_pixmap_height)

    #Pre-fill pixmap with bg color
    self.set_color_to_BG_color()
    l_pixmap.draw_rectangle(self.gc, 1, 0, 0, l_pixmap_width, l_pixmap_height)
   
    #Now load pixmap with pixbuf 
    l_pixmap.draw_pixbuf(self.gc, l_scaled_pixbuf, 0, 0, X_BOUND_DUAL_RADIUS, 0, -1, -1)

    #Now draw filled arc for start
    self.set_color(GRADIENT_LV)
    l_pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND_DUAL, Y_BOUND_DUAL, 5760, 11520)
    l_pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND_DUAL, Y_BOUND_DUAL, 17280, 11520)

    #Arc for end must match gradient
    self.set_color_to_BG_color()

    #The pixmap extends right to end with a square end. Now we need
    #to 'erase' those pixels beyond where the ellipse ends. The 
    #ellipse_hashtable will tell us where to start when added to
    #the x offset
    for y in range(0, Y_BOUND_DUAL):
      x_small_offset = self.dual_ellipse_hashtable[y]
      x_offset = x_small_offset + MAX_X + X_BOUND_DUAL_RADIUS - 1
      for x in range(x_offset, l_pixmap_width):
        l_pixmap.draw_point(self.gc, x, y)

    self.draw_dual_arcs(p_pixmap,l_pixmap)

    self.p_main_pixmap = p_pixmap #Copy used for foundation

    self.l_main_pixmap = l_pixmap #Copy used for foundation

    self.draw_dual_highlighted_sections()

    self.draw_dual_labels(p_pixmap,l_pixmap)

    self.main_window.draw_drawable(self.gc, self.l_main_pixmap, 0, 0, X_DUAL_L_PIXMAP_OFFSET, Y_DUAL_L_PIXMAP_OFFSET, -1, -1)
    self.main_window.draw_drawable(self.gc, self.p_main_pixmap, 0, 0, X_DUAL_P_PIXMAP_OFFSET, Y_DUAL_P_PIXMAP_OFFSET, -1, -1)


  def rerender(self):
    scaled_pixbuf = self.base_pixbuf.scale_simple(self.x_length + X_BOUND_RADIUS, self.y_length, gtk.gdk.INTERP_BILINEAR)
    pixmap_width = self.x_length + X_BOUND
    pixmap_height = self.y_length
    pixmap = gtk.gdk.Pixmap(self.main_window, pixmap_width, pixmap_height)
                                                                                
    #Pre-fill pixmap with bg color
    self.set_color_to_BG_color()
    pixmap.draw_rectangle(self.gc, 1, 0, 0, pixmap_width, pixmap_height)
    #Now load pixmap with pixbuf
    pixmap.draw_pixbuf(self.gc, scaled_pixbuf, 0, 0, X_BOUND_RADIUS, 0, -1, -1)
                                                                                
    #Now draw filled arc for start
    self.set_color(self.gradient_color)
    pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND, Y_BOUND, 5760, 11520)
    pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND, Y_BOUND, 17280, 11520)
                                                                                
    #Arc for end must match gradient
    self.set_color_to_BG_color()
                                                                                
    #The pixmap extends right to end with a square end. Now we need
    #to 'erase' those pixels beyond where the ellipse ends. The
    #ellipse_hashtable will tell us where to start when added to
    #the x offset
    for y in range(0, Y_BOUND):
      x_small_offset = self.ellipse_hashtable[y]
      x_offset = x_small_offset + self.x_length + X_BOUND_RADIUS - 1
      for x in range(x_offset, pixmap_width):
        pixmap.draw_point(self.gc, x, y)
                                                                                
    self.draw_arcs(pixmap)
                                                                                
    self.main_pixmap = pixmap #Copy used for foundation
                                                                                
    self.draw_highlighted_sections()

    self.draw_labels(pixmap)
                                                                                
    self.main_window.draw_drawable(self.gc, pixmap, 0, 0, X_PIXMAP_OFFSET, Y_PIXMAP_OFFSET, -1, -1)
    
                       
  def render_single_volume(self, pv, render_type):

    self.x_length = SINGLE_MAX_X
    self.clear_drawing_area()

    if(render_type == PHYS_TYPE):
      self.base_pixbuf = self.base_pv_pixbuf
      self.gradient_color = GRADIENT_PV
    elif(render_type == UNALLOCATED_TYPE):  #use LV_RENDERMETHOD
      self.base_pixbuf = self.base_pv_pixbuf
      self.gradient_color = GRADIENT_PV
    elif(render_type == LOG_TYPE):  #use LV_RENDERMETHOD
      self.base_pixbuf = self.base_lv_pixbuf
      self.gradient_color = GRADIENT_LV
    else:  #Uninitialized type
      self.base_pixbuf = self.base_uv_pixbuf
      self.gradient_color = GRADIENT_UV


    #These calls determine spans for each volume, and init for rendering
    self.viewable_volume = self.prep_volume(pv)
    self.divide_single_volume(self.viewable_volume)

    self.do_single_render()


  def do_single_render(self):

    scaled_pixbuf = self.base_pixbuf.scale_simple(SINGLE_MAX_X + X_BOUND_SINGLE_RADIUS, Y_BOUND_SINGLE, gtk.gdk.INTERP_BILINEAR)
    pixmap_width = SINGLE_MAX_X + X_BOUND_SINGLE
    pixmap_height = Y_BOUND_SINGLE
    single_vol_pixmap = gtk.gdk.Pixmap(self.main_window, pixmap_width, pixmap_height)

    #Pre-fill pixmap with bg color
    self.set_color_to_BG_color()
    single_vol_pixmap.draw_rectangle(self.gc, 1, 0, 0, pixmap_width, pixmap_height)
   
    #Now load pixmap with pixbuf 
    single_vol_pixmap.draw_pixbuf(self.gc, scaled_pixbuf, 0, 0, X_BOUND_SINGLE_RADIUS, 0, -1, -1)

    #Now draw filled arc for start
    self.set_color(self.gradient_color)
    single_vol_pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND_SINGLE, Y_BOUND_SINGLE, 5760, 11520)
    single_vol_pixmap.draw_arc(self.gc, 1, 0, 0, X_BOUND_SINGLE, Y_BOUND_SINGLE, 17280, 11520)

    #Arc for end must match gradient
    self.set_color_to_BG_color()

    #The pixmap extends right to end with a square end. Now we need
    #to 'erase' those pixels beyond where the ellipse ends. The 
    #ellipse_hashtable will tell us where to start when added to
    #the x offset
    for y in range(0, Y_BOUND_SINGLE):
      x_small_offset = self.single_vol_ellipse_hashtable[y]
      x_offset = x_small_offset + SINGLE_MAX_X + X_BOUND_SINGLE_RADIUS - 1
      for x in range(x_offset, pixmap_width):
        single_vol_pixmap.draw_point(self.gc, x, y)

    self.draw_single_vol_arcs(single_vol_pixmap)

    self.single_vol_pixmap = single_vol_pixmap #Copy used for foundation

    self.draw_highlighted_extents(single_vol_pixmap)

    self.draw_single_vol_labels(single_vol_pixmap)

    self.main_window.draw_drawable(self.gc, single_vol_pixmap, 0, 0, X_SINGLE_PIXMAP_OFFSET, Y_SINGLE_PIXMAP_OFFSET, -1, -1)


  def render_noselection(self):
    self.clear_drawing_area()
    self.clear_label_layout_pixmap()
    self.set_color("black")
    self.label_layout_pixmap.draw_layout(self.gc, 0, 0, self.unselected_layout)
    self.main_window.draw_drawable(self.gc, self.label_layout_pixmap, 0, 0, X_PIXMAP_OFFSET, Y_PIXMAP_OFFSET, -1, -1)
    pass

  def render_uninitialized(self):
    self.clear_drawing_area()
    self.clear_label_layout_pixmap()
    self.set_color("black")
    self.label_layout_pixmap.draw_layout(self.gc, 0, 0, self.uninitialized_layout)
    self.main_window.draw_drawable(self.gc, self.label_layout_pixmap, 0, 0, X_PIXMAP_OFFSET, Y_PIXMAP_OFFSET, -1, -1)
  
  def render_unallocated(self):
    self.clear_drawing_area()
    self.clear_label_layout_pixmap()
    self.set_color("black")
    self.label_layout_pixmap.draw_layout(self.gc, 0, 0, self.unallocated_layout)
    self.main_window.draw_drawable(self.gc, self.label_layout_pixmap, 0, 0, X_PIXMAP_OFFSET, Y_PIXMAP_OFFSET, -1, -1)
    pass 

  def make_render_choices(self, render_method):
    self.render_method = render_method

    if(render_method == PV_RENDERMETHOD):
      self.base_pixbuf = self.base_pv_pixbuf
      self.gradient_color = GRADIENT_PV
    elif(render_method == VG_RENDERMETHOD ):
      self.base_pixbuf = self.base_vg_pixbuf
      self.gradient_color = GRADIENT_VG
    else:  #use LV_RENDERMETHOD
      self.base_pixbuf = self.base_lv_pixbuf
      self.gradient_color = GRADIENT_LV

  def highlight_section(self, widget, event, *args):
    x,y = event.get_coords()
    outabounds_layout = pango.Layout(self.pango_context)
    outabounds_layout.set_text("HEY! The mouse is not over anything!")
    if x < X_PIXMAP_OFFSET:
      return None
    if x > MAX_X + X_PIXMAP_OFFSET + X_BOUND_RADIUS:
      return None
    if y < Y_PIXMAP_OFFSET:
      return outabounds_layout
    if y > Y_BOUND + Y_PIXMAP_OFFSET:
      return outabounds_layout

    section = self.retrieve_section(x, y)
    outabounds_layout.set_text("X is " + str(x) + "Y is " + str(y) + "\nSection is " + str(section))
   
    return outabounds_layout 

    

    #Now figure out which section needs highlighting 
  def highlight_section_persist(self, event):
    x,y = event.get_coords()
    if x < X_PIXMAP_OFFSET:
      return None
    if x > MAX_X + X_PIXMAP_OFFSET + X_BOUND:
      return None
    if y < Y_PIXMAP_OFFSET:
      return None
    if y > Y_BOUND + Y_PIXMAP_OFFSET:
      return None

    if event.button == 1:
      section = self.retrieve_section(x, y)
      if self.viewable_vols[section].get_volume().is_vol_utilized() == False:
        return None
      if self.viewable_vols[section].get_is_selected() == True:
        self.viewable_vols[section].set_is_selected(False)
      else:
        self.viewable_vols[section].set_is_selected(True)
      #self.highlight_this_section(section)

      self.rerender() 
      #return updated list of selected sections
      return_list = list()
      for vvol in self.viewable_vols:
        if vvol.get_is_selected() == True:  
          return_list.append(vvol.get_volume())
      if len(return_list) > 0:
        return return_list
      else:
        return None

    return None

  def dual_highlight_section_persist(self, event):
    x,y = event.get_coords()
    if x < X_DUAL_P_PIXMAP_OFFSET:
      return
    if x > MAX_X + X_DUAL_P_PIXMAP_OFFSET + X_BOUND_DUAL:
      return
    if y < Y_DUAL_L_PIXMAP_OFFSET:
      return
    if y > Y_BOUND_DUAL + Y_DUAL_P_PIXMAP_OFFSET:
      return
    if (y > Y_DUAL_L_PIXMAP_OFFSET + Y_BOUND_DUAL) and (y < Y_DUAL_P_PIXMAP_OFFSET): #Between volume views
      return

    if event.button == 1:
      vol,section = self.dual_retrieve_section(x, y)
      if vol == PHYSICAL_VIEW:
        #if self.p_viewable_vols[section].get_is_selected() == TRUE:
        #  self.p_viewable_vols[section].set_is_selected(False)
        #else:
        #  self.p_viewable_vols[section].set_is_selected(TRUE)
        return    ##PV View is not currently selectable
      elif vol == LOGICAL_VIEW:
        #If selected, de-select and clear extent pixmap
        if self.l_viewable_vols[section].get_is_selected() == True:
          self.l_viewable_vols[section].set_is_selected(False)
        else:
          #clear all selections, and make selected one true, and 
          #write out fresh extent pixmap 
          for vol in self.l_viewable_vols:
            vol.set_is_selected(False)
          self.l_viewable_vols[section].set_is_selected(True)
      else:
        return  #section not found

      self.do_dual_render() 

  def single_highlight_extent_persist(self, event):
    x,y = event.get_coords()
    if x < X_SINGLE_PIXMAP_OFFSET:
      return
    if x > SINGLE_MAX_X + X_SINGLE_PIXMAP_OFFSET + X_BOUND_SINGLE:
      return
    if y < Y_SINGLE_PIXMAP_OFFSET:
      return
    if y > Y_BOUND_SINGLE + Y_SINGLE_PIXMAP_OFFSET:
      return

    if event.button == 1:
      extent = self.retrieve_extent(x, y)
      #vol = self.viewable_vols[section]
      viewable_extents = self.viewable_volume.get_viewable_extents()
      if viewable_extents[extent].get_is_selected() == True:
        viewable_extents[extent].set_is_selected(False)
      else:
        viewable_extents[extent].set_is_selected(True)
      #self.highlight_this_section(section)
      self.do_single_render() 

  def retrieve_section(self, xval, yval):
    #x = xval - X_PIXMAP_OFFSET + X_BOUND_RADIUS
    x = xval - X_PIXMAP_OFFSET
    y = yval - Y_PIXMAP_OFFSET
    x_small_offset = self.ellipse_hashtable[y]
    i = (-1)
    for item in self.viewable_vols:
      i = i + 1
      start = item.get_start() + x_small_offset + X_BOUND_RADIUS
      span = item.get_span() 
      if (x >= start) and (x < (start + span)):
        return i

    return (-1)

  def dual_retrieve_section(self, xval, yval):
    view = 0
    if (yval >= Y_DUAL_L_PIXMAP_OFFSET) and (yval <= Y_DUAL_L_PIXMAP_OFFSET + Y_BOUND_DUAL):
      view = LOGICAL_VIEW
      y = yval - Y_DUAL_L_PIXMAP_OFFSET
    else:
      view = PHYSICAL_VIEW
      y = yval - Y_DUAL_P_PIXMAP_OFFSET
    x = xval - X_DUAL_P_PIXMAP_OFFSET
    x_small_offset = self.dual_ellipse_hashtable[y]
    i = (-1)
    if view == LOGICAL_VIEW:
      viewables = self.l_viewable_vols
    else:
      viewables = self.p_viewable_vols

    for item in viewables:
      i = i + 1
      start = item.get_start() + x_small_offset + X_BOUND_DUAL_RADIUS
      span = item.get_span() 
      if (x >= start) and (x < (start + span)):
        return view,i

    return (0,-1)

  def retrieve_extent(self, xval, yval):
    viewable_extents = self.viewable_volume.get_viewable_extents()
    #x = xval - X_PIXMAP_OFFSET + X_BOUND_RADIUS
    x = xval - X_SINGLE_PIXMAP_OFFSET
    y = yval - Y_SINGLE_PIXMAP_OFFSET
    x_small_offset = self.single_vol_ellipse_hashtable[y]
    i = (-1)
    for item in viewable_extents:
      i = i + 1
      start = item.get_start_pixel() + x_small_offset + X_BOUND_SINGLE_RADIUS
      span = item.get_span() 
      if (x >= start) and (x < (start + span)):
        return i

    return (-1)

  def highlight_this_section(self, section):
    if section < 0:
      return
    if section > (len(self.viewable_vols) - 1):
      return
    self.set_color("white")
    vvol = self.viewable_vols[section]
    start = vvol.get_start()
    vvol.set_selected = True
    span = vvol.get_span() - 1
    pixmap = self.main_pixmap
    for i in range(0, Y_BOUND, 2):
      x_small_offset = self.ellipse_hashtable[i]
      x = start + x_small_offset + X_BOUND_RADIUS
      x_end = x + span 
      pixmap.draw_line(self.gc,int(x), i, int(x_end), i)  
    self.main_window.draw_drawable(self.gc, pixmap, 0, 0, X_PIXMAP_OFFSET, Y_PIXMAP_OFFSET, -1, -1)
      
  def highlight_this_dual_p_section(self, section):
    if section < 0:
      return
    if section > (len(self.p_viewable_vols) - 1):
      return
    self.set_color("white")
    vvol = self.p_viewable_vols[section]
    start = vvol.get_start()
    vvol.set_selected = True
    span = vvol.get_span() - 1
    pixmap = self.p_main_pixmap
    for i in range(0, Y_BOUND_DUAL, 2):
      x_small_offset = self.dual_ellipse_hashtable[i]
      x = start + x_small_offset + X_BOUND_DUAL_RADIUS
      x_end = x + span 
      pixmap.draw_line(self.gc,x, i, x_end, i)  
    self.main_window.draw_drawable(self.gc, pixmap, 0, 0, X_DUAL_P_PIXMAP_OFFSET, Y_DUAL_P_PIXMAP_OFFSET, -1, -1)

  def highlight_this_dual_l_section(self, section):
    if section < 0:
      return
    if section > (len(self.l_viewable_vols) - 1):
      return
    self.set_color("white")
    vvol = self.l_viewable_vols[section]
    start = vvol.get_start()
    vvol.set_selected = True
    span = vvol.get_span() - 1
    pixmap = self.l_main_pixmap
    for i in range(0, Y_BOUND_DUAL, 2):
      x_small_offset = self.dual_ellipse_hashtable[i]
      x = start + x_small_offset + X_BOUND_DUAL_RADIUS
      x_end = x + span 
      pixmap.draw_line(self.gc,int(x), i, int(x_end), i)  
    self.main_window.draw_drawable(self.gc, pixmap, 0, 0, X_DUAL_L_PIXMAP_OFFSET, Y_DUAL_L_PIXMAP_OFFSET, -1, -1)

    #Now highlight the appropriate extents on the PV view
    #selection vals must be cleared fresh before resetting below
    for vvolume in self.p_viewable_vols:
      vvolume.clear_extent_selections()

    self.set_color("gray")
    lv_name = vvol.get_volume().get_name()
    p_pixmap = self.p_main_pixmap
    for pvvol in self.p_viewable_vols:
      vexlist = pvvol.get_viewable_extents()
      for vex in vexlist:
        if vex.check_name(lv_name):
          vex.set_is_selected(True)
          for j in range(0, Y_BOUND_DUAL, 2):
            vexstart,vexspan = vex.get_start_span()
            x_small_offset = self.dual_ellipse_hashtable[j] 
            vx = vexstart + x_small_offset + X_BOUND_DUAL_RADIUS
            vx_end = vx + vexspan
            p_pixmap.draw_line(self.gc, int(vx), j, int(vx_end), j)


    self.main_window.draw_drawable(self.gc, p_pixmap, 0, 0, X_DUAL_P_PIXMAP_OFFSET, Y_DUAL_P_PIXMAP_OFFSET, -1, -1)
    

  def highlight_this_extent(self, extent,pixmap):
    viewable_extents = self.viewable_volume.get_viewable_extents()
    if extent < 0:
      return
    if extent > (len(viewable_extents) - 1):
      return
    self.set_color("white")
    vext = viewable_extents[extent]
    start = vext.get_start_pixel()
    vext.set_selected = True
    span = vext.get_span() - 1
    for i in range(0, Y_BOUND_SINGLE, 2):
      x_small_offset = self.single_vol_ellipse_hashtable[i]
      x = start + x_small_offset + X_BOUND_SINGLE_RADIUS
      x_end = x + span 
      pixmap.draw_line(self.gc,int(x), i, int(x_end), i)  
    self.main_window.draw_drawable(self.gc, pixmap, 0, 0, X_SINGLE_PIXMAP_OFFSET, Y_SINGLE_PIXMAP_OFFSET, -1, -1)
      
  def draw_highlighted_sections(self):
    i = (-1)
    for vols in self.viewable_vols:
      i = i + 1
      if vols.get_is_selected() == True:
        self.highlight_this_section(i)

  def draw_dual_highlighted_sections(self):
    ###FIXME This loop over PVs below is dead now that
    ###nothing on the PV can be selected in the dual view
    ###Leaving this code in case selection is added for
    ###the PV view
    i = (-1)
    for vols in self.p_viewable_vols:
      i = i + 1
      if vols.get_is_selected() == True:
        self.highlight_this_dual_p_section(i)

    i = (-1)
    for vols in self.l_viewable_vols:
      i = i + 1
      if vols.get_is_selected() == True:
        self.highlight_this_dual_l_section(i)

  def draw_highlighted_extents(self, single_vol_pixmap):
    viewable_extents = self.viewable_volume.get_viewable_extents()
    i = (-1)
    for extent in viewable_extents:
      i = i + 1
      if extent.get_is_selected() == True:
        self.highlight_this_extent(i,single_vol_pixmap)

  def draw_arcs(self, pixmap):
    for item in self.viewable_vols:
      x_val = item.get_start()
      if x_val == 0:
        continue
      pixmap.draw_arc(self.gc, 0, int(x_val), 0, X_BOUND, Y_BOUND, 17280, 11520)

  def draw_dual_arcs(self, p_pixmap, l_pixmap):
    for item in self.p_viewable_vols:
      x_val = item.get_start()
      if x_val == 0:
        continue
      p_pixmap.draw_arc(self.gc, 0, int(x_val), 0, X_BOUND_DUAL, Y_BOUND_DUAL, 17280, 11520)

    for item in self.l_viewable_vols:
      x_val = item.get_start()
      if x_val == 0:
        continue
      l_pixmap.draw_arc(self.gc, 0, int(x_val), 0, X_BOUND_DUAL, Y_BOUND_DUAL, 17280, 11520)

  def draw_single_vol_arcs(self, pixmap):
    elist = self.viewable_volume.get_viewable_extents()
    for item in elist:
      x_val = item.get_start_pixel()
      if x_val == 0:
        continue
      pixmap.draw_arc(self.gc, 0, int(x_val), 0, X_BOUND_SINGLE, Y_BOUND_SINGLE, 17280, 11520)

  def draw_labels(self, pixmap):
    self.clear_drawing_area()
 
    px, py = pixmap.get_size()

    self.draw_end_label(px, py)

    #I hate iterating through this list twice, but a better way
    #does not come to mind, as label pixmap must be constructed
    #with proper size before labels can be drawn to it.
    max_y = 0
    for vol in self.viewable_vols:
      l = vol.get_vertical_layout(9)
      xval, yval = l.get_pixel_size()
      if yval > max_y:
        max_y = yval
    label_pixmap = gtk.gdk.Pixmap(self.main_window, px, max_y + 2)
    self.set_color_to_BG_color()
    label_pixmap.draw_rectangle(self.gc, True, 0, 0, px, max_y + 2)

    self.set_color("black")

    for item in self.viewable_vols:
      layout = item.get_vertical_layout(9)
      span = item.get_span()
      span2 = operator.div(span, 2)
      start = item.get_start()
      label_x = int(X_BOUND_RADIUS + start + span2 - LABEL_NUDGE_FACTOR )
      x,y = layout.get_pixel_size()
      label_y = max_y - y - LABEL_NUDGE_FACTOR
      label_pixmap.draw_layout(self.gc, label_x, label_y, layout)
      #label_pixmap.draw_layout(self.gc, 10, 10, layout)
      self.main_window.draw_drawable(self.gc, label_pixmap, 0, 0, X_PIXMAP_OFFSET, Y_PIXMAP_OFFSET - max_y - LABEL_NUDGE_FACTOR, -1, -1)

  def draw_end_label(self, px, py):
    vol = self.viewable_vols[0].get_volume()
    type = vol.get_type()
    line0 = "<span size=\"7000\"><b>" + VOLUME_GRP_STR + "</b></span>\n"
    line1 = "<span size=\"7000\"><b>" + vol.get_vg_name() + "</b></span>\n"
    if type == PHYS_TYPE:
      line2 = "<span foreground=\"#ED1C2A\" size=\"8000\"><i>" + PHYSICAL_VIEW_STR + "</i></span>" 
    else:
      line2 = "<span foreground=\"#43ACE2\" size=\"8000\"><i>" + LOGICAL_VIEW_STR + "</i></span>" 
    
    textstr = line0 + line1 + line2
    layout = pango.Layout(self.pango_context)
    attr,text,a = pango.parse_markup(textstr, u'_')
    layout.set_attributes(attr)
    layout.set_text(text)

    xval,yval = layout.get_pixel_size()

    side_label_pixmap = gtk.gdk.Pixmap(self.main_window, xval, py)
    self.set_color_to_BG_color()
    side_label_pixmap.draw_rectangle(self.gc, True, 0, 0, xval, py)
    self.set_color("black")
    side_label_pixmap.draw_layout(self.gc, 0,0, layout)
    little_y_offset = operator.div((py - yval),2)
    self.main_window.draw_drawable(self.gc,
                                   side_label_pixmap,
                                   0,
                                   0,
                                   X_PIXMAP_OFFSET - (xval + 5),
                                   Y_PIXMAP_OFFSET + little_y_offset,
                                   -1,
                                   -1)
 

  def draw_single_vol_labels(self, pixmap):
    #self.clear_drawing_area()
    px, py = pixmap.get_size()

    self.draw_single_end_label(px, py)

    #self.draw_single_vol_top_label(px, py)

    self.draw_single_vol_bottom_label(px, py)

    #self.draw_single_vol_legend()

  def draw_single_end_label(self,px,py):
    #4 cases here. 
    vol = self.viewable_volume.get_volume()
    type = vol.get_type()
    if type == PHYS_TYPE:
      line0 = "<span foreground=\"#ED1C2A\" size=\"8000\"><b>" + PHYSICAL_VOL_STR + "</b></span>"
      line1 = "<span size=\"8000\"><b>" + vol.get_path() + "</b></span>"
      textstr = line0 + "\n" + line1
    elif type == UNALLOCATED_TYPE:
      line0 = "<span foreground=\"#ED1C2A\" size=\"8000\"><b>" + UNALLOCATED_STR + "</b></span>"
      line1 = "<span foreground=\"#ED1C2A\" size=\"8000\"><b>" + PHYSICAL_VOL_STR + "</b></span>"
      line2 = "<span size=\"8000\"><b>" + vol.get_path() + "</b></span>"
      textstr = line0 + "\n" + line1 + "\n" + line2
    elif type == UNINITIALIZED_TYPE:
      line0 = "<span size=\"8000\"><b>" + UNINITIALIZED_STR + "</b></span>"
      line1 = "<span size=\"8000\"><b>" + DISK_ENTITY_STR + "</b></span>"
      line2 = "<span size=\"8000\"><b>" + vol.get_path() + "</b></span>"
      textstr = line0 + "\n" + line1 + "\n" + line2
    else:  #Logical Vol
      line0 =  "<span foreground=\"#43ACE2\" size=\"8000\"><b>" + LOGICAL_VOL_STR + "</b></span>"
      line1 = "<span size=\"8000\"><b>" + vol.get_path() + "</b></span>"
      textstr = line0 + "\n" + line1

    layout = pango.Layout(self.pango_context)
    attr,text,a = pango.parse_markup(textstr, u'_')
    layout.set_attributes(attr)
    layout.set_text(text)

    xval,yval = layout.get_pixel_size()
      
    side_label_pixmap = gtk.gdk.Pixmap(self.main_window, xval, py)
    self.set_color_to_BG_color()
    side_label_pixmap.draw_rectangle(self.gc, True, 0, 0, xval, py)
    self.set_color("black")
    side_label_pixmap.draw_layout(self.gc, 0,0, layout)
    little_y_offset = operator.div((py - yval),2)
    self.main_window.draw_drawable(self.gc, 
                                   side_label_pixmap, 
                                   0, 
                                   0, 
                                   X_SINGLE_PIXMAP_OFFSET - (xval + 5), 
                                   Y_SINGLE_PIXMAP_OFFSET + little_y_offset, 
                                   -1, 
                                   -1) 

  def draw_single_vol_top_label(self, px, py): 
    #I hate iterating through this list twice, but a better way
    #does not come to mind, as label pixmap must be constructed
    #with proper size before labels can be drawn to it.
    max_y = 0
    vol = self.viewable_volume
    l = vol.get_vertical_layout(9)
    xval, yval = l.get_pixel_size()
    if yval > max_y:
      max_y = yval
    label_pixmap = gtk.gdk.Pixmap(self.main_window, px, max_y + 2)
    self.set_color_to_BG_color()
    label_pixmap.draw_rectangle(self.gc, True, 0, 0, px, max_y + 2)

    self.set_color("black")

    layout = vol.get_vertical_layout(9)
    span = vol.get_span()
    span2 = operator.div(span, 2)
    start = vol.get_start()
    label_x = X_BOUND_RADIUS + start + span2 - LABEL_NUDGE_FACTOR 
    x,y = layout.get_pixel_size()
    label_y = max_y - y - LABEL_NUDGE_FACTOR
    label_pixmap.draw_layout(self.gc, label_x, label_y, layout)
    self.main_window.draw_drawable(self.gc, label_pixmap, 0, 0, X_SINGLE_PIXMAP_OFFSET, Y_SINGLE_PIXMAP_OFFSET - max_y - LABEL_NUDGE_FACTOR, -1, -1)

  def draw_single_vol_bottom_label(self, px, py): 
    vol = self.viewable_volume
    vexlist = vol.get_viewable_extents()
    num_extents = len(vexlist)
    label_height = (num_extents + 1) * EXTENT_LABEL_OFFSET
    x_padded = px + 30
    bottom_label_pixmap = gtk.gdk.Pixmap(self.main_window, x_padded, label_height)
    self.set_color_to_BG_color()
    bottom_label_pixmap.draw_rectangle(self.gc, True, 0, 0, x_padded, label_height)
    self.set_color("black")

    offset_counter = 1
    for vex in vexlist:
      layout = vex.get_horizontal_layout(7)
      start,span = vex.get_start_span()
      span_div_2 = int(operator.div(span,2))
      centerpix = start + span_div_2 + X_BOUND_DUAL_RADIUS + 4
      y_layout = (offset_counter - 1) * EXTENT_LABEL_OFFSET
      bottom_label_pixmap.draw_line(self.gc,int(centerpix), 0, int(centerpix),offset_counter * EXTENT_LABEL_OFFSET) 
      bottom_label_pixmap.draw_layout(self.gc, int(centerpix) + 2, y_layout, layout)
      if offset_counter == 4:
        offset_counter = 2
      else:
        offset_counter = offset_counter + 1

    self.main_window.draw_drawable(self.gc, bottom_label_pixmap, 0, 0, X_SINGLE_PIXMAP_OFFSET, Y_SINGLE_PIXMAP_OFFSET + py + 1, -1, -1)


  def draw_single_vol_legend(self):
    vol = self.viewable_volume.get_volume()
    type = vol.get_type()
    if type == PHYS_TYPE:
      total,free,alloc = vol.get_extent_values()
      size = float(vol.get_volume_size()) * 1000.0  #in megabytes
      pixs = operator.div(float(self.x_length * 20), float(total))
      pixsize = operator.div(float(self.x_length * 20), float(size))
      twenty_pixel = int(math.ceil(pixs))
      color = GRADIENT_PV
    else:
      return

    line1 = str(twenty_pixel) + " " + EXTENTS_STR
    f_val = "%.3f" % pixsize
    line2 = "(" + f_val  + " " + MEGABYTES_STR + ")"
    textstr = line1 + "\n" + line2
    layout = pango.Layout(self.pango_context)
    layout.set_text(textstr)
    lx,ly = layout.get_pixel_size()
    legend_pixmap = gtk.gdk.Pixmap(self.main_window, lx, ly + 25)
    self.set_color_to_BG_color()
    legend_pixmap.draw_rectangle(self.gc, True, 0, 0, lx, ly + 25)
    self.set_color(color)
    legend_pixmap.draw_line(self.gc, LABEL_NUDGE_FACTOR,
                                     0,
                                     LABEL_NUDGE_FACTOR,
                                     10)
    legend_pixmap.draw_line(self.gc, LABEL_NUDGE_FACTOR + 20,
                                     0,
                                     LABEL_NUDGE_FACTOR + 20,
                                     10)
    legend_pixmap.draw_line(self.gc, LABEL_NUDGE_FACTOR,
                                     10,
                                     LABEL_NUDGE_FACTOR + 20,
                                     10)
    self.set_color("black")
    legend_pixmap.draw_layout(self.gc, 0,14,layout)
    self.main_window.draw_drawable(self.gc, 
                                   legend_pixmap, 
                                   0, 
                                   0, 
                                   LEGEND_X_OFFSET, 
                                   LEGEND_Y_OFFSET, 
                                   -1, 
                                   -1)

      
     

  def draw_dual_labels(self, p_pixmap, l_pixmap):
    px, py = p_pixmap.get_size()

    self.draw_dual_end_labels(px, py)

    #get size of tallest label...base pixmap size on it
    max_y = 0
    for vol in self.p_viewable_vols:
      l = vol.get_layout()
      xval, yval = l.get_pixel_size()
      if yval > max_y:
        max_y = yval
    p_label_pixmap = gtk.gdk.Pixmap(self.main_window, px, max_y + 2)
    self.set_color_to_BG_color()
    p_label_pixmap.draw_rectangle(self.gc, True, 0, 0, px, max_y + 2)

    self.set_color("black")

    for item in self.p_viewable_vols:
      layout = item.get_vertical_layout(6)
      span = item.get_span()
      span2 = operator.div(span, 2)
      start = item.get_start()
      label_x = X_BOUND_DUAL_RADIUS + start + span2 - LABEL_NUDGE_FACTOR 
      x,y = layout.get_pixel_size()
      label_y = max_y - y - LABEL_NUDGE_FACTOR
      p_label_pixmap.draw_layout(self.gc, int(label_x), int(label_y), layout)
      self.main_window.draw_drawable(self.gc, p_label_pixmap, 0, 0, X_DUAL_P_PIXMAP_OFFSET, Y_DUAL_P_PIXMAP_OFFSET - max_y - LABEL_NUDGE_FACTOR, -1, -1)

    self.draw_extent_labels_for_dualview_PV(p_pixmap)

    lx, ly = l_pixmap.get_size()
    max_y = 0
    for vol in self.l_viewable_vols:
      l = vol.get_layout()
      xval, yval = l.get_pixel_size()
      if yval > max_y:
        max_y = yval
    l_label_pixmap = gtk.gdk.Pixmap(self.main_window, lx, max_y + 2)
    self.set_color_to_BG_color()
    l_label_pixmap.draw_rectangle(self.gc, True, 0, 0, lx, max_y + 2)

    self.set_color("black")

    for item in self.l_viewable_vols:
      layout = item.get_vertical_layout(6)
      span = item.get_span()
      span2 = operator.div(span, 2)
      start = item.get_start()
      label_x = X_BOUND_DUAL_RADIUS + start + span2 - LABEL_NUDGE_FACTOR 
      x,y = layout.get_pixel_size()
      label_y = max_y - y - LABEL_NUDGE_FACTOR
      l_label_pixmap.draw_layout(self.gc, int(label_x), int(label_y), layout)
      self.main_window.draw_drawable(self.gc, l_label_pixmap, 0, 0, X_DUAL_L_PIXMAP_OFFSET, Y_DUAL_L_PIXMAP_OFFSET - max_y - LABEL_NUDGE_FACTOR, -1, -1)

  def draw_dual_end_labels(self, px, py):
    vol = self.l_viewable_vols[0].get_volume()
    line0 = "<span size=\"7000\"><b>" + VOLUME_GRP_STR + "</b></span>\n"
    line1 = "<span size=\"7000\"><b>" + vol.get_vg_name() + "</b></span>\n"
    line2A = "<span foreground=\"#43ACE2\" size=\"8000\"><i>" + LOGICAL_VIEW_STR + "</i></span>"
    line2B = "<span foreground=\"#ED1C2A\" size=\"8000\"><i>" + PHYSICAL_VIEW_STR + "</i></span>"
                                                                                
    textstr_log = line0 + line1 + line2A
    textstr_phys = line0 + line1 + line2B
    layout_l = pango.Layout(self.pango_context)
    layout_p = pango.Layout(self.pango_context)

    attr,text,a = pango.parse_markup(textstr_log, u'_')
    layout_l.set_attributes(attr)
    layout_l.set_text(text)
                                                                                
    attr,text,a = pango.parse_markup(textstr_phys, u'_')
    layout_p.set_attributes(attr)
    layout_p.set_text(text)

    #layouts should be the same size, so we need to do this just once 
    xval,yval = layout_l.get_pixel_size()
                                                                                
    side_label_pixmap_l = gtk.gdk.Pixmap(self.main_window, xval, py)
    side_label_pixmap_p = gtk.gdk.Pixmap(self.main_window, xval, py)
    self.set_color_to_BG_color()
    side_label_pixmap_l.draw_rectangle(self.gc, True, 0, 0, xval, py)
    side_label_pixmap_p.draw_rectangle(self.gc, True, 0, 0, xval, py)
    self.set_color("black")
    side_label_pixmap_l.draw_layout(self.gc, 0,0, layout_l)
    side_label_pixmap_p.draw_layout(self.gc, 0,0, layout_p)
    little_y_offset = operator.div((py - yval),2)
    self.main_window.draw_drawable(self.gc,
                                   side_label_pixmap_l,
                                   0,
                                   0,
                                   X_DUAL_L_PIXMAP_OFFSET - (xval + 5),
                                   Y_DUAL_L_PIXMAP_OFFSET + little_y_offset,
                                   -1,
                                   -1)
    self.main_window.draw_drawable(self.gc,
                                   side_label_pixmap_p,
                                   0,
                                   0,
                                   X_DUAL_P_PIXMAP_OFFSET - (xval + 5),
                                   Y_DUAL_P_PIXMAP_OFFSET + little_y_offset,
                                   -1,
                                   -1)
                                                                                
                                                                                
                                                                                


  def draw_extent_labels_for_dualview_PV(self, p_pixmap):
    x,y = p_pixmap.get_size()
    x_padded = x + 30
    p_extent_label_pixmap = gtk.gdk.Pixmap(self.main_window, x_padded, (EXTENT_LABEL_OFFSET * 4))
    self.set_color_to_BG_color()
    p_extent_label_pixmap.draw_rectangle(self.gc, True, 0, 0, x_padded, (EXTENT_LABEL_OFFSET * 4))
    self.set_color("black")

    offset_counter = 1
    for vvol in self.p_viewable_vols:
      vexlist = vvol.get_viewable_extents()
      for vex in vexlist:
        if vex.get_is_selected() == True:
          layout = vex.get_horizontal_layout(7)
          start,span = vex.get_start_span()
          span_div_2 = int(operator.div(span,2))
          centerpix = start + span_div_2 + X_BOUND_DUAL_RADIUS + 4
          y_layout = (offset_counter - 1) * EXTENT_LABEL_OFFSET
          p_extent_label_pixmap.draw_line(self.gc,int(centerpix), 0, int(centerpix),offset_counter * EXTENT_LABEL_OFFSET) 
          p_extent_label_pixmap.draw_layout(self.gc, int(centerpix) + 2, y_layout, layout)
          if offset_counter == 4:
            offset_counter = 1
          else:
            offset_counter = offset_counter + 1

      self.main_window.draw_drawable(self.gc, p_extent_label_pixmap, 0, 0, X_DUAL_P_PIXMAP_OFFSET, Y_DUAL_P_PIXMAP_OFFSET + y + 1, -1, -1)


#  def draw_arcs(self, pixmap):
#    i = 0
#    for item in self.viewable_vols:
#      i = i + 1
#      x_val = item.get_start()
#      if x_val == 0:
#        continue
#      if(i == 5):
#        continue
#      if(i == 3):
#        x_val = x_val - 20
#      pixmap.draw_arc(self.gc, 0, x_val, 0, X_BOUND, Y_BOUND, 17280, 11520)
#
#    self.set_color("black")
#    for j in range(172, 300, 2):
#      pixmap.draw_arc(self.gc, 0, j, 0, X_BOUND, Y_BOUND, 17280, 11520)
#
#    pc = self.area.get_pango_context()
#    layout = pango.Layout(pc)
#    layout.set_text("/\nd\ne\nv\n/\nh\nd\na\n1\n")
#    pixmap.draw_layout(self.gc, 20, 20, layout)
#
    #Now draw arcs...
    #pixmap.draw_arc(self.gc, 0, 80, 0, X_BOUND, Y_BOUND, 17280, 11520)
    #pixmap.draw_arc(self.gc, 0, 130, 0, X_BOUND, Y_BOUND, 17280, 11520)
    #pixmap.draw_arc(self.gc, 0, 170, 0, X_BOUND, Y_BOUND, 17280, 11520)
    #pixmap.draw_arc(self.gc, 0, 195, 0, X_BOUND, Y_BOUND, 17280, 11520)
    #pixmap.draw_arc(self.gc, 0, 225, 0, X_BOUND, Y_BOUND, 17280, 11520)
    #pixmap.draw_arc(self.gc, 0, 275, 0, X_BOUND, Y_BOUND, 17280, 11520)

  
  #This method will slowly evolve into a more complex method. This
  #first cut will simply add size of all volumes on list and
  #divide into 300 pixels to get multiplier. The start 
  #points for each volume will then be calculated. Eventually,
  #this method will calculate the optimal size of the volume 
  #group and adjust values for MAX_X.
  def divide_volume(self, vlist):
    self.section_count = len(vlist)
    size = self.compute_vol_list_size(vlist)
    multiplier = operator.div(MAX_X,size)
    start_val = 0
    for item in vlist:
      span = multiplier * item.get_size()
      item.set_start_span(start_val, span)
      start_val = start_val + span
      #check if extentlist for volume size is > 0
      viewable_extents = item.get_viewable_extents()
      if len(viewable_extents) > 0:
        #If so, get vol from vvol and get total extents
        vol = item.get_volume()
        total,free,alloc = vol.get_extent_values()
        extent_multiplier = operator.div(span, total)
        starting_val = item.get_start()
        for ve in viewable_extents:
          extent_span = extent_multiplier * ve.get_extent_count()
          ve.set_start_span(starting_val, extent_span)
          starting_val = starting_val + extent_span
          

  def divide_single_volume(self, viewable):
    start_val = 0
    span = SINGLE_MAX_X
    viewable.set_start_span(start_val, span)
    #check if extentlist for volume size is > 0
    viewable_extents = viewable.get_viewable_extents()
    if len(viewable_extents) > 0:
      #If so, get vol from vvol and get total extents
      vol = viewable.get_volume()
      total,free,alloc = vol.get_extent_values()
      extent_multiplier = operator.div(float(span), float(total))
      starting_val = 0
      for ve in viewable_extents:
        extent_span = extent_multiplier * float(ve.get_extent_count())
        ve.set_start_span(starting_val, int(extent_span))
        starting_val = starting_val + extent_span


  def compute_vol_list_size(self, vlist):
    size = 0
    for item in vlist:
      size = size + item.get_size()
                                                                                
    return size

  def prep_volume_list(self, vlist):
    viewable_vols = list()
    for item in vlist:
      viewable = ViewableVolume(item, self.pango_context)
      extent_list = item.get_extent_segments()
      if len(extent_list) > 0:
        for extent in extent_list:
          viewable_extent = ViewableExtent(extent, self.pango_context)
          viewable.add_viewable_extent(viewable_extent)
      viewable_vols.append(viewable)

    return viewable_vols 

  def prep_volume(self, pv):
    viewable = ViewableVolume(pv, self.pango_context)
    extent_list = viewable.get_volume().get_extent_segments()
    if len(extent_list) > 0:
      for extent in extent_list:
        viewable_extent = ViewableExtent(extent, self.pango_context)
        viewable.add_viewable_extent(viewable_extent)

    return viewable 

  def initialize_label_layouts(self):
    self.label_layout_pixmap = gtk.gdk.Pixmap(self.main_window, LABEL_X, LABEL_Y)
    self.uninitialized_layout = pango.Layout(self.pango_context)
    self.uninitialized_layout.set_text(UNINITIALIZED_MESSAGE)

    self.unselected_layout = pango.Layout(self.pango_context)
    self.unselected_layout.set_text(UNSELECTED_MESSAGE)

    self.unallocated_layout = pango.Layout(self.pango_context)
    self.unallocated_layout.set_text(UNALLOCATED_MESSAGE)

  def clear_label_layout_pixmap(self):
    style = self.area.get_style()
    r = style.bg[gtk.STATE_NORMAL].red
    g = style.bg[gtk.STATE_NORMAL].green
    b = style.bg[gtk.STATE_NORMAL].blue
                                                                                
    self.gc.set_foreground(gtk.gdk.colormap_get_system().alloc_color(r,g,b, 1,1))
    self.label_layout_pixmap.draw_rectangle(self.gc, True, 0, 0, LABEL_X, LABEL_Y) 

  ##################################################
  ###Color setter section
  #This section contains convenience methods for setting colors
  #and clearing rendering sections
  def set_color(self, color):
    self.gc.set_foreground(gtk.gdk.colormap_get_system().alloc_color(color, 1,1))

  def set_color_to_BG_color(self):
    #Get the background color. This is used to paint background pixels.
    #This will need to be changed to use the alpha color eventually.
    style = self.area.get_style()
    r = style.bg[gtk.STATE_NORMAL].red
    g = style.bg[gtk.STATE_NORMAL].green
    b = style.bg[gtk.STATE_NORMAL].blue
    self.gc.set_foreground(gtk.gdk.colormap_get_system().alloc_color(r,g,b, 1,1))

  def clear_drawing_area(self):
    self.set_color_to_BG_color()
    rect = self.area.get_allocation()
    w = rect.width
    h = rect.height
    clear_pixmap = gtk.gdk.Pixmap(self.main_window, w, h)
    clear_pixmap.draw_rectangle(self.gc, 1, 0, 0, w, h)
    self.main_window.draw_drawable(self.gc, clear_pixmap, 0, 0, 0, 0, -1, -1)

  #################################################################
  ###Hash Table Generation Section
  #The following methods set up 3 hash tables for 3 differently
  #sized volume views. These tables make recomputing the arcs
  #for the three sizes of volumes each time it is necessary to:
  # 1) determine which section of a VG the mouse click occurred in
  # 2) draw a highlighted section or extent
  # 3) render the for right end of a volume or volume group
  def generate_hash_tables(self):

    self.generate_ellipse_hashtable()

    self.generate_dual_ellipse_hashtable()

    self.generate_single_vol_ellipse_hashtable()

  def generate_ellipse_hashtable(self):
    self.ellipse_hashtable = {}

    self.ellipse_hashtable.clear()
    for y in range(Y_BOUND_RADIUS, -Y_BOUND_RADIUS, -1):
      yy = y * y
      val1 = operator.div(yy, float(Y_BOUND_RADIUS * Y_BOUND_RADIUS))
      val2 = operator.sub(1.0, val1)
      x_squared = (float(X_BOUND_RADIUS * X_BOUND_RADIUS)) * val2
      x_offset_float = math.sqrt(operator.abs(x_squared))
      x_offset = int(math.ceil(x_offset_float))
      self.ellipse_hashtable[operator.abs(y - Y_BOUND_RADIUS)] = x_offset

  def generate_dual_ellipse_hashtable(self):

    self.dual_ellipse_hashtable = {}

    self.dual_ellipse_hashtable.clear()
    for y in range(Y_BOUND_DUAL_RADIUS, -Y_BOUND_DUAL_RADIUS, -1):
      yy = y * y
      val1 = operator.div(yy, float(Y_BOUND_DUAL_RADIUS * Y_BOUND_DUAL_RADIUS))
      val2 = operator.sub(1.0, val1)
      x_squared = (float(X_BOUND_DUAL_RADIUS * X_BOUND_DUAL_RADIUS)) * val2
      x_offset_float = math.sqrt(operator.abs(x_squared))
      x_offset = int(math.ceil(x_offset_float))
      self.dual_ellipse_hashtable[operator.abs(y - Y_BOUND_DUAL_RADIUS)] = x_offset

  def generate_single_vol_ellipse_hashtable(self):

    self.single_vol_ellipse_hashtable = {}

    self.single_vol_ellipse_hashtable.clear()
    for y in range(Y_BOUND_SINGLE_RADIUS, -Y_BOUND_SINGLE_RADIUS, -1):
      yy = y * y
      val1 = operator.div(yy, float(Y_BOUND_SINGLE_RADIUS * Y_BOUND_SINGLE_RADIUS))
      val2 = operator.sub(1.0, val1)
      x_squared = (float(X_BOUND_SINGLE_RADIUS * X_BOUND_SINGLE_RADIUS)) * val2
      x_offset_float = math.sqrt(operator.abs(x_squared))
      x_offset = int(math.ceil(x_offset_float))
      self.single_vol_ellipse_hashtable[operator.abs(y - Y_BOUND_SINGLE_RADIUS)] = x_offset

