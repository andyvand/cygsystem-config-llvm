

import math
import operator

import pygtk
import gtk, gtk.gdk



class Widget:

    def __init__(self):
        self.left_clickable = False
        self.right_clickable = False
        
        self.objects = {}
        
    def draw(self, dc, gc, (x, y)):
        pass
    
    def click(self, (x, y), leftClick): # local coordinates
        return None # nothing selected
    
    def add_object(self, id, obj):
        self.objects[id] = obj
    
    def get_object(self, id):
        return self.objects[id]
    
class Highlight:

    def __init__(self):
        self.highlighted = False
        self.also_highlight = []
    
    def add_highlightable(self, obj):
        self.also_highlight.append(obj)
    
    def remove_highlightable(self, obj):
        self.also_highlight.remove(obj)
    
    def highlight(self):
        for ch in self.also_highlight:
            ch.highlighted = True
        
    def unhighlight(self):
        for ch in self.also_highlight:
            ch.highlighted = False
    
    

class CylinderItem(Widget):
    
    def __init__(self,
                 selectable=False,
                 width=0,
                 height=0,
                 label_upper='',
                 label_lower=''):
        
        Widget.__init__(self)
        
        self.children = []
        self.ratio = 1 # pixels/width
        self.width = width
        self.height = height
        self.selectable = selectable
        self.selected = False
        
        self.label_upper = label_upper
        self.LU_showAlways = True
        self.LU_showAtSelected = False
        self.LU_showAtHighlighted = False
        
        self.label_lower = label_lower
        self.LL_showAlways = True
        self.LL_showAtSelected = False
        self.LL_showAtHighlighted = False
        
        self.highlighted = False
        
        self.anchors = {}
        
        
    def set_label_upper(self, text, showAlways=True, showAtSelected=False, showAtHighlighted=False):
        self.label_upper = text
        self.LU_showAlways = showAlways
        self.LU_showAtSelected = showAtSelected
        self.LU_showAtHighlighted = showAtHighlighted
        
    def set_label_lower(self, text, showAlways=True, showAtSelected=False, showAtHighlighted=False):
        self.label_lower = text
        self.LL_showAlways = showAlways
        self.LL_showAtSelected = showAtSelected
        self.LL_showAtHighlighted = showAtHighlighted
        
    def get_label_upper(self):
        return self.label_upper
    def get_label_lower(self):
        return self.label_lower
    
    def get_selected(self):
        return self.selected
    def set_selected(self, bool):
        self.selected = bool
        for child in self.children:
            child.set_selected(bool)
        
    def set_height(self, height):
        self.height = height
        for child in self.children:
            child.set_height(height)
    
    def draw(self, dc, gc, (x, y)):
        x = x + self.get_width()
        self.children.reverse()
        for child in self.children:
            x = x - child.get_width()
            child.draw(dc, gc, (x, y))
        self.children.reverse()
        
    def get_labels_upper(self):
        return self.__get_labels(True)
    def get_labels_lower(self):
        return self.__get_labels(False)
    def __get_labels(self, upper):
        labels = []
        if upper:
            if self.label_upper != '':
                if self.LU_showAlways or (self.selected and self.LU_showAtSelected) or (self.highlighted and self.LU_showAtHighlighted):
                    offset = self.get_width() / 2
                    labels.append((self.label_upper, offset))
        else:
            if self.label_lower != '':
                if self.LL_showAlways or (self.selected and self.LL_showAtSelected) or (self.highlighted and self.LL_showAtHighlighted):
                    offset = self.get_width() / 2
                    labels.append((self.label_lower, offset))
        # set offset of childrens' labels
        offset = 0
        for child in self.children:
            ch_labels = child.__get_labels(upper)
            for label in ch_labels:
                labels.append((label[0], label[1] + offset))
            offset = offset + child.get_width()
        return labels
    
    def get_smallest_selectable_width(self):
        maximum = 100000000
        smallest = maximum
        for child in self.children:
            width = child.get_smallest_selectable_width()
            if width == 0:
                continue
            if width < smallest:
                smallest = width
        
        if self.get_width() < smallest and self.selectable:
            smallest = self.get_width()
        if smallest == maximum:
            return 0
        else:
            return smallest
    
    def get_width(self): # returns width adjusted by ratio
        if self.width != 0:
            # end_node
            width = int(self.width * self.ratio)
            if width == 0:
                return 1
            return width
        width = 0
        for child in self.children:
            width = width + child.get_width()
        return width
    
    def set_ratio(self, ratio):
        self.ratio = ratio
        for child in self.children:
            child.set_ratio(ratio)
    
    def click(self, (x, y), leftClick):
        if x > self.get_width():
            return None
        
        if self.selectable and leftClick and self.left_clickable:
            print 'left clicked'
            return self
        if self.right_clickable and not leftClick:
            print 'right clicked'
            return self
        
        # propagate click
        offset = 0
        for child in self.children:
            child_width = child.get_width()
            if (x > offset) and (x < offset + child_width):
                return child.click((x - offset, y), leftClick)
            offset = offset + child_width
        return None
    
    def set_anchor(self, id, perc):
        self.anchors[id] = perc
    def get_anchors(self):
        anchors = []
        width = self.get_width()
        if self.selected or self.highlighted:
            for id in self.anchors:
                anchors.append((id, int(width * self.anchors[id])))
        
        # set offset of childrens' anchors
        offset = 0
        for child in self.children:
            for anchor in child.get_anchors():
                anchors.append((anchor[0], anchor[1] + offset))
            offset = offset + child.get_width()
        return anchors
    
    

