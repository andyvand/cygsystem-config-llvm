
import re
import os

from execute import execWithCapture, execWithCaptureErrorStatus, execWithCaptureStatus, execWithCaptureProgress, execWithCaptureErrorStatusProgress, execWithCaptureStatusProgress
from CommandError import *


CREATING_FS=_("Creating %s filesystem")
RESIZING_FS=_("Resizing %s filesystem")
CHECKING_FS=_("Checking %s filesystem")
UPGRADING_FS=_("Upgrading %s filesystem to %s")
FSCREATE_FAILURE=_("Creation of filesystem failed. Command attempted: \"%s\" - System Error Message: %s")
FSRESIZE_FAILURE=_("Resize of filesystem failed. Command attempted: \"%s\" - System Error Message: %s")
FSCHECK_FAILURE=_("Check of filesystem failed. Command attempted: \"%s\" - System Error Message: %s")
FSUPGRADE_FAILURE=_("Upgrade of filesystem failed. Command attempted: \"%s\" - System Error Message: %s")



def get_fs(path):
    filesys_name = None
    result = execWithCapture("/usr/bin/file", ['/usr/bin/file', '-s', '-L', path])
    
    if re.search('ext3', result, re.I):
        return ext3()
    elif re.search('ext2', result, re.I):
        return ext2()
    elif re.search('FAT \(12 bit\)', result, re.I):
        return Unknown('vfat12')
    elif re.search('FAT \(16 bit\)', result, re.I):
        return Unknown('vfat16')
    elif re.search('FAT \(32 bit\)', result, re.I):
        return Unknown('vfat32')
    elif re.search('minix', result, re.I):
        return Unknown('minix')
    elif re.search('xfs', result, re.I):
        return Unknown('xfs')
    elif re.search('jfs', result, re.I):
        return Unknown('jfs')
    elif re.search('raiserfs', result, re.I):
        return Unknown('raiserfs')
    elif re.search('swap', result, re.I):
        filesys = Unknown('swap')
        filesys.mountable = False
        return filesys
    else:
        # check if GFS
        if os.access('/sbin/gfs_tool', os.F_OK):
            args = ['/sbin/gfs_tool']
            args.append('sb')
            args.append(path)
            args.append('proto')
            cmdstr = ' '.join(args)
            o,e,r = execWithCaptureErrorStatus('/sbin/gfs_tool', args)
            if r == 0:
                if 'lock_nolock' in o:
                    return gfs_local()
                elif 'lock_dlm' in o or 'lock_gulm' in o:
                    return gfs_clustered()
        
        return NoFS()
    

def get_filesystems():
    fss = [NoFS()] # NoFS has to be first
    
    if os.access('/sbin/mkfs.ext2', os.F_OK):
        fss.append(ext2())
    if os.access('/sbin/mkfs.ext3', os.F_OK):
        fss.append(ext3())
    if os.access('/sbin/gfs_mkfs', os.F_OK):
        fss.append(gfs_local())
    
    return fss


class Filesystem:
    def __init__(self, name, creatable, editable, mountable,
                 extendable_online, extendable_offline,
                 reducible_online, reducible_offline):
        self.name = name
        self.creatable = creatable
        self.editable = editable
        self.mountable = mountable
        
        self.extendable_online = extendable_online
        self.extendable_offline = extendable_offline
        self.reducible_online = reducible_online
        self.reducible_offline = reducible_offline
        
        self.upgradable = False
        
    
    def create(self, path):
        pass
    
    def extend_online(self, dev_path):
        pass
    
    def extend_offline(self, dev_path):
        pass
    
    def reduce_online(self, dev_path, new_size_bytes):
        pass
    
    def reduce_offline(self, dev_path, new_size_bytes):
        pass
    
    def set_options(self, devpath):
        pass
    def change_options(self, devpath):
        pass
    
    def get_label(self, devpath):
        return None
    

