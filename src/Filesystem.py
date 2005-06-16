
from execute import execWithCapture, execWithCaptureErrorStatus, execWithCaptureStatus, execWithCaptureProgress, execWithCaptureErrorStatusProgress, execWithCaptureStatusProgress
from CommandError import *
from CommandHandler import FSCREATE_FAILURE

CREATING_FS=_("Please wait while filesystem is being created")
RESIZING_FS=_("Please wait while filesystem is being resized")
FSRESIZE_FAILURE=_("Resize of filesystem failed. Command attempted: \"%s\" - System Error Message: %s")


def get_fs(path):
    filesys_name = None
    result = execWithCapture("/usr/bin/file", ['/usr/bin/file', '-s', '-L', path])
    words = result.split()
    if len(words) < 3:  #No file system
        return NoFS()
    elif words[2].strip() == "rev":
        filesys_name = words[4]
    else:
        filesys_name = words[2]
    for fs in get_filesystems():
        if filesys_name == fs.name:
            return fs
    return Unknown(filesys_name)


def get_filesystems():
    return [NoFS(), ext3(), ext2()]


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
        o,e,r = execWithCaptureErrorStatusProgress("/sbin/mkfs", args, CREATING_FS)
        if r != 0:
            raise CommandError('FATAL', FSCREATE_FAILURE % (cmdstr,e))
    
    def extend_online(self, dev_path):
        args = list()
        args.append('/usr/sbin/ext2online')
        args.append(dev_path)
        cmdstr = ' '.join(args)
        o,e,r = execWithCaptureErrorStatusProgress('/usr/sbin/ext2online', args, RESIZING_FS)
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
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/e2fsck', args, RESIZING_FS)
        if not (r==0 or r==1):
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
        
        args = list()
        args.append('/sbin/resize2fs')
        args.append(dev_path)
        cmdstr = ' '.join(args)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/resize2fs', args, RESIZING_FS)
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
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/e2fsck', args, RESIZING_FS)
        if not (r==0 or r==1):
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
        
        new_size_kb = new_size_bytes / 1024
        args = list()
        args.append('/sbin/resize2fs')
        args.append(dev_path)
        args.append(str(new_size_kb) + 'K')
        cmdstr = ' '.join(args)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/resize2fs', args, RESIZING_FS)
        if r != 0:
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
        
        
class ext2(Filesystem):
    def __init__(self):
        Filesystem.__init__(self, 'ext2', True, True, True,
                            False, True, False, True)
        
    def create(self, path):
        args = list()
        args.append("/sbin/mkfs")
        args.append("-t")
        args.append('ext2')
        args.append(path)
        cmdstr = ' '.join(args)
        o,e,r = execWithCaptureErrorStatusProgress("/sbin/mkfs", args, CREATING_FS)
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
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/e2fsck', args, RESIZING_FS)
        if not (r==0 or r==1):
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
        
        args = list()
        args.append('/sbin/resize2fs')
        args.append(dev_path)
        cmdstr = ' '.join(args)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/resize2fs', args, RESIZING_FS)
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
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/e2fsck', args, RESIZING_FS)
        if not (r==0 or r==1):
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
        
        new_size_kb = new_size_bytes / 1024
        args = list()
        args.append('/sbin/resize2fs')
        args.append(dev_path)
        args.append(str(new_size_kb) + 'K')
        cmdstr = ' '.join(args)
        o,e,r = execWithCaptureErrorStatusProgress('/sbin/resize2fs', args, RESIZING_FS)
        if r != 0:
            raise CommandError('FATAL', FSRESIZE_FAILURE % (cmdstr,e))