class Separator(CylinderItem):
    
    def __init__(self, width=1):
        CylinderItem.__init__(self, False, width)

    def get_width(self):
        # no ratio adjustment
        return self.width
    
    def get_smallest_selectable_width(self):
        return 0

class End(CylinderItem):
    
    def __init__(self, cyl_gen):
        CylinderItem.__init__(self)
        self.cyl_gen = cyl_gen
    
    def draw(self, dc, gc, (x, y)):
        self.cyl_gen.draw_end(dc, gc, x, y, self.height)
    
    def get_smallest_selectable_width(self):
        return 0
    

class Subcylinder(CylinderItem, Highlight):
    
    def __init__(self, 
                 cyl_gen=None, 
                 selectedPattern=None, 
                 highlightedPattern=None, 
                 selectable=False, 
                 width=0):
        CylinderItem.__init__(self, selectable, width, 0)
        Highlight.__init__(self)
        
        if selectable:
            self.left_clickable = True
        #self.right_clickable = True
        
        self.cyl_gen = cyl_gen
        
        self.selectedPattern = selectedPattern
        self.highlightedPattern = highlightedPattern
        
    
    def set_patterns(self, selected, highlighted):
        self.selectedPattern = selected
        self.highlightedPattern = highlighted
    
    def set_selected(self, bool):
        CylinderItem.set_selected(self, bool)
        if bool:
            self.highlight()
        else:
            self.unhighlight()
    
    def draw(self, dc, gc, (x, y)):
        # draw children
        CylinderItem.draw(self, dc, gc, (x, y))
        
        if self.cyl_gen == None:
            return
        # draw self
        if self.width != 0:
            cyl_pix = self.cyl_gen.get_cyl(dc, self.get_width(), self.height)
            dc.draw_pixbuf(gc, cyl_pix, 0, 0, x, y)
        # draw highlighted pattern
        if self.highlighted:
            cyl_pix = self.cyl_gen.get_pattern(self.highlightedPattern, dc, self.get_width(), self.height)
            dc.draw_pixbuf(gc, cyl_pix, 0, 0, x, y)
        # draw selection pattern
        if self.selected:
            cyl_pix = self.cyl_gen.get_pattern(self.selectedPattern, dc, self.get_width(), self.height)
            dc.draw_pixbuf(gc, cyl_pix, 0, 0, x, y)
        
    
    def click(self, (x, y), leftClick): # local coordinates
        selection = CylinderItem.click(self, (x, y), leftClick)
        if leftClick:
            # left click handling
            return selection
        else:
            # right click handling
            return selection
        
    
