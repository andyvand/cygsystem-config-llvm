

import sys
import pygtk
import gtk, gtk.glade



from cylinder_items import *

from lvmui_constants import *



GRADIENT_PV = "#ED1C2A"
GRADIENT_VG = "#2D6C23"
GRADIENT_LV = "#43ACE2"
GRADIENT_UV = "#404040"


HEIGHT_SINGLE = 100
HEIGHT_DUAL = 50
WIDTH_SINGLE = 200
WIDTH_MULTIPLE = 300
SMALLEST_SELECTABLE_WIDTH = 4

Y_OFFSET = 80


#UNINITIALIZED_MESSAGE=_("This extent has not yet been \n initialized for use with LVM.")
UNSELECTED_MESSAGE=_("No Volume Selected")
MULTIPLE_SELECTION_MESSAGE=_("Multiple selection")
#UNALLOCATED_MESSAGE=_("This Volume has not been allocated \n to a Volume Group yet.") 
LOGICAL_VOL_STR=_("Logical Volume")
PHYSICAL_VOL_STR=_("Physical Volume")
VOLUME_GRP_STR=_("Volume Group")
LOGICAL_VIEW_STR=_("Logical View")
PHYSICAL_VIEW_STR=_("Physical View")
UNALLOCATED_STR=_("Unallocated")
UNINITIALIZED_STR=_("Uninitialized")
DISK_ENTITY_STR=_("Disk Entity")
#EXTENTS_STR=_("extents")
#MEGABYTES_STR=_("Megabytes")



CYL_ID_VOLUME = 0
CYL_ID_FUNCTION = 1
CYL_ID_ARGS = 2





