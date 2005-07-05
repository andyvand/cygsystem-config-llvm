
import gtk


class WaitMsg:
    
    def __init__(self, message):
        self.displayed = False
        self.msg = message
    
    def show(self):
        self.dlg = gtk.MessageDialog(None, 0,
                                     gtk.MESSAGE_INFO, gtk.BUTTONS_NONE, 
                                     self.msg)
        self.dlg.set_modal(True)
        self.dlg.show_now()
        self.displayed = True
        self.refresh()
        self.refresh()
        self.refresh()
    
    def hide(self):
        if self.displayed:
            self.dlg.destroy()
            self.displayed = False
        self.refresh()
    
    def refresh(self):
        while gtk.events_pending():
            gtk.main_iteration(False)
