AUTOMAKE_OPTIONS = foreign 1.7

#SUBDIRS = src po docs
SUBDIRS = src po

EXTRA_DIST = \
	system-config-lvm.spec			\
	system-config-lvm.console		\
	system-config-lvm.pam			\
	src/pixmaps/grad3.xpm			\
	src/pixmaps/UV.xpm			\
	src/pixmaps/LV.xpm			\
	src/pixmaps/PV.xpm			\
	src/pixmaps/VG.xpm			\
	intltool-extract.in			\
	intltool-merge.in			\
	intltool-update.in			\
	ChangeLog

CLEANFILES=$(applications_DATA)
DISTCLEANFILES=intltool-extract intltool-merge intltool-update
MAINTAINERCLEANFILES=ChangeLog

@INTLTOOL_DESKTOP_RULE@

.PHONY: changelog srpm

install-data-hook:
	$(mkinstalldirs) $(DESTDIR)$(sysconfdir)/security/console.apps
	$(mkinstalldirs) $(DESTDIR)$(sysconfdir)/pam.d
	$(mkinstalldirs) $(DESTDIR)$(prefix)/bin/
	$(INSTALL_DATA) $(srcdir)/system-config-lvm.console $(DESTDIR)$(sysconfdir)/security/console.apps/system-config-lvm
	$(INSTALL_DATA) $(srcdir)/system-config-lvm.pam $(DESTDIR)$(sysconfdir)/pam.d/system-config-lvm
#	$(INSTALL_DATA) $(srcdir)/src/pixmaps/UV.xpm $(DESTDIR)$(pkgdatadir)
#	$(INSTALL_DATA) $(srcdir)/src/pixmaps/LV.xpm $(DESTDIR)$(pkgdatadir)
#	$(INSTALL_DATA) $(srcdir)/src/pixmaps/PV.xpm $(DESTDIR)$(pkgdatadir)
#	$(INSTALL_DATA) $(srcdir)/src/pixmaps/VG.xpm $(DESTDIR)$(pkgdatadir)
#	$(INSTALL_DATA) $(srcdir)/src/pixmaps/grad3.xpm $(DESTDIR)$(pkgdatadir)
	ln -fs consolehelper $(DESTDIR)$(prefix)/bin/system-config-lvm

uninstall-local:
	rm -f $(DESTDIR)$(sysconfdir)/pam.d/system-config-lvm
	rm -f $(DESTDIR)$(prefix)/bin/system-config-lvm
#	rm -f $(DESTDIR)$(pkgdatadir)/LV.xpm
#	rm -f $(DESTDIR)$(pkgdatadir)/UV.xpm
#	rm -f $(DESTDIR)$(pkgdatadir)/VG.xpm
#	rm -f $(DESTDIR)$(pkgdatadir)/PV.xpm
#	rm -f $(DESTDIR)$(pkgdatadir)/grad3.xpm

changelog:
	rcs2log | sed -e 's|/usr/local/CVS/redhat-config-network/||g' \
		-e 's|@.*\.redhat\.com|@redhat.com|g' > ChangeLog

clean:
	rm -f *~

PKGNAME=${PACKAGE}
VERSION=@VERSION@
CVSTAG=r$(subst .,-,$(VERSION))

archive: distcheck changelog
	cvs ci -m "release $(VERSION)"
	cvs tag -cFR $(CVSTAG) .
	@rm -rf /tmp/${PKGNAME}-$(VERSION) /tmp/${PKGNAME}
	@CVSROOT=`cat CVS/Root`; cd /tmp; cvs -d $$CVSROOT export -r$(CVSTAG) ${PKGNAME}
	@cd /tmp/${PKGNAME};./autogen.sh
	@mv /tmp/${PKGNAME} /tmp/${PKGNAME}-$(VERSION)
	@dir=$$PWD; cd /tmp; tar cvzf $$dir/${PKGNAME}-$(VERSION).tar.gz ${PKGNAME}-$(VERSION)
	@chmod u+w -R /tmp/${PKGNAME}-$(VERSION)
#	@rm -rf /tmp/${PKGNAME}-$(VERSION)
	@echo "The archive is in ${PKGNAME}-$(VERSION).tar.gz"

srpm: archive
	rpmbuild --define "_sourcedir `pwd`" --define "_srcrpmdir `pwd`" --define "_specdir `pwd`" -ts @PACKAGE@-@VERSION@.tar.gz

srpm-test:
	rpmbuild --define "_sourcedir `pwd`" --define "_srcrpmdir `pwd`" --define "_specdir `pwd`" -ts @PACKAGE@-@VERSION@.tar.gz