class DisplayView:
    
    def __init__(self,
                 register_selections_fcn, # to get absolete with rightclick
                 da1, # drawing area
                 properties_renderer1, 
                 da2=None, 
                 properties_renderer2=None):
        self.da = da1
        self.pr = properties_renderer1
        
        self.dvH = None # helper DisplayView
        if da2 != None:
            self.dvH = DisplayView(None, da2, properties_renderer2) 
        self.dvH_selectable = False
        
        self.gc = self.da.window.new_gc()
        white = gtk.gdk.colormap_get_system().alloc_color("white", 1,1)
        black = gtk.gdk.colormap_get_system().alloc_color("black", 1,1)
        self.gc.foreground = black
        self.gc.background = white
        
        self.da.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.da.connect('expose-event', self.expose)
        self.da.connect('button_press_event', self.mouse_event)
        
        self.message = ''
        
        self.display = None # Single or Double Cylinder
        
        lv_color = gtk.gdk.colormap_get_system().alloc_color(GRADIENT_LV, 1,1)
        pv_color = gtk.gdk.colormap_get_system().alloc_color(GRADIENT_PV, 1,1)
        uv_color = gtk.gdk.colormap_get_system().alloc_color(GRADIENT_UV, 1,1)
        vg_color = gtk.gdk.colormap_get_system().alloc_color(GRADIENT_VG, 1,1)
        self.pv_cyl_gen = CylinderGenerator(INSTALLDIR + '/pixmaps/PV.xpm', pv_color)
        self.lv_cyl_gen = CylinderGenerator(INSTALLDIR + '/pixmaps/LV.xpm', lv_color)
        self.uv_cyl_gen = CylinderGenerator(INSTALLDIR + '/pixmaps/UV.xpm', uv_color)
        self.vg_cyl_gen = CylinderGenerator(INSTALLDIR + '/pixmaps/VG.xpm', vg_color)
        
        
        # to be removed when right clicking gets implemented
        self.type = None
        self.register_selections_fcn = register_selections_fcn
        
        
    
    def render_pv(self, pv):
        if self.dvH != None:
            self.dvH.render_no_selection()
            self.dvH_selectable = True
        
        self.type = PHYS_TYPE
        
        # display properties
        self.pr.render_to_layout_area(pv.getProperties(), pv.get_path(), PHYS_TYPE)
        
        # display cylinder
        line1 = "<span foreground=\"" + GRADIENT_PV + "\" size=\"8000\"><b>" + PHYSICAL_VOL_STR + "</b></span>\n"
        line2 = "<span size=\"8000\"><b>" + pv.get_path() + "</b></span>"
        label = line1 + line2
        self.display = SingleCylinder(False, '', label, SMALLEST_SELECTABLE_WIDTH, WIDTH_MULTIPLE, HEIGHT_SINGLE)
        self.display.append_right(End(self.pv_cyl_gen))
        # TODO: sort them
        for extent in pv.get_extent_segments():
            if extent.is_utilized():
                cyl = Subcylinder(self.pv_cyl_gen, 1, 1, True, extent.get_start_size()[1])
            else:
                cyl = Subcylinder(self.pv_cyl_gen, 1, 1, False, extent.get_start_size()[1])
            label = "<span size=\"7000\">"
            label = label + extent.get_name() + '\n'
            label = label + extent.get_annotation() + '\n'
            label = label + str(extent.get_start_size()[1]) + ' extents'
            label = label + "</span>"
            cyl.set_label_lower(label)
            self.display.append_right(cyl)
            self.display.append_right(Separator())
            # set up helper display
            cyl.add_object(CYL_ID_VOLUME, extent)
            cyl.add_object(CYL_ID_FUNCTION, DisplayView.render_ext)
            cyl.add_object(CYL_ID_ARGS, [extent])
        self.draw()
    
    def render_unalloc_pv(self, pv):
        if self.dvH != None:
            self.dvH.render_none()
            self.dvH_selectable = False
        
        self.type = None
        
        # display properties
        self.pr.render_to_layout_area(pv.getProperties(), pv.get_path(), UNALLOCATED_TYPE)
        
        # display cylinder
        line1 = "<span foreground=\"" + GRADIENT_PV + "\" size=\"8000\"><b>" + UNALLOCATED_STR + "</b></span>"
        line2 = "<span foreground=\"" + GRADIENT_PV + "\" size=\"8000\"><b>" + PHYSICAL_VOL_STR + "</b></span>"
        line3 = "<span size=\"8000\"><b>" + pv.get_path() + "</b></span>"
        label = line1 + "\n" + line2 + "\n" + line3
        self.display = SingleCylinder(True, '', label, SMALLEST_SELECTABLE_WIDTH, WIDTH_SINGLE, HEIGHT_SINGLE)
        self.display.append_right(End(self.pv_cyl_gen))
        cyl = Subcylinder(self.pv_cyl_gen, 1, 1, False, 1)
        self.display.append_right(cyl)
        self.draw()
    
    def render_uninit_pv(self, pv):
        if self.dvH != None:
            self.dvH.render_none()
            self.dvH_selectable = False
        
        self.type = None
        
        # display properties
        self.pr.render_to_layout_area(pv.getProperties(), pv.get_path(), UNINITIALIZED_TYPE)
        
        # display cylinder
        line1 = "<span size=\"8000\"><b>" + UNINITIALIZED_STR + "</b></span>\n"
        line2 = "<span size=\"8000\"><b>" + DISK_ENTITY_STR + "</b></span>\n"
        line3 = "<span size=\"8000\"><b>" + pv.get_path() + "</b></span>"
        label = line1 + line2 + line3
        self.display = SingleCylinder(True, '', label, SMALLEST_SELECTABLE_WIDTH, WIDTH_SINGLE, HEIGHT_SINGLE)
        self.display.append_right(End(self.uv_cyl_gen))
        cyl = Subcylinder(self.uv_cyl_gen, 1, 1, False, 1)
        self.display.append_right(cyl)
        self.draw()
    
    def render_pvs(self, vg, pv_list):
        if self.dvH != None:
            self.dvH.render_no_selection()
            self.dvH_selectable = True
        
        self.type = VG_PHYS_TYPE
        
        # display properties
        self.pr.render_to_layout_area(vg.getProperties(), vg.get_name(), VG_PHYS_TYPE)
        
        # display cylinder
        line1 = "<span size=\"7000\"><b>" + VOLUME_GRP_STR + "</b></span>\n"
        line2 = "<span size=\"7000\"><b>" + pv_list[0].get_vg_name() + "</b></span>\n"
        line3 = "<span foreground=\"" + GRADIENT_PV + "\" size=\"8000\"><i>" + PHYSICAL_VIEW_STR + "</i></span>" 
        label = line1 + line2 + line3
        self.display = SingleCylinder(False, '', label, SMALLEST_SELECTABLE_WIDTH, WIDTH_MULTIPLE, HEIGHT_SINGLE)
        self.display.append_right(End(self.pv_cyl_gen))
        for pv in pv_list:
            selectable = pv.is_utilized
            cyl = Subcylinder(self.pv_cyl_gen, 1, 2, selectable, int(pv.get_volume_size()))
            #label = "<span foreground=\"" + GRADIENT_PV + "\" size=\"8000\">" + pv.get_name() + "</span>"
            label = pv.get_name()
            cyl.set_label_upper(label)
            self.display.append_right(cyl)
            self.display.append_right(Separator())
            # set up helper display
            cyl.add_object(CYL_ID_VOLUME, pv)
            cyl.add_object(CYL_ID_FUNCTION, DisplayView.render_pv)
            cyl.add_object(CYL_ID_ARGS, [pv])
        self.draw()
    
    def render_lv(self, lv):
        if self.dvH != None:
            self.dvH.render_none()
            self.dvH_selectable = False
        
        self.type = None
        
        # display properties
        self.pr.render_to_layout_area(lv.getProperties(), lv.get_path(), LOG_TYPE)
        
        # display cylinder
        line1 = "<span foreground=\"" + GRADIENT_LV + "\" size=\"8000\"><b>" + LOGICAL_VOL_STR + "</b></span>\n"
        line2 = "<span size=\"8000\"><b>" + lv.get_path() + "</b></span>"
        label = line1 + line2
        self.display = SingleCylinder(True, '', label, SMALLEST_SELECTABLE_WIDTH, WIDTH_SINGLE, HEIGHT_SINGLE)
        self.display.append_right(End(self.lv_cyl_gen))
        cyl = Subcylinder(self.lv_cyl_gen, 1, 1, False, 1)
        self.display.append_right(cyl)
        self.draw()
    
    def render_lvs(self, vg, lv_list):
        if self.dvH != None:
            self.dvH.render_no_selection()
            self.dvH_selectable = True
        
        self.type = VG_LOG_TYPE
        
        # display properties
        self.pr.render_to_layout_area(vg.getProperties(), vg.get_name(), VG_LOG_TYPE)
        
        # display cylinder
        line1 = "<span size=\"7000\"><b>" + VOLUME_GRP_STR + "</b></span>\n"
        line2 = "<span size=\"7000\"><b>" + lv_list[0].get_vg_name() + "</b></span>\n"
        line3 = "<span foreground=\"" + GRADIENT_LV + "\" size=\"8000\"><i>" + LOGICAL_VIEW_STR + "</i></span>" 
        label = line1 + line2 + line3
        self.display = SingleCylinder(False, '', label, SMALLEST_SELECTABLE_WIDTH, WIDTH_MULTIPLE, HEIGHT_SINGLE)
        self.display.append_right(End(self.lv_cyl_gen))
        for lv in lv_list:
            selectable = lv.is_utilized
            cyl = Subcylinder(self.lv_cyl_gen, 1, 2, selectable, lv.size_extents)
            #label = "<span foreground=\"" + GRADIENT_LV + "\" size=\"8000\">" + lv.get_name() + "</span>"
            label = lv.get_name()
            cyl.set_label_upper(label)
            self.display.append_right(cyl)
            self.display.append_right(Separator())
            # set up helper display
            cyl.add_object(CYL_ID_VOLUME, lv)
            cyl.add_object(CYL_ID_FUNCTION, DisplayView.render_lv)
            cyl.add_object(CYL_ID_ARGS, [lv])
        self.draw()
    
    def render_vg(self, vg, lv_list, pv_list):
        if self.dvH != None:
            self.dvH.render_no_selection()
            self.dvH_selectable = True
        
        self.type = None
        
        # display properties
        self.pr.render_to_layout_area(vg.getProperties(), vg.get_name(), VG_TYPE)
        
        # display cylinder
        line1 = "<span size=\"7000\"><b>" + VOLUME_GRP_STR + "</b></span>\n"
        line2 = "<span size=\"7000\"><b>" + lv_list[0].get_vg_name() + "</b></span>\n"
        line3 = "<span foreground=\"" + GRADIENT_LV + "\" size=\"8000\"><i>" + LOGICAL_VIEW_STR + "</i></span>" 
        label_upper = line1 + line2 + line3
        line1 = "<span size=\"7000\"><b>" + VOLUME_GRP_STR + "</b></span>\n"
        line2 = "<span size=\"7000\"><b>" + pv_list[0].get_vg_name() + "</b></span>\n"
        line3 = "<span foreground=\"" + GRADIENT_PV + "\" size=\"8000\"><i>" + PHYSICAL_VIEW_STR + "</i></span>" 
        label_lower = line1 + line2 + line3
        self.display = DoubleCylinder(Y_OFFSET, '', label_upper, label_lower, 5, WIDTH_MULTIPLE, HEIGHT_DUAL)
        
        lv_cyls_dir = {}
        lv_cyls = []
        for lv in lv_list:
            #label = "<span foreground=\"" + GRADIENT_LV + "\" size=\"8000\">" + lv.get_name() + "</span>"
            label = lv.get_name()
            cyl = None
            if lv.is_utilized:
                cyl = Subcylinder(self.lv_cyl_gen, 1, 2, True)
                lv_cyls_dir[lv.get_name()] = cyl
            else:
                cyl = Subcylinder(self.lv_cyl_gen, 1, 2, False, lv.size_extents)
            cyl.set_label_upper(label)
            lv_cyls.append(cyl)
            # set up helper display
            cyl.add_object(CYL_ID_VOLUME, lv)
            cyl.add_object(CYL_ID_FUNCTION, DisplayView.render_lv)
            cyl.add_object(CYL_ID_ARGS, [lv])
            
        pv_cyls = []
        for pv in pv_list:
            #pv_cyl = Subcylinder(self.pv_cyl_gen, 1, 2, True)
            pv_cyl = Subcylinder(self.pv_cyl_gen, 1, 2, False)
            #label = "<span foreground=\"" + GRADIENT_PV + "\" size=\"8000\">" + pv.get_name() + "</span>"
            label = pv.get_name()
            pv_cyl.set_label_upper(label)
            pv_cyls.append(pv_cyl)
            # set up helper display
            pv_cyl.add_object(CYL_ID_VOLUME, pv)
            pv_cyl.add_object(CYL_ID_FUNCTION, DisplayView.render_pv)
            pv_cyl.add_object(CYL_ID_ARGS, [pv])
            exts = pv.get_extent_segments()
            for ext in exts:
                width = ext.get_start_size()[1]
                ext_cyl_p = Subcylinder(self.pv_cyl_gen, 1, 2, False, width)
                label = "<span size=\"7000\">"
                label = label + ext.get_annotation() + '\n'
                label = label + str(ext.get_start_size()[1]) + ' extents'
                label = label + "</span>"
                ext_cyl_p.set_label_lower(label, False, False, True)
                if ext.is_utilized():
                    ext_cyl_l = Subcylinder(self.lv_cyl_gen, 1, 2, False, width)
                    ext_cyl_l.add_highlightable(ext_cyl_p)
                    lv_cyls_dir[ext.get_name()].children.append(ext_cyl_l)
                pv_cyl.children.append(ext_cyl_p)
        
        self.display.append_right(True, End(self.lv_cyl_gen))
        for lv_cyl in lv_cyls:
            self.display.append_right(True, lv_cyl)
            self.display.append_right(True, Separator())
        
        self.display.append_right(False, End(self.pv_cyl_gen))
        for pv_cyl in pv_cyls:
            self.display.append_right(False, pv_cyl)
            self.display.append_right(False, Separator())
        
        self.draw()
    
    def render_ext(self, ext):
        # TODO: implement extent view
        if self.dvH != None:
            self.dvH.render_none()
            self.dvH_selectable = False
        self.render_text(_("extent view"))
        
        self.type = None
        
        return
    
    def render_no_selection(self):
        #self.render_text(UNSELECTED_MESSAGE)
        self.render_text('')
        self.dvH_selectable = True
        
        self.type = None
        
    def render_none(self):
        self.render_text('')
        self.dvH_selectable = False
        
        self.type = None
        
    def render_multiple_selection(self):
        self.render_text(MULTIPLE_SELECTION_MESSAGE)
        self.dvH_selectable = True
        
        self.type = None
        
    def render_text(self, txt):
        # clear properties
        self.pr.clear_layout_area()
        # set up message
        self.message = txt
        self.display = None
        # draw
        self.draw()
        # render helper
        if self.dvH != None:
            self.dvH.render_none()
        
        self.type = None
        
        
        
    
    def expose(self, obj1, obj2):
        self.draw()
    
    def draw(self):
        if self.display != None:
            self.display.draw(self.da, self.gc, (10, Y_OFFSET))
        else:
            # clear pixmap
            pixmap = self.da.window
            (w, h) = pixmap.get_size()
            back = self.gc.foreground
            self.gc.foreground = self.gc.background
            pixmap.draw_rectangle(self.gc, True, 0, 0, w, h)
            self.gc.foreground = back
            
            # draw message
            layout = self.da.create_pango_layout('')
            layout.set_markup(self.message)
            label_w, label_h = layout.get_pixel_size()
            #pixmap.draw_layout(self.gc, (w-label_w)/2, (h-label_h)/2, layout)
            pixmap.draw_layout(self.gc, 180, 180, layout)
        
    def mouse_event(self, obj, event, *args):
        if event.type == gtk.gdk.BUTTON_PRESS:
            #	print 'single click'
            #       print 'button', event.button
            #	print 'time', event.time
            #	print 'x', event.x
            #	print 'y', event.y
            pass
        elif event.type == gtk.gdk._2BUTTON_PRESS:
            #	print 'double click'
            #	print 'button', event.button
            #	print 'time', event.time
            #	print 'x', event.x
            #	print 'y', event.y
            pass
        elif event.type == gtk.gdk._3BUTTON_PRESS:
            #	print 'triple click'
            #	print 'button', event.button
            #	print 'time', event.time
            #	print 'x', event.x
            #	print 'y', event.y
            pass
        else:
            print 'unknown mouse event'
        
        if self.display != None:
            self.display.click((int(event.x), int(event.y)), event.button==1)
            
            selection = self.display.get_selection()
            
            # register selection
            if self.register_selections_fcn != None and self.type != None:
                sels = []
                for sel in selection:
                    sels.append(sel.get_object(CYL_ID_VOLUME))
                self.register_selections_fcn(self.type, sels)
            
            # render helper DisplayView
            if self.dvH != None:
                if len(selection) == 0:
                    if self.dvH_selectable:
                        self.dvH.render_no_selection()
                    else:
                        self.dvH.render_none()
                elif len(selection) == 1:
                    # render to dvH
                    cyl = selection[0]
                    volume = cyl.get_object(CYL_ID_VOLUME)
                    render_fct = cyl.get_object(CYL_ID_FUNCTION)
                    args = cyl.get_object(CYL_ID_ARGS)
                    if len(args) == 0:
                        render_fct(self.dvH)
                    elif len(args) == 1:
                        render_fct(self.dvH, args[0])
                    elif len(args) == 2:
                        render_fct(self.dvH, args[0], args[1])
                    elif len(args) == 3:
                        render_fct(self.dvH, args[0], args[1], args[2])
                else:
                    self.dvH.render_multiple_selection()
            
            self.draw()