class NoFS(Filesystem):
    def __init__(self):
        Filesystem.__init__(self, _('None'), True, False, False, 
                            False, True, False, True)
        
        
class Unknown(Filesystem):
    def __init__(self, name = _('Unknown filesystem')):
        Filesystem.__init__(self, name, False, False, True,
                            False, False, False, False)
        
        
class ext3(Filesystem):
    def __init__(self):
        Filesystem.__init__(self, 'ext3', True, True, True,
                            True, True, False, True)
        
    def create(self, path):
        args = list()
        args.append("/sbin/mkfs")
        args.append("-t")
        args.append('ext3')
        args.append(path)
        cmdstr = ' '.join(args)
        msg = CREATING_FS % (self.name)
        o,e,r = execWithCaptureErrorStatusProgress("/sbin/mkfs", args, msg)
        if r != 0:
            raise CommandError('FATAL', FSCREATE_FAILURE % (cmdstr,e))
    
    def extend_online(self, dev_path):
        args = list()
        args.append('/usr/sbin/ext2online')
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = RESIZING_FS % (self.name)
        o,e,r = execWithCaptureErrorStatusProgress('/usr/sbin/ext2online', args, msg)
        if r != 0:
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
    
    def reduce_online(self, dev_path, new_size_bytes):
        # not supported
        raise 'NOT supported'
    
    def extend_offline(self, dev_path):
        # first check fs (resize2fs requirement)
        args = list()
        args.append('/sbin/e2fsck')
        args.append('-f')
        args.append('-p') # repair fs
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = CHECKING_FS % self.name
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/e2fsck', args, msg)
        if not (r==0 or r==1):
            raise CommandError('FATAL', FSCHECK_FAILURE % (cmdstr,e))
        
        args = list()
        args.append('/sbin/resize2fs')
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = RESIZING_FS % self.name
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/resize2fs', args, msg)
        if r != 0:
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
        
    def reduce_offline(self, dev_path, new_size_bytes):
        # first check fs (resize2fs requirement)
        args = list()
        args.append('/sbin/e2fsck')
        args.append('-f')
        args.append('-p') # repair fs
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = CHECKING_FS % self.name
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/e2fsck', args, msg)
        if not (r==0 or r==1):
            raise CommandError('FATAL', FSCHECK_FAILURE % (cmdstr,e))
        
        new_size_kb = new_size_bytes / 1024
        args = list()
        args.append('/sbin/resize2fs')
        args.append(dev_path)
        args.append(str(new_size_kb) + 'K')
        cmdstr = ' '.join(args)
        msg = RESIZING_FS % (self.name)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/resize2fs', args, msg)
        if r != 0:
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
    
    def get_label(self, devpath):
        args = ['/sbin/tune2fs']
        args.append('-l')
        args.append(devpath)
        o, r = execWithCaptureStatus('/sbin/tune2fs', args)
        if r == 0:
            lines = o.splitlines()
            for line in lines:
                if re.search('volume name', line, re.I):
                    words = line.split()
                    label = words[len(words) - 1]
                    if re.match('<none>', label, re.I):
                        return None
                    else:
                        return label
        return None
    

