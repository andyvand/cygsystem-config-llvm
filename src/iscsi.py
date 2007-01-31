

import os, sys, copy
import re
from execute import execWithCaptureErrorStatus, execWithCaptureErrorStatusProgress
from socket import gethostbyname

import gtk, gtk.glade

from lvmui_constants import PROGNAME, INSTALLDIR


ISCSILS_PATH="/sbin/iscsi-ls"

CONFPATH = '/etc/iscsi.conf'

ISCSI_NAME = 'iscsi'
INITD_PATH = '/etc/init.d/'
CHKCONFIG_PATH = '/sbin/chkconfig'

ISCSI_INITD_PATH = INITD_PATH + ISCSI_NAME

RPM_PATH = '/bin/rpm'
INITIATOR_RPM_NAME = 'iscsi-initiator-utils'

SCSI_ID_PATH = '/sbin/scsi_id'

DEFAULT_ISCSI_PORT = 3260

NETCAT_PATH = '/usr/bin/nc'



def __get_targets_info_2(lines, infodir):
    if len(lines) <= 5:
        return
    if 'TARGET NAME' not in lines[0]:
        return
    
    info = {}
    info['LUNS'] = {}
    curr_lun = {}
    for line in lines:
        if '**************' in line:
            break
        idx = line.find(':')
        if idx < 1:
            continue
        key = line[:idx].strip()
        value = line[idx+1:].strip()
        if key == 'TARGET NAME':
            info['TARGET_NAME'] = value
        elif key == 'TARGET ALIAS':
            info['TARGET_ALIAS'] = value
        elif key == 'TARGET ADDRESS':
            address = value[:value.find(',')]
            idx = address.find(':')
            port = address[idx+1:]
            address = address[:idx]
            info['TARGET_ADDRESS'] = address
            info['TARGET_PORT'] = port
        elif key == 'HOST ID':
            info['HOST_ID'] = value
        elif key == 'SESSION STATUS':
            if 'ESTABLISHED' in value:
                value = True
            else:
                value = False
            info['ESTABLISHED'] = value
        elif key == 'LUN ID':
            curr_lun['LUN_ID'] = value
        elif key == 'Device':
            curr_lun['DEVICE'] = value
            l = value.strip().split('/')
            p = l[len(l)-1]
            args = [SCSI_ID_PATH, '-g', '-u', '-s', '/block/' + p]
            res, err, status = execWithCaptureErrorStatus(SCSI_ID_PATH, args)
            if status == 0:
                curr_lun['SCSI_ID'] = res.strip()
            else:
                curr_lun['SCSI_ID'] = ''
            info['LUNS'][curr_lun['LUN_ID']] = curr_lun
            curr_lun = {}
    if 'TARGET_NAME' in info:
        infodir[info['TARGET_NAME']] = info
    return
def get_targets_info():
    info = {}
    
    args = [ISCSILS_PATH, '-l']
    res, err, status = execWithCaptureErrorStatus(ISCSILS_PATH, args)
    if status:
        raise "iscsi error: " + err
    if 'driver is not loaded' in res:
        raise res
    
    lines = res.splitlines()
    i = 0
    for line in lines:
        i = i + 1
        if '**************' in line:
            __get_targets_info_2(lines[i:], info)
    return info

def get_hosts():
    CATPATH = '/bin/cat'
    args = [CATPATH, CONFPATH]
    res, err, status = execWithCaptureErrorStatus(CATPATH, args)
    if status:
        raise "missing " + CONFPATH
    
    hosts = []
    lines = res.splitlines()
    for line in lines:
        l = line.strip()
        if len(l) < 1:
            continue
        if l[0] == '#':
            continue
        idx = l.find('=')
        if idx < 1:
            continue
        key = l[:idx].strip()
        if key != 'DiscoveryAddress':
            continue
        host_port = l[idx+1:].strip()
        idx = host_port.find(':')
        if idx < 0:
            host = host_port
            port = str(DEFAULT_ISCSI_PORT)
        else:
            host = host_port[:idx]
            port = host_port[idx+1:]
        if len(host) != 0 and len(port) != 0:
            try:
                hosts.append([host, gethostbyname(host), port])
            except:
                hosts.append([host, '', port])
    return hosts

