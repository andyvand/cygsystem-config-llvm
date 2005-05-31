PYTHON_FILES = ExtentSegment.py \
InputController.py \
CommandHandler.py  \
CommandError.py  \
LogicalVolume.py \
lvm_model.py \
lvmui_constants.py \
PhysicalExtent.py \
PhysicalVolume.py \
Properties_Renderer.py \
renderer.py \
ViewableExtent.py \
ViewableVolume.py \
VolumeGroup.py \
Volume.py \
Volume_Tab_View.py \
fdisk_wrapper.py \
FDiskModel.py \
execute.py	\
pixmaps/UV.xpm	\
pixmaps/VG.xpm	\
pixmaps/LV.xpm	\
pixmaps/PV.xpm	\
pixmaps/grad3.xpm	\
pixmaps/lv_icon.png	\
system-config-lvm.py

GLADE_FILES = lvui.glade

EXTRA_DIST = $(PYTHON_FILES) $(GLADE_FILES)

execdir = $(sbindir)

all-local: 
	rm -f system-config-lvm
	ln -s system-config-lvm.py system-config-lvm

gladedir = $(pkgdatadir)
glade_DATA = $(GLADE_FILES)

install-exec-local:
	mkdir -p $(DESTDIR)$(sbindir) $(DESTDIR)$(bindir) $(DESTDIR)$(pkgdatadir) $(DESTDIR)$(pkgdatadir)/pixmaps/
	sed -e 's/\@VERSION\@/@VERSION@/g' $(srcdir)/system-config-lvm.py > $(DESTDIR)$(pkgdatadir)/system-config-lvm.py
	chmod 755 $(DESTDIR)$(pkgdatadir)/system-config-lvm.py
	install -m 0640 $(srcdir)/ExtentSegment.py $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/InputController.py $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/CommandHandler.py $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/CommandError.py $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/LogicalVolume.py $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/lvm_model.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/lvmui_constants.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/PhysicalExtent.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/PhysicalVolume.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/Properties_Renderer.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/renderer.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/ViewableExtent.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/ViewableVolume.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/VolumeGroup.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/Volume.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/Volume_Tab_View.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/fdisk_wrapper.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/FDiskModel.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/execute.py  $(DESTDIR)$(pkgdatadir)/
	install -m 0640 $(srcdir)/pixmaps/PV.xpm  $(DESTDIR)$(pkgdatadir)/pixmaps/
	install -m 0640 $(srcdir)/pixmaps/LV.xpm  $(DESTDIR)$(pkgdatadir)/pixmaps/
	install -m 0640 $(srcdir)/pixmaps/UV.xpm  $(DESTDIR)$(pkgdatadir)/pixmaps/
	install -m 0640 $(srcdir)/pixmaps/VG.xpm  $(DESTDIR)$(pkgdatadir)/pixmaps/
	install -m 0640 $(srcdir)/pixmaps/grad3.xpm  $(DESTDIR)$(pkgdatadir)/pixmaps/
	install -m 0644 $(srcdir)/pixmaps/lv_icon.png  $(DESTDIR)$(pkgdatadir)/pixmaps/
	softdir=$(pkgdatadir); \
	p=$(DESTDIR) ; \
	softdir=$${softdir/#$$p} ; \
	p=$(prefix) ; \
	softdir=$${softdir/#$$p} ; \
	softdir=$${softdir/#\/} ; \
	ln  -fs ../$${softdir}/system-config-lvm.py $(DESTDIR)$(sbindir)/system-config-lvm;

uninstall-local:
	rm -fr $(DESTDIR)$(pkgdatadir)
	rm -f  $(DESTDIR)$(sbindir)/system-config-lvm

docs:
	cd $(srcdir)
	python @PYDOC@ -w $(PYTHON_FILES)
	mv *.html doc

pycheck:
	pychecker -F $(top_srcdir)/pycheckrc $(PYTHON_FILES)

clean:
	rm -f *.pyo *.pyc
	rm -f ${BUILT_SOURCES}
