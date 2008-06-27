#!/usr/bin/python2

"""Entry point for system-config-lvm.

   This application wraps the LVM2 command line
   interface in a graphical user interface.

"""
__author__ = 'Jim Parsons (jparsons@redhat.com)'
 
import sys
import types
import select
import signal
import string
import os
from gtk import TRUE, FALSE

PROGNAME = "system-config-lvm"
VERSION = "@VERSION@"
INSTALLDIR="/usr/share/system-config-lvm"

### gettext ("_") must come before import gtk ###
import gettext
gettext.bindtextdomain(PROGNAME, "/usr/share/locale")
gettext.textdomain(PROGNAME)
try:
    gettext.install(PROGNAME, "/usr/share/locale", 1)
except IOError:
    import __builtin__
    __builtin__.__dict__['_'] = unicode
                                                                                

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
                                                                                
from renderer import volume_renderer
from lvm_model import lvm_model
from Volume_Tab_View import Volume_Tab_View
from lvmui_constants import *

import gnome
import gnome.ui

gnome.program_init (PROGNAME, VERSION)
gnome.app_version = VERSION
FORMALNAME=_("system-config-lvm")
ABOUT_VERSION=_("%s %s") % ('system-config-lvm',VERSION)
                                                                                
###############################################
class baselvm:
  def __init__(self, glade_xml, app):
 
    self.lvmm = lvm_model()
                                                                                
    self.main_win = app
    self.glade_xml = glade_xml

    self.volume_tab_view = Volume_Tab_View(glade_xml, self.lvmm, self.main_win)

    self.glade_xml.signal_autoconnect(
      {
        "on_quit1_activate" : self.quit,
        "on_about1_activate" : self.on_about
      }
    )
                                                                                
  def on_about(self, *args):
        dialog = gnome.ui.About(
            ABOUT_VERSION,
            '', ### Don't specify version - already in ABOUT_VERSION
            _("Copyright (c) 2004 Red Hat, Inc. All rights reserved."),
            _("This software is licensed under the terms of the GPL."),
            [ 'Jim Parsons (system-config-lvm) <jparsons at redhat.com>',
              'Alasdair Kergon (LVM2 Maintainer) <agk at redhat.com>',
              'Heinz Mauelshagen (LVM Maintainer) <mauelshagen at redhat.com>',
              '',
              'Kevin Anderson (Project Leader) <kanderso at redhat.com>'],
            [ 'Paul Kennedy <pkennedy at redhat.com>',
              'John Ha <jha at redhat.com>'], # doc people
        ) ### end dialog
        dialog.set_title (FORMALNAME)
        dialog.show()
                                                                                
                                                                                
                                                                                
  def quit(self, *args):
    gtk.main_quit()



#############################################################
def initGlade():
    gladepath = "lvui.glade"
    if not os.path.exists(gladepath):
      gladepath = "%s/%s" % (INSTALLDIR,gladepath)

    gtk.glade.bindtextdomain(PROGNAME)
    glade_xml = gtk.glade.XML (gladepath, domain=PROGNAME)
    return glade_xml
                                                                                
def runFullGUI():
    glade_xml = initGlade()
    app = glade_xml.get_widget('window1')
    blvm = baselvm(glade_xml, app)
    app.show()
    app.connect("destroy", lambda w: gtk.mainquit())
    gtk.main()
                                                                                
                                                                                
if __name__ == "__main__":
    cmdline = sys.argv[1:]
    sys.argv = sys.argv[:1]
                                                                                

    if os.getuid() != 0:
        print _("Please restart %s with root permissions!") % (sys.argv[0])
        sys.exit(10)

    runFullGUI()

