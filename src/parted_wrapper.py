
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
            beg = self.__to_bytes(words[1]) / sectorSize
            end = self.__to_bytes(words[2]) / sectorSize - 1
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




    def __to_bytes(self, word):
        t = word.strip().lower()
        multiplier = 1024 * 1024
        if t.endswith('b'):
            t = t.rstrip('b')
            multiplier = 1
            if t.endswith('k'):
                t = t.rstrip('k')
                multiplier = 1024
            elif t.endswith('m'):
                t = t.rstrip('m')
                multiplier = 1024 * 1024
            elif t.endswith('g'):
                t = t.rstrip('g')
                multiplier = 1024 * 1024 * 1024
            elif t.endswith('t'):
                t = t.rstrip('t')
                multiplier = 1024 * 1024 * 1024 * 1024
        return int(float(t) * multiplier)