class SingleCylinder:
    
    def __init__(self,
                 exclusive_selection,
                 name='',
                 label='',
                 smallest_clickable_width=1,
                 width=200, # fullfilled only if smallest_clickable_width is met
                 height=1):
        
        self.cyl = Subcylinder()
        self.cyl_drawn_at = (0, 0)
        
        self.smallest_clickable_width = smallest_clickable_width
        self.width = width
        self.height = height
        
        self.exclusive_selection = exclusive_selection
        self.selection = []
        
        self.name = name
        self.label = label
        
    
    def get_selection(self):
        return self.selection
    
    def click(self, (x, y), leftClick):
        (ellipse_table, x_radius) = get_ellipse_table(self.height/2)
        
        cyl_x = self.cyl_drawn_at[0]
        cyl_y = self.cyl_drawn_at[1]
        if not (y > cyl_y and y < cyl_y + self.height):
            return None
        if not (x > cyl_x and x < cyl_x + self.cyl.get_width() + x_radius):
            return None
        # click is in a rectangle, change to local coordinates
        y = y - cyl_y
        x = x - cyl_x - ellipse_table[y]
        if x < 0:
            return None
        
        selected = self.cyl.click((x, y), leftClick) # local coordinates
        if leftClick:
            if selected in self.selection:
                selected.set_selected(False)
                self.selection.remove(selected)
                return
            
            if self.exclusive_selection:
                # single selection only
                if selected != None:
                    if len(self.selection) != 0:
                        self.selection[0].set_selected(False)
                        self.selection = []
                    selected.set_selected(True)
                    self.selection.append(selected)
            else:
                if selected != None:
                    selected.set_selected(True)
                    self.selection.append(selected)
            
    
    def append_right(self, child):
        self.cyl.children.append(child)
        self.cyl.set_height(self.height)
        
        # adjust width
        self.cyl.set_ratio(1)
        width = self.cyl.get_width()
        if width == 0:
            return
        else:
            self.cyl.set_ratio(float(self.width)/width)
        
        smallest = self.cyl.get_smallest_selectable_width()
        if smallest == 0:
            return
        elif smallest < self.smallest_clickable_width:
            self.cyl.set_ratio(1)
            smallest = self.cyl.get_smallest_selectable_width()
            self.cyl.set_ratio(self.smallest_clickable_width/float(smallest))
        
    
    def set_height(self, height):
        self.height = height
        self.cyl.set_height(height)
    
    def draw(self, da, gc, (x, y)):
        dc = da.window
        (w, h) = dc.get_size()
        pixmap = gtk.gdk.Pixmap(dc, w, h) # buffer
        
        # clear
        front = gc.foreground
        gc.foreground = gc.background
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)
        gc.foreground = front
        
        # draw name
        #layout = da.create_pango_layout(self.name)
        #label_w, label_h = layout.get_pixel_size()
        #pixmap.draw_layout(gc, x, y + (self.height - label_h) / 2, layout)
        
        # draw main label
        layout = da.create_pango_layout('')
        layout.set_markup(self.label)
        label_w, label_h = layout.get_pixel_size()
        pixmap.draw_layout(gc, x, y+(self.height-label_h)/2, layout)
        
        # draw cylinder
        x = x + label_w + get_ellipse_table(self.height/2)[1] + 10
        self.cyl.draw(pixmap, gc, (x, y))
        self.cyl_drawn_at = (x, y)
        
        # draw labels
        draw_cyl_labels_upper(da, pixmap, gc,
                                   self.cyl.get_labels_upper(), 
                                   x, y)
        draw_cyl_labels_lower(da, pixmap, gc,
                                   self.cyl.get_labels_lower(), 
                                   x, y, self.height)
        
        # double buffering
        dc.draw_drawable(gc, pixmap, 0, 0, 0, 0, w, h)
        