class ext2(Filesystem):
    def __init__(self):
        Filesystem.__init__(self, 'ext2', True, True, True, 
                            False, True, False, True)
        self.upgradable = True
        
    
    def create(self, path):
        args = list()
        args.append("/sbin/mkfs")
        args.append("-t")
        args.append('ext2')
        args.append(path)
        cmdstr = ' '.join(args)
        msg = CREATING_FS % (self.name)
        o,e,r = execWithCaptureErrorStatusProgress("/sbin/mkfs", args, msg)
        if r != 0:
            raise CommandError('FATAL', FSCREATE_FAILURE % (cmdstr,e))
    
    def extend_online(self, dev_path):
        # not supported
        raise 'NOT supported'
    
    def reduce_online(self, dev_path, new_size_bytes):
        # not supported
        raise 'NOT supported'
    
    def extend_offline(self, dev_path):
        # first check fs (resize2fs requirement)
        args = list()
        args.append('/sbin/e2fsck')
        args.append('-f')
        args.append('-p') # repair fs
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = CHECKING_FS % self.name
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/e2fsck', args, msg)
        if not (r==0 or r==1):
            raise CommandError('FATAL', FSCHECK_FAILURE % (cmdstr,e))
        
        args = list()
        args.append('/sbin/resize2fs')
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = RESIZING_FS % (self.name)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/resize2fs', args, msg)
        if r != 0:
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
        
    def reduce_offline(self, dev_path, new_size_bytes):
        # first check fs (resize2fs requirement)
        args = list()
        args.append('/sbin/e2fsck')
        args.append('-f')
        args.append('-p') # repair fs
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = CHECKING_FS % self.name
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/e2fsck', args, msg)
        if not (r==0 or r==1):
            raise CommandError('FATAL', FSCHECK_FAILURE % (cmdstr,e))
        
        new_size_kb = new_size_bytes / 1024
        args = list()
        args.append('/sbin/resize2fs')
        args.append(dev_path)
        args.append(str(new_size_kb) + 'K')
        cmdstr = ' '.join(args)
        msg = RESIZING_FS % (self.name)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/resize2fs', args, msg)
        if r != 0:
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
    
    def upgrade(self, dev_path):
        args = ['/sbin/tune2fs']
        args.append('-j')
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = UPGRADING_FS % (self.name, ext3().name)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/tune2fs', args, msg)
        if r != 0:
            raise CommandError('FATAL', FSUPGRADE_FAILURE % (cmdstr,e))
    
    def get_label(self, devpath):
        args = ['/sbin/tune2fs']
        args.append('-l')
        args.append(devpath)
        o, r = execWithCaptureStatus('/sbin/tune2fs', args)
        if r == 0:
            lines = o.splitlines()
            for line in lines:
                if re.search('volume name', line, re.I):
                    words = line.split()
                    label = words[len(words) - 1]
                    if re.match('<none>', label, re.I):
                        return None
                    else:
                        return label
        return None
    

class gfs_local(Filesystem):
    def __init__(self):
        mountable = False
        # check if mountable
        args = list()
        args.append('/bin/cat')
        args.append('/proc/filesystems')
        cmdstr = ' '.join(args)
        out = execWithCapture('/bin/cat', args)
        if re.search('gfs', out, re.I):
            mountable = True
        Filesystem.__init__(self, _("GFS (local)"), True, False, mountable, 
                            True, False, False, False)
        
    
    def create(self, path):
        MKFS_GFS_BIN='/sbin/gfs_mkfs'
        args = [MKFS_GFS_BIN]
        args.append('-j')
        args.append('1')
        args.append('-p')
        args.append('lock_nolock')
        args.append('-O')
        args.append(path)
        cmdstr = ' '.join(args)
        msg = CREATING_FS % (self.name)
        o,e,r = execWithCaptureErrorStatusProgress(MKFS_GFS_BIN, args, msg)
        if r != 0:
            raise CommandError('FATAL', FSCREATE_FAILURE % (cmdstr,e))
    
    def extend_online(self, dev_path):
        args = ['/sbin/gfs_grow']
        args.append(dev_path)
        cmdstr = ' '.join(args)
        msg = RESIZING_FS % (self.name)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/gfs_grow', args, msg)
        if r != 0:
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
    

class gfs_clustered(Filesystem):
    def __init__(self):
        mountable = False
        # check if mountable
        args = list()
        args.append('/bin/cat')
        args.append('/proc/filesystems')
        cmdstr = ' '.join(args)
        out = execWithCapture('/bin/cat', args)
        if re.search('gfs', out, re.I):
            mountable = True
        Filesystem.__init__(self, _("GFS (clustered)"), False, False, mountable, 
                            False, False, False, False)
        
    
