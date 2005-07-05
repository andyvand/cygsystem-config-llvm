
import os

from execute import execWithCapture, execWithCaptureErrorStatus, execWithCaptureStatus, execWithCaptureProgress, execWithCaptureErrorStatusProgress, execWithCaptureStatusProgress


MULTIPATH_BIN='/sbin/multipath'
DMSETUP_BIN='/sbin/dmsetup'
LS_BIN='/bin/ls'

DMSETUP_FAILURE=_("dmsetup command failed. Command attempted: \"%s\" - System Error Message: %s")
LS_FAILURE=_("ls command failed. Command attempted: \"%s\" - System Error Message: %s")


class Multipath:
    
    def __init__(self):
        pass
    
    
    def get_multipath_data(self):
        #return self.get_multipath_data()
        
        # for testing purposes, return arbitrary values
        d = {}
        d['/dev/test_multipath'] = ['/dev/hda', '/dev/hde'] #, '/dev/hdb', '/dev/hdm']
        #d['/dev/mapper/testmultipath_2'] = ['/dev/sda', '/dev/sdb']
        return d
    
    # {multipath_access_path:[dev1, dev2, ...], ... }
    def get_multipath_data_2(self):
        multipath_data = {}
        
        dmsetup_lines = None
        if os.access(DMSETUP_BIN, os.F_OK):
            args = list()
            args.append(DMSETUP_BIN)
            args.append('table')
            cmdstr = ' '.join(args)
            o,e,r = execWithCaptureErrorStatus(DMSETUP_BIN, args)
            if r != 0:
                raise CommandError('FATAL', DMSETUP_FAILURE % (cmdstr, e))
            dmtable_lines = o.splitlines()
        else:
            return multipath_data
        
        args = list()
        args.append(LS_BIN)
        args.append('-l')
        args.append('/dev/')
        cmdstr = ' '.join(args)
        o,e,r = execWithCaptureErrorStatus(LS_BIN, args)
        if r != 0:
            raise CommandError('FATAL', LS_FAILURE % (cmdstr, e))
        ls_lines = o.splitlines()
        
        # get block devices
        block_devices = []
        for line in ls_lines:
            words = line.split()
            if len(words) == 0:
                continue
            if words[0][0] == 'b':
                # [name, major, minor]
                block_devices.append(['/dev/' + words[9], words[4].rstrip(','), words[5]])
        
        # process dmsetup table
        for line in dmtable_lines:
            if len(line) == 0:
                continue
            words = line.split()
            
            if 'multipath' not in words:
                continue
            
            origin = '/dev/mapper/' + words[0].rstrip(':')
            devices = []
            for word in words[1:]:
                if ':' in word:
                    idx = word.find(':')
                    major = word[:idx]
                    minor = word[idx+1:]
                    for bd in block_devices:
                        if bd[1] == major and bd[2] == minor:
                            devices.append(bd[0])
            if len(devices) == 0:
                print 'multipath error: ' + origin + str(devices)
                continue
            
            multipath_data[origin] = devices
        
        return multipath_data