def draw_cyl_labels_upper(da, pixmap, gc, labels, x, y):
        # sort
        labels_t = labels
        labels = []
        while len(labels_t) != 0:
            largest = labels_t[0]
            for label in labels_t:
                if label[1] > largest[1]:
                    largest = label
            labels_t.remove(largest)
            labels.append(largest)
        
        X_boundry = 1000000 # used for offset adjustment
        offset_default = 0
        offset = offset_default
        length = 30
        for label in labels:
            layout = da.create_pango_layout('')
            layout.set_markup(label[0])
            label_w, label_h = layout.get_pixel_size()
            X1 = x + label[1]
            Y1 = y
            X2 = X1 - int(math.cos(math.pi/4) * length)
            Y2 = Y1 - int(math.sin(math.pi/4) * length)
            X3 = X2
            if X2 + label_w + 3 > X_boundry:
                offset = offset + label_h
            else:
                offset = offset_default
            Y3 = Y2 - offset - label_h / 2
            X_boundry = X2
            pixmap.draw_line(gc, X1, Y1, X2, Y2)
            pixmap.draw_line(gc, X2, Y2, X3, Y3)
            X_lay = X2 + 2
            Y_lay = Y3 - label_h/2
            back = gc.foreground
            gc.foreground = gc.background
            pixmap.draw_rectangle(gc, True, X_lay, Y_lay, label_w, label_h)
            gc.foreground = back
            pixmap.draw_layout(gc, X_lay, Y_lay, layout)

def draw_cyl_labels_lower(da, pixmap, gc, labels, x, y, cyl_height):
        # sort
        labels_t = labels
        labels = []
        while len(labels_t) != 0:
            largest = labels_t[0]
            for label in labels_t:
                if label[1] > largest[1]:
                    largest = label
            labels_t.remove(largest)
            labels.append(largest)
        
        X_boundry = 1000000 # used for offset adjustment
        height = int(cyl_height * 5 / 8)
        X_offset = get_ellipse_table(cyl_height/2)[0][height]
        offset_default = cyl_height - height + 10
        offset = offset_default
        for label in labels:
            layout = da.create_pango_layout('')
            layout.set_markup(label[0])
            label_w, label_h = layout.get_pixel_size()
            X1 = x + label[1] + X_offset
            Y1 = y + height
            X2 = X1
            Y2 = Y1 + label_h
            X3 = X2 + label_w
            if X3 + 3 > X_boundry:
                offset = offset + label_h + 1
            else:
                offset = offset_default
            Y2 = Y2 + offset
            Y3 = Y2
            X_boundry = X1
            pixmap.draw_line(gc, X1, Y1, X2, Y2)
            pixmap.draw_line(gc, X2, Y2, X3, Y3)
            X_lay = X2 + 2
            Y_lay = Y2 - label_h
            back = gc.foreground
            gc.foreground = gc.background
            pixmap.draw_rectangle(gc, True, X_lay, Y_lay, label_w, label_h)
            gc.foreground = back
            pixmap.draw_layout(gc, X_lay, Y_lay, layout)
        

