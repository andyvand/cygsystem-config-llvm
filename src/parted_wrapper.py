
import os, sys
import re
from execute import execWithCapture, execWithCaptureErrorStatus, execWithCaptureStatus, execWithCaptureProgress, execWithCaptureErrorStatusProgress, execWithCaptureStatusProgress

from Partition import *
from fdisk_wrapper import FDisk


PARTED='/sbin/parted'


class Parted:
    
    def getPartitions(self, devpath):
        sectorSize = FDisk().getDeviceGeometry(devpath)[1]
        parts = list()
        res = execWithCapture(PARTED, [PARTED, devpath, 'print', '-s'])
        lines = res.splitlines()
        for line in lines:
            if not re.match('^[0-9]', line):
                continue
            words = line.split()
            if len(words) < 3:
                continue
            # partition num
            part_num = int(words[0])
            # beg, end
            beg = int(float(words[1]) * 1024 * 1024) / sectorSize
            end = int(float(words[2]) * 1024 * 1024) / sectorSize - 1
            # bootable
            bootable = False
            for word in words:
                if 'boot' in word:
                    bootable = True
            # partition id
            id = ID_UNKNOWN
            if 'lvm' in words:
                id = ID_LINUX_LVM
            elif 'raid' in words:
                id = 253
            else:
                for word in words:
                    if 'swap' in word:
                        id = ID_SWAPS[0]
            
            part = Partition(beg, end, id, part_num, bootable, sectorSize)
            parts.append(part)
        
        return parts
    
    
    
    def savePartTable(self, devpath, parts):
        if len(self.getPartitions(devpath)) != 0:
            print 'partition table already exists'
            sys.exit(1)
        if len(parts) != 1:
            print 'parted save implementation is not complete'
            sys.exit(1)
        
        # create partition table
        print execWithCapture(PARTED, [PARTED, devpath, 'mklabel', 'gpt', '-s'])
        # create partition
        part = parts[0]
        beg = part.beg * part.sectorSize / 1024.0 / 1024 # parted uses Magabytes
        end = part.end * part.sectorSize / 1024.0 / 1024
        print beg, end
        print execWithCapture(PARTED, [PARTED, devpath, 'mkpart', 'primary', str(beg), str(end), '-s'])
        # add flags - if any
        if part.id == ID_LINUX_LVM:
            print execWithCapture(PARTED, [PARTED, devpath, 'set', str(part.num), 'lvm', 'on', '-s'])