def add_host(hostname, port=DEFAULT_ISCSI_PORT):
    if len(hostname) == 0:
        raise 'missing hostname'
    port = str(int(port))
    ip = gethostbyname(hostname)
    
    hosts = get_hosts()
    for host in hosts:
        if host[2] == port:
            if host[0] == hostname or host[0] == ip or host[1] == hostname or host[1] == ip:
                # already present -> nothing to do
                return False
    
    f = open(CONFPATH, 'a')
    f.write('\nDiscoveryAddress=' + hostname + ':' + port + '\n')
    f.flush()
    f.close()
    
    return True # need to reload


def iscsi_start():
    if iscsi_running():
        return
    args = [ISCSI_INITD_PATH, 'start']
    res, err, status = execWithCaptureErrorStatusProgress(ISCSI_INITD_PATH, args, "Starting iSCSI subsystem...")
    if status:
        raise 'failed to start iscsi initiator'
    args = [CHKCONFIG_PATH, ISCSI_NAME, 'on']
    res, err, status = execWithCaptureErrorStatus(CHKCONFIG_PATH, args)


def iscsi_stop():
    args = [ISCSI_INITD_PATH, 'stop']
    res, err, status = execWithCaptureErrorStatus(ISCSI_INITD_PATH, args)
    if status:
        raise 'failed to stop iscsi initiator'
    args = [CHKCONFIG_PATH, ISCSI_NAME, 'off']
    res, err, status = execWithCaptureErrorStatus(CHKCONFIG_PATH, args)


def iscsi_reload():
    iscsi_start()
    args = [ISCSI_INITD_PATH, 'reload']
    res, err, status = execWithCaptureErrorStatus(ISCSI_INITD_PATH, args)
    if status:
        raise 'failed to reload iscsi initiator'


def iscsi_running():
    args = [ISCSI_INITD_PATH, 'status']
    res, err, status = execWithCaptureErrorStatus(ISCSI_INITD_PATH, args)
    return not status


def iscsi_installed():
    args = [RPM_PATH, '-q', INITIATOR_RPM_NAME]
    res, err, status = execWithCaptureErrorStatus(RPM_PATH, args)
    return not status




class ISCSI_INITIATOR:
    
    def __init__(self):
        gladepath = 'iscsi.glade'
        if not os.path.exists(gladepath):
            gladepath = "%s/%s" % (INSTALLDIR, gladepath)
        gtk.glade.bindtextdomain(PROGNAME)
        self.__glade_xml = gtk.glade.XML (gladepath, domain=PROGNAME)
        
        self.__modified = False
        pass
    
    # return True if anything changed 
    def run(self):
        self.__reload()
        
        win = self.__glade_xml.get_widget('iscsi_configuration')
        while True:
            resp = win.run()
            if resp == gtk.RESPONSE_APPLY:
                if self.__new_target():
                    self.__populate_form()
            elif resp == gtk.RESPONSE_HELP:
                self.__reload()
            elif resp == gtk.RESPONSE_CLOSE:
                break
            else:
                break
        win.hide()
        return True
    
    def __reload(self):
        hosts = get_hosts()
        
        self.__modified = True
        if iscsi_running():
            iscsi_reload()
        else:
            if len(hosts):
                iscsi_start()
            else:
                self.__modified = False
        self.__populate_form()
        return
    
    def __populate_form(self):
        hosts = get_hosts()
        targets = []
        try:
            targets = get_targets_info()
            
            # expand targets, so that each lun has its own row
            new_ts = []
            for t_name in targets:
                target = targets[t_name]
                if len(target['LUNS'].keys()) == 0:
                    new_t = copy.deepcopy(target)
                    del new_t['LUNS']
                    new_ts.append(new_t)
                else:
                    for lun_id in target['LUNS']:
                        lun = copy.deepcopy(target['LUNS'][lun_id])
                        new_t = copy.deepcopy(target)
                        for k in lun:
                            new_t[k] = lun[k]
                        del new_t['LUNS']
                        new_ts.append(new_t)
            targets = new_ts
        except:
            pass
        
        table = gtk.Table(len(targets) + 1, 6)
        table.set_row_spacings(3)
        table.set_col_spacings(10)
        
        # header
        table.attach(gtk.Label(''), 0, 1, 0, 1, gtk.FILL, 0)
        table.attach(gtk.Label('Path'), 1, 2, 0, 1, gtk.FILL, 0)
        table.attach(gtk.Label('Target Name'), 2, 3, 0, 1, gtk.FILL, 0)
        table.attach(gtk.Label('Lun'), 3, 4, 0, 1, gtk.FILL, 0)
        table.attach(gtk.Label('Hostname'), 4, 5, 0, 1, gtk.FILL, 0)
        table.attach(gtk.Label('SCSI ID'), 5, 6, 0, 1, gtk.FILL, 0)
        
        # entries
        row = 1
        for target in targets:
            connected = target['ESTABLISHED']
            
            active = gtk.CheckButton()
            active.set_active(connected)
            active.set_sensitive(False)
            name = gtk.Label(str(target['TARGET_NAME']))
            if connected:
                path = gtk.Label(str(target['DEVICE']))
                scsi_id = gtk.Label(str(target['SCSI_ID']))
                lun = gtk.Label(str(target['LUN_ID']))
            else:
                path = gtk.Label('')
                scsi_id = gtk.Label('')
                lun = gtk.Label('')
            hostname = target['TARGET_ADDRESS']
            port = target['TARGET_PORT']
            for h in hosts:
                if h[1] == hostname:
                    hostname = h[0]
            if str(port) == str(DEFAULT_ISCSI_PORT):
                hostname = gtk.Label(str(hostname))
            else:
                hostname = gtk.Label(str(hostname) + ':' + str(port))
            
            table.attach(active, 0, 1, row, row+1, gtk.FILL, 0)
            table.attach(path, 1, 2, row, row+1, gtk.FILL, 0)
            table.attach(name, 2, 3, row, row+1, gtk.FILL, 0)
            table.attach(lun, 3, 4, row, row+1, gtk.FILL, 0)
            table.attach(hostname, 4, 5, row, row+1, gtk.FILL, 0)
            table.attach(scsi_id, 5, 6, row, row+1, gtk.FILL, 0)
            
            row += 1
        
        insert_here = self.__glade_xml.get_widget('iscsi_configuration_viewport')
        insert_here.remove(insert_here.get_child())
        insert_here.add(table)
        insert_here.resize_children()
        insert_here.show_all()
        
        pass
    
    
    def __new_target(self):
        hostname_entry = self.__glade_xml.get_widget('new_target_hostname')
        hostname_entry.set_text('')
        hostname_entry.grab_focus()
        
        port_entry = self.__glade_xml.get_widget('new_target_port')
        port_entry.set_text(str(DEFAULT_ISCSI_PORT))
        
        win = self.__glade_xml.get_widget('new_target_dlg')
        ret = True
        while True:
            resp = win.run()
            if resp == gtk.RESPONSE_OK:
                hostname = hostname_entry.get_text()
                port = port_entry.get_text()
                
                # validate input
                if len(hostname) == 0:
                    self.__errorMessage("Missing hostname")
                    hostname_entry.grab_focus()
                    continue
                if len(port) == 0:
                    self.__errorMessage("Missing port")
                    port_entry.grab_focus()
                    continue
                try:
                    i = int(port)
                    if i < 1 or i > 65535:
                        raise 'port out of range'
                except:
                    self.__errorMessage("Port has to be an integer value in range 1-65535")
                    port_entry.grab_focus()
                    continue
                
                # try to contact target
                args = [NETCAT_PATH, '-z', hostname, port]
                res, err, status = execWithCaptureErrorStatus(NETCAT_PATH, args)
                if status:
                    self.__errorMessage("Unable to contact port %s on %s. \nMake sure iSCSI target is present there, and try again." % (port, hostname))
                    hostname_entry.grab_focus()
                    continue
                
                # add target to conf file and reload iscsi
                ret = add_host(hostname, port)
                if ret:
                    iscsi_reload()
                
                break
            else:
                ret = False
                break
        win.hide()
        self.__modified = self.__modified or ret
        return ret
    
    
    def __errorMessage(self, message):
        dlg = gtk.MessageDialog(None, 0,
                                gtk.MESSAGE_ERROR,
                                gtk.BUTTONS_OK,
                                message)
        dlg.show_all()
        rc = dlg.run()
        dlg.destroy()
        return rc
    


if __name__ == "__main__":
    
    conf = ISCSI_INITIATOR()
    conf.run()
    
    print 'installed: ', iscsi_installed()
    print 'running: ', iscsi_running()
    print 'hosts: ', get_hosts()
    print 'targets info: ', get_targets_info()
    
    
    pass