class DoubleCylinder:
    
    def __init__(self,
                 distance, 
                 name='', 
                 label_upper='', 
                 label_lower='', 
                 smallest_clickable_width=1, 
                 width=200, # fullfilled only if smallest_clickable_width is met
                 height=1):
        
        self.cyl_upper = Subcylinder()
        self.cyl_lower = Subcylinder()
        self.cyl_upper_drawn_at = (0, 0)
        self.cyl_lower_drawn_at = (0, 0)
        
        self.label_upper = label_upper
        self.label_lower = label_lower
        
        self.width = width
        self.height = height
        self.smallest_clickable_width = smallest_clickable_width
        
        self.distance = distance
        
        self.selection = None
        
        self.name = name
        
    
    def get_selection(self):
        if self.selection == None:
            return []
        return [self.selection]
    
    def click(self, (x, y), leftClick):
        (ellipse_table, x_radius) = get_ellipse_table(self.height/2)
        
        cyl = None
        
        cyl_x = self.cyl_upper_drawn_at[0]
        cyl_y = self.cyl_upper_drawn_at[1]
        if x > cyl_x and x < cyl_x + self.cyl_upper.get_width() + x_radius:
            if y > cyl_y and y < cyl_y + self.height:
                cyl = self.cyl_upper
        if cyl == None:
            cyl_x = self.cyl_lower_drawn_at[0]
            cyl_y = self.cyl_lower_drawn_at[1]
            if x > cyl_x and x < cyl_x + self.cyl_lower.get_width() + x_radius:
                if y > cyl_y and y < cyl_y + self.height:
                    cyl = self.cyl_lower
        
        if cyl == None:
            return None
        
        # click is in a rectangle, change to local coordinates
        y = y - cyl_y
        x = x - cyl_x - ellipse_table[y]
        if x < 0:
            return None
        
        selected = cyl.click((x, y), leftClick) # local coordinates
        if leftClick:
            if selected == self.selection and selected != None:
                selected.set_selected(False)
                self.selection = None
                return
            if selected != None:
                if self.selection != None:
                    self.selection.set_selected(False)
                selected.set_selected(True)
                self.selection = selected
            
    
    def append_right(self, upper, child):
        cyl = None
        if upper:
            cyl = self.cyl_upper
        else:
            cyl = self.cyl_lower
        
        cyl.children.append(child)
        cyl.set_height(self.height)
        
        
        # adjust width
        cyl.set_ratio(1)
        width = cyl.get_width()
        if width == 0:
            return
        else:
            cyl.set_ratio(float(self.width)/width)
        
        smallest = cyl.get_smallest_selectable_width()
        if smallest == 0:
            return
        elif smallest < self.smallest_clickable_width:
            cyl.set_ratio(1)
            smallest = cyl.get_smallest_selectable_width()
            cyl.set_ratio(self.smallest_clickable_width/float(smallest))
    
    def set_height(self, height):
        self.height = height
        self.cyl_upper.set_height(height)
        self.cyl_lower.set_height(height)
    
    def draw(self, da, gc, (x, y)):
        dc = da.window
        (w, h) = dc.get_size()
        pixmap = gtk.gdk.Pixmap(dc, w, h) # buffer
        
        # clear
        front = gc.foreground
        gc.foreground = gc.background
        pixmap.draw_rectangle(gc, True, 0, 0, w, h)
        gc.foreground = front
        
        # draw name
        #layout = da.create_pango_layout(self.name)
        #label_w, label_h = layout.get_pixel_size()
        #pixmap.draw_layout(gc, x, y + (self.height - label_h) / 2, layout)
        
        # draw upper label
        layout = da.create_pango_layout('')
        layout.set_markup(self.label_upper)
        label_w, label_h = layout.get_pixel_size()
        pixmap.draw_layout(gc, x, y + (self.height-label_h)/2, layout)
        max_label_w = label_w
        # draw lower label
        layout = da.create_pango_layout('')
        layout.set_markup(self.label_lower)
        label_w, label_h = layout.get_pixel_size()
        pixmap.draw_layout(gc,
                           x,
                           y + self.height + self.distance + (self.height - label_h)/2,
                           layout)
        if label_w > max_label_w:
            max_label_w = label_w
        
        # draw upper cylinder
        x = x + max_label_w + get_ellipse_table(self.height/2)[1] + 10
        self.cyl_upper.draw(pixmap, gc, (x, y))
        self.cyl_upper_drawn_at = (x, y)
        # draw lower cylinder
        self.cyl_lower.draw(pixmap, gc, (x, y + self.height + self.distance))
        self.cyl_lower_drawn_at = (x, y + self.height + self.distance)
        
        # draw mapping lines
        self.draw_mappings(pixmap, gc)
        
        # draw cylinders' labels
        # upper cylinder
        draw_cyl_labels_upper(da, pixmap, gc,
                              self.cyl_upper.get_labels_upper(), 
                              self.cyl_upper_drawn_at[0], 
                              self.cyl_upper_drawn_at[1])
        draw_cyl_labels_lower(da, pixmap, gc,
                              self.cyl_upper.get_labels_lower(), 
                              self.cyl_upper_drawn_at[0], 
                              self.cyl_upper_drawn_at[1],
                              self.height)
        # lower cylinder
        draw_cyl_labels_upper(da, pixmap, gc, 
                              self.cyl_lower.get_labels_upper(), 
                              self.cyl_lower_drawn_at[0], 
                              self.cyl_lower_drawn_at[1])
        draw_cyl_labels_lower(da, pixmap, gc, 
                              self.cyl_lower.get_labels_lower(), 
                              self.cyl_lower_drawn_at[0], 
                              self.cyl_lower_drawn_at[1], 
                              self.height)
        
        # double buffering
        dc.draw_drawable(gc, pixmap, 0, 0, 0, 0, w, h)
        
    
    def draw_mappings(self, dc, gc):
        upper_anchors = self.cyl_upper.get_anchors()
        lower_anchors = self.cyl_lower.get_anchors()
        
        # match them
        anchors = []
        for ancU in self.cyl_upper.get_anchors():
            for ancL in self.cyl_lower.get_anchors():
                if ancU[0] == ancL[0]:
                    anchors.append((ancU[1], ancL[1]))
                    break
        
        # draw lines
        back = gc.line_style
        gc.line_style = gtk.gdk.LINE_ON_OFF_DASH
        for pair in anchors:
            dc.draw_line(gc,
                         self.cyl_upper_drawn_at[0] + pair[0], #x1
                         self.cyl_upper_drawn_at[1] + self.height, #y1
                         self.cyl_lower_drawn_at[0] + pair[1], #x2
                         self.cyl_lower_drawn_at[1]) #y2
        gc.line_style = back
    

class CylinderGenerator:
    
    def __init__(self, pixmap_path, end_color):
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(pixmap_path)
        self.end_color = end_color
        
        
    def get_cyl(self, dc, width, height):
        
        y_radius = height / 2
        (ellipse_table, x_radius) = get_ellipse_table(y_radius)
        
        pixmap_width = width + x_radius
        scaled_pixbuf = self.pixbuf.scale_simple(pixmap_width, height, gtk.gdk.INTERP_BILINEAR)
        
        gc = dc.new_gc()
        colormap = dc.get_colormap()
        gc.foreground = colormap.alloc_color(0, 0, 0)
        
        pixmap = gtk.gdk.Pixmap(dc, pixmap_width, height)
        pixmap.draw_pixbuf(gc, scaled_pixbuf, 0, 0, 0, 0, -1, -1)
        
        for y in range(0, height):
            x_offset = ellipse_table[y]
            for x in range(0, x_offset):
                pixmap.draw_point(gc, x, y)
            for x in range(width + x_offset, pixmap_width):
                pixmap.draw_point(gc, x, y)
        
                
        # get pixbuf from pixmap in order to add alpha channel
        pixbuf = scaled_pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(), 0, 0, 0, 0, pixmap_width, height)
        
        # add alpha channel
        pixbuf = pixbuf.add_alpha(True, chr(0), chr(0), chr(0))
        
        return pixbuf
    
    def __get_pattern0(self, dc, width, height):
        y_radius = height / 2
        (ellipse_table, x_radius) = get_ellipse_table(y_radius)
        
        pixmap_width = width + x_radius
        scaled_pixbuf = self.pixbuf.scale_simple(pixmap_width, height, gtk.gdk.INTERP_BILINEAR)
        
        gc = dc.new_gc()
        colormap = dc.get_colormap()
        gc.foreground = colormap.alloc_color(0, 0, 0)
        
        pixmap = gtk.gdk.Pixmap(dc, pixmap_width, height)
        pixmap.draw_rectangle(gc, True, 0, 0, pixmap_width, height)
        
        # get pixbuf from pixmap in order to add alpha channel
        pixbuf = scaled_pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(), 0, 0, 0, 0, pixmap_width, height)
        
        # add alpha channel
        pixbuf = pixbuf.add_alpha(True, chr(0), chr(0), chr(0))
        
        return pixbuf
    
    def __get_pattern1(self, dc, width, height):
        y_radius = height / 2
        (ellipse_table, x_radius) = get_ellipse_table(y_radius)
        
        pixmap_width = width + x_radius
        scaled_pixbuf = self.pixbuf.scale_simple(pixmap_width, height, gtk.gdk.INTERP_BILINEAR)
        
        gc = dc.new_gc()
        colormap = dc.get_colormap()
        gc.foreground = colormap.alloc_color(0, 0, 0)
        
        pixmap = gtk.gdk.Pixmap(dc, pixmap_width, height)
        pixmap.draw_rectangle(gc, True, 0, 0, pixmap_width, height)
        
        gc.foreground = gtk.gdk.colormap_get_system().alloc_color("white", 1,1)
        for y in range(0, height, 2):
            x_offset = ellipse_table[y]
            for x in range(x_offset, x_offset + width):
                pixmap.draw_point(gc, x, y)
        
        # get pixbuf from pixmap in order to add alpha channel
        pixbuf = scaled_pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(), 0, 0, 0, 0, pixmap_width, height)
        
        # add alpha channel
        pixbuf = pixbuf.add_alpha(True, chr(0), chr(0), chr(0))
        
        return pixbuf
    
    def __get_pattern2(self, dc, width, height):
        y_radius = height / 2
        (ellipse_table, x_radius) = get_ellipse_table(y_radius)
        
        pixmap_width = width + x_radius
        scaled_pixbuf = self.pixbuf.scale_simple(pixmap_width, height, gtk.gdk.INTERP_BILINEAR)
        
        gc = dc.new_gc()
        colormap = dc.get_colormap()
        gc.foreground = colormap.alloc_color(0, 0, 0)
        
        pixmap = gtk.gdk.Pixmap(dc, pixmap_width, height)
        pixmap.draw_rectangle(gc, True, 0, 0, pixmap_width, height)
        
        gc.foreground = gtk.gdk.colormap_get_system().alloc_color("white", 1,1)
        for y in range(0, height, 5):
            x_offset = ellipse_table[y]
            for x in range(x_offset, x_offset + width):
                pixmap.draw_point(gc, x, y)
        
        # get pixbuf from pixmap in order to add alpha channel
        pixbuf = scaled_pixbuf.get_from_drawable(pixmap, pixmap.get_colormap(), 0, 0, 0, 0, pixmap_width, height)
        
        # add alpha channel
        pixbuf = pixbuf.add_alpha(True, chr(0), chr(0), chr(0))
        
        return pixbuf
    
    def get_pattern(self, pattern_id, dc, width, height):
        if pattern_id == 0:
            return self.__get_pattern0(dc, width, height)
        elif pattern_id == 1:
            return self.__get_pattern1(dc, width, height)
        elif pattern_id == 2:
            return self.__get_pattern2(dc, width, height)
        else:
            raise 'INVALID PATTERN ID'
    
    def draw_end(self, dc, gc, x, y, height):
        color_backup = gc.foreground
        gc.foreground = self.end_color
        
        ellipse_table, x_radius = get_ellipse_table(height / 2)
        
        #dc.draw_arc(gc, True, x - x_radius, y, 2 * x_radius, height, 5760, 11520)
        #dc.draw_arc(gc, True, x - x_radius, y, 2 * x_radius, height, 17280, 11520)
        
        # draw ellipse by hand
        for Y in range(0, height):
            x_offset = ellipse_table[Y]
            for X in range(x - x_offset, x + x_offset):
                dc.draw_point(gc, X, y + Y)
        
        gc.foreground = color_backup
        
        
        
        
        
# returns (ellipse_table, x_radius)
ellipses_table = {}
def get_ellipse_table(y_radius):
    global ellipses_table
    
    if ellipses_table.has_key(y_radius):
        return ellipses_table[y_radius]
    
    x_radius = y_radius / 2
    
    ellipse_table = {}
    split_point = y_radius - 0.5
    for y in range(y_radius, 0, -1):
        yy = y * y
        val1 = operator.div(yy, float(y_radius * y_radius))
        val2 = operator.sub(1.0, val1)
        x_squared = (float(x_radius * x_radius)) * val2
        x_offset_float = math.sqrt(operator.abs(x_squared))
        x_offset = int(math.ceil(x_offset_float))
        y_offset = operator.abs(y - y_radius)
        ellipse_table[y_offset] = x_offset
        
        
        ellipse_table[int(2*split_point) - y_offset] = x_offset
    
    pair = (ellipse_table, x_radius)
    ellipses_table[y_radius] = pair
    
    return pair