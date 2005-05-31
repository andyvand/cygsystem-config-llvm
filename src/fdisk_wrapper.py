
import os, sys
from execute import execWithCapture, execWithCaptureErrorStatus, execWithCaptureStatus
import re
import copy

SFDISK='/sbin/sfdisk'
FDISK='/sbin/fdisk'
BASH='/bin/bash'

ID_EMPTY = -1
ID_EXTENDS = [0x5, 0x85]
ID_SWAPS = [0x82]
ID_LINUX_LVM = 0x8e

PARTITION_IDs = { -1 : 'NONE',
                  0 : 'Empty',
                  1 : 'FAT12',
                  2 : 'XENIX root',
                  3 : 'XENIX usr',
                  4 : 'FAT16 <32M',
                  5 : 'Extended',
                  6 : 'FAT16',
                  7 : 'HPFS/NTFS',
                  8 : 'AIX',
                  9 : 'AIX bootable',
                  10 : 'OS/2 Boot Manager',
                  11 : 'W95 FAT32',
                  12 : 'W95 FAT32 (LBA)',
                  14 : 'W95 FAT16 (LBA)',
                  15 : 'W95 Ext\'d (LBA)',
                  16 : 'OPUS',
                  17 : 'Hidden FAT12',
                  18 : 'Compaq diagnostics',
                  20 : 'Hidden FAT16 <32M',
                  22 : 'Hidden FAT16',
                  23 : 'Hidden HPFS/NTFS',
                  24 : 'AST SmartSleep',
                  27 : 'Hidden W95 FAT32',
                  28 : 'Hidden W95 FAT32 (LBA)',
                  30 : 'Hidden W95 FAT16 (LBA)',
                  36 : 'NEC DOS',
                  57 : 'Plan 9',
                  60 : 'PartitionMagic recovery',
                  64 : 'Venix 80286',
                  65 : 'PPC PReP Boot',
                  66 : 'SFS',
                  77 : 'QNX4.x',
                  78 : 'QNX4.x 2nd part',
                  79 : 'QNX4.x 3rd part',
                  80 : 'OnTrack DM',
                  81 : 'OnTrack DM6 Aux1',
                  82 : 'CP/M',
                  83 : 'OnTrack DM6 Aux3',
                  84 : 'OnTrackDM6',
                  85 : 'EZ-Drive',
                  86 : 'Golden Bow',
                  92 : 'Priam Edisk',
                  97 : 'SpeedStor',
                  99 : 'GNU HURD or SysV',
                  100 : 'Novell Netware 286',
                  101 : 'Novell Netware 386',
                  112 : 'DiskSecure Multi-Boot',
                  117 : 'PC/IX',
                  128 : 'Old Minix',
                  129 : 'Minix / old Linux',
                  130 : 'Linux swap',
                  131 : 'Linux',
                  132 : 'OS/2 hidden C: drive',
                  133 : 'Linux extended',
                  134 : 'NTFS volume set',
                  135 : 'NTFS volume set',
                  142 : 'Linux LVM',
                  147 : 'Amoeba',
                  148 : 'Amoeba BBT',
                  159 : 'BSD/OS',
                  160 : 'IBM Thinkpad hibernation',
                  165 : 'FreeBSD',
                  166 : 'OpenBSD',
                  167 : 'NeXTSTEP',
                  168 : 'Darwin UFS',
                  169 : 'NetBSD',
                  171 : 'Darwin boot',
                  183 : 'BSDI fs',
                  184 : 'BSDI swap',
                  187 : 'Boot Wizard hidden',
                  190 : 'Solaris boot',
                  193 : 'DRDOS/sec (FAT-12)',
                  196 : 'DRDOS/sec (FAT-16 < 32M)',
                  198 : 'DRDOS/sec (FAT-16)',
                  199 : 'Syrinx',
                  218 : 'Non-FS data',
                  219 : 'CP/M / CTOS / ...',
                  222 : 'Dell Utility',
                  223 : 'BootIt',
                  225 : 'DOS access',
                  227 : 'DOS R/O',
                  228 : 'SpeedStor',
                  235 : 'BeOS fs',
                  238 : 'EFI GPT',
                  239 : 'EFI (FAT-12/16/32)',
                  240 : 'Linux/PA-RISC boot',
                  241 : 'SpeedStor',
                  244 : 'SpeedStor',
                  242 : 'DOS secondary',
                  253 : 'Linux raid autodetect',
                  254 : 'LANstep',
                  255 : 'BBT'}
# fill out gaps in PARTITION_IDs
for i in range(256):
    if i not in PARTITION_IDs:
        PARTITION_IDs[i] = _("Unknown")
    
TMP_FILE='/tmp/one_extremely_long_name_hoping_nobody_is_gona_use_it'


# all size values are in sectors


class FDiskErr:
    pass
class FDiskErr_occupied(FDiskErr):
    pass
class FDiskErr_cannotFit(FDiskErr):
    pass
class FDiskErr_extended(FDiskErr):
    pass
class FDiskErr_extendedNumsMissing(FDiskErr):
    pass
class FDiskErr_num(FDiskErr):
    pass
class FDiskErr_partFormat(FDiskErr):
    pass


class Segment:
    def __init__(self, beg, end, sectorSize):
        self.children = list()
        self.beg = beg
        self.end = end
        self.sectorSize = sectorSize # bytes
        self.id = ID_EMPTY
        self.wholeDevice = False # occupies whole drive?
    def getSize(self):
        return self.end + 1 - self.beg
    def getSizeBytes(self):
        return self.getSize() * self.sectorSize
    def printout(self):
        print ' ', ' ', str(self.beg), str(self.end), str(self.id), str(self.getSize()), str(self.getSizeBytes())
    
class Partition(Segment):
    def __init__(self, beg, end, id, num, bootable, sectorSize):
        Segment.__init__(self, beg, end, sectorSize)
        self.id = id
        self.num = num
        self.bootable = bootable
    def printout(self):
        self.__printout(self)
    def __printout(self, seg):
        if seg.bootable:
            b = 'b'
        else:
            b = ' '
        print str(seg.num), b, str(seg.beg), str(seg.end), str(seg.id), str(seg.getSize()), str(self.getSizeBytes())
        for child in seg.children:
            child.printout()
        
        
## all parsing is done at FDisk ##
class FDisk:

    def getDeviceNames(self):
        res = execWithCapture(SFDISK, [SFDISK, '-s'])
        lines = res.splitlines()
        devices = list()
        for line in lines:
            if not re.match('^/dev/', line):
                continue
            words = line.split(':')
            devname = words[0].strip()
            if not re.match('.*[0-9]', devname):
                # check if partition table is OK       
                # out, err, ret = rhpl.executil.execWithCaptureErrorStatus(SFDISK, [SFDISK, '-V', devname])
                out, ret = execWithCaptureStatus(SFDISK, [SFDISK, '-V', devname])
                if ret != 0:
                    print 'THERE IS A PROBLEM WITH PARTITION TABLE at device ' + devname
                    # print err
                devices.append(devname)
        # check if geometry can be detected
        for dev in devices[:]:
            res = execWithCapture(SFDISK, [SFDISK, '-s', dev])
            if re.match('.*cannot get geometry.*', res):
                devices.remove(dev)
        return devices
    
    
    # returns [sectors, sectorSize, cylinders,  sectorsPerTrack, sectorsPerCylinder]
    def getDeviceGeometry(self, devname):
        sectors = None
        sectorSize = None
        spt = None
        spc = None
        cyls = None
        res = execWithCapture(FDISK, [FDISK, '-l', '-u', devname])
        lines = res.splitlines()
        for line in lines:
            if re.match('^Units = sectors .* [0-9]* bytes', line):
                words = line.split()
                if (words[len(words) - 1] == 'bytes'):
                    sectorSize = int(words[len(words) - 2])
                else:
                    print 'bad fdisk output for device ' + devname
                    sys.exit()
            elif re.match('.* [0-9]* sectors/track, [0-9]* cylinders, total [0-9]* sectors', line):
                words = line.split()
                if (words[len(words) - 1] == 'sectors') and (words[len(words) - 3] == 'total'):
                    sectors = int(words[len(words) - 2])
                else:
                    print 'bad fdisk output for device ' + devname
                    sys.exit()
                if words[3].rstrip(',') == 'sectors/track':
                    spt = int(words[2])
                else:
                    print 'bad fdisk output for device ' + devname
                    sys.exit()
                if words[5].rstrip(',') == 'cylinders':
                    cyls = int(words[4])
                else:
                    print 'bad fdisk output for device ' + devname
                    sys.exit()
        if sectors == None or sectorSize == None or spt == None or cyls == None:
            print 'bad fdisk output for device ' + devname
            sys.exit()
        return [sectors, sectorSize, cyls, spt, sectors/cyls]
    
    
    def getPartitions(self, devname):
        sectorSize = self.getDeviceGeometry(devname)[1]
        parts = list()
        res = execWithCapture(SFDISK, [SFDISK, '-l', '-uS', devname])
        lines = res.splitlines()
        for line in lines:
            if not re.match('^/dev/', line):
                continue
            words = line.split()
            # partition num
            tmp = words[0].strip()
            part_num = int(tmp[len(devname):])
            del(words[0])
            # bootable
            if words[0] == '*':
                bootable = True
                del(words[0])
            else:
                bootable = False
            beg, end, ignore, id = words[:4]
            # beg
            if beg == '-':
                continue
            else:
                beg = int(beg)
            #end
            if end == '-':
                continue
            else:
                end = int(end)
            # partition id
            id = int(id, 16)
            part = Partition(beg, end, id, part_num, bootable, sectorSize)
            parts.append(part)
        return parts
    
    
    def savePartTable(self, devname, parts):
        new_parts = []
        for part in parts:
            if part.id != ID_EMPTY:
                new_parts.append(part)
                if part.id in ID_EXTENDS:
                    for p in part.children:
                        if p.id != ID_EMPTY:
                            new_parts.append(p)
        parts = new_parts
        
        # make sure all partitions are in the list
        max = 0
        for part in parts:
            if part.num > max:
                max = part.num
        part_nums = list()
        for part in parts:
            part_nums.append(part.num)
        for i in range(1, max + 1):
            if i not in part_nums:
                if i < 5:
                    p = Partition(0, 0, ID_EMPTY, i, False, 0)
                    parts.append(p)
                else:
                    print 'A gap in extended partition nums for', devname + '!!!'
                    sys.exit()
        
        # sort parts
        for i in range(len(parts) - 1, 0, -1):
            for j in range(i):
                if parts[j].num > parts[j+1].num:
                    tmp = parts[j + 1]
                    parts[j + 1] = parts[j]
                    parts[j] = tmp    
        
        # create sfdisk's input
        commands = list()
        for part in parts:
            if part.id == ID_EMPTY:
                beg = ''
                size = '0'
            else:
                beg = str(part.beg)
                size = str(part.getSize())
            id = hex(part.id)[2:]
            boot = '-'
            if part.bootable:
                boot = '*'
            
            commands.append(beg + ',' + size + ',' + id + ',' + boot)
        
        # write to disk
        TMP_FILE_INPUT = TMP_FILE + '_input'
        file = open(TMP_FILE_INPUT, 'w')
        for command in commands:
            file.write(command + '\n')
            print command
        file.flush()
        file.close()
        TMP_FILE_COMMAND = TMP_FILE + '_command'
        file = open(TMP_FILE_COMMAND, 'w')
        file.write('#!' + BASH + '\n')
        file.write(SFDISK + ' -uS -L -f ' + devname + ' < ' + TMP_FILE_INPUT + '\n')
        file.flush()
        file.close()
        os.chmod(TMP_FILE_COMMAND, 0700)
        print 'commiting partitions to disk ' + devname

        if len(self.getPartitions(devname)) == 0:
            # no existing partitions, write
            out, ret = execWithCaptureStatus(TMP_FILE_COMMAND, [TMP_FILE_COMMAND])
            print out, ret
        else:
            # there is something on drive, ignore for now
            print 'joking :)'
            print 'for now'
            
        os.remove(TMP_FILE_COMMAND)
        os.remove(TMP_FILE_INPUT)
        
        
class BlockDevice:
    
    def __init__(self, devpath):
        self.__segs = list()
        self.dev = devpath
        self.sectors = 0
        self.sectorSize = 0
        self.cyls = 0
        self.spt = 0   # sectors per track
        self.spc = 0   # sectors per cylinder
        self.reload()
        
    # discard changes
    def reload(self):
        fdisk = FDisk()
        self.__segs = list()
        # get disk geometry
        self.sectors, self.sectorSize, self.cyls, self.spt, self.spc = fdisk.getDeviceGeometry(self.dev)
        # allocate all space
        new_seg = Segment(1, self.sectors-1, self.sectorSize)
        new_seg.wholeDevice = True
        self.__segs.append(new_seg)
        # get partitions
        parts = fdisk.getPartitions(self.dev)
        # then insert extended partitions
        for part in parts:
            if part.id in ID_EXTENDS:
                self.addNoAlign(part.beg, part.end, part.id, part.bootable, part.num)
        # insert other partitions
        for part in parts:
            if part.id not in ID_EXTENDS:
                self.addNoAlign(part.beg, part.end, part.id, part.bootable, part.num)
        self.__sortSegs()
    
    # !!! save partition to disk !!!
    def saveTable(self):
        # make sure extended partitions don't have gaps in numbering
        nums = self.getPartNums()
        max_part = 4
        for i in nums:
            if i > max_part:
                max_part = i
        for i in range(5, max_part + 1):
            if i not in nums:
                raise FDiskErr_extendedNumsMissing()
        FDisk().savePartTable(self.dev, self.getSegments())

    def renumberExtends(self):
        self.__sortSegs()
        i = 5
        for part in self.__segs:
            if part.id in ID_EXTENDS:
                for p in part.children:
                    if p.id != ID_EMPTY:
                        p.num = i
                        p.children[1].num = i
                        i = i + 1
        
    def getSegments(self):
        segs_copy = copy.deepcopy(self.__sortSegs())
        return self.__getSegments(segs_copy, False)
    def __getSegments(self, segs, extended):
        if extended:
            # clean up
            for seg in segs:
                if seg.id != ID_EMPTY:
                    seg.beg = seg.children[1].beg
                    seg.children = list()
        # remove small unallocatable segments
        for seg in segs[:]:
            seg.children = self.__getSegments(seg.children, True)
            if (seg.id == ID_EMPTY) and (seg.getSize() <= self.spc):
                segs.remove(seg)
        return segs
    
    def getPartNums(self):
        nums = list()
        for seg in self.__segs:
            if seg.id != ID_EMPTY:
                nums.append(seg.num)
            if seg.id in ID_EXTENDS:
                for s in seg.children:
                    if s.id != ID_EMPTY:
                        nums.append(s.num)
        return nums

    def addAlign(self, beg, end, id, bootable, num = None):
        beg = self.__alignLowerBound(beg)
        if end != self.sectors - 1:
            end = self.__alignUpperBound(end)
        return self.addNoAlign(beg, end, id, bootable, num)
    
    def addNoAlign(self, beg, end, id, bootable, num = None):
        if beg >= end or beg == None or end == None:
            raise FDiskErr_partFormat()
        if id == None or id < 1 or id > 255:
            raise FDiskErr_partFormat()
        if (bootable != True) and (bootable != False):
            raise FDiskErr_partFormat()
        if (num != None) and (num < 1):
            raise FDiskErr_partFormat()
        
        if beg >= end or id == ID_EMPTY:
            return None
        
        if id in ID_EXTENDS:
            bootable = False
            for seg in self.__segs:
                if seg.id in ID_EXTENDS:
                    # only one extended allowed
                    raise FDiskErr_extended()
        
        intoExtended = False
        for seg in self.__segs:
            if seg.id in ID_EXTENDS:
                if beg >= seg.beg and beg <= seg.end:
                    intoExtended = True

        # autodetermine partition number
        if num == None:
            avail_nums = list()
            if intoExtended:
                avail_nums = range(5, 100)
                for i in self.getPartNums():
                    if i > 4:
                        avail_nums.remove(i)
            else:
                avail_nums = range(1,5)
                for i in self.getPartNums():
                    if i < 5:
                        avail_nums.remove(i)
            if len(avail_nums) == 0:
                raise FDiskErr_num()
            num = avail_nums[0]
        
        if num in self.getPartNums():
            raise FDiskErr_num()
        if (id in ID_EXTENDS) and (num > 4):
            raise FDiskErr_extended()
        if intoExtended and num < 5:
            raise FDiskErr_extended()
        if (not intoExtended) and (num > 4):
            raise FDiskErr_extended()
        
        part = Partition(beg, end, id, num, bootable, self.sectorSize)
        if part.id in ID_EXTENDS:
            new_seg = Segment(part.beg, part.end, self.sectorSize)
            part.children = [new_seg]
        self.__insert(part)
        return num
    
    # no allignment is performed
    def __insert(self, part):
        self.__insert2(part, self.__segs, False)
    def __insert2(self, part, segs, extended):
        for seg in segs:
            if (part.beg >= seg.beg) and (part.end <= seg.end):
                if seg.id in ID_EXTENDS:
                    self.__insert2(part, seg.children, True)
                    return
                elif seg.id == ID_EMPTY:
                    if extended:
                        if part.beg == seg.beg:
                            part.beg = part.beg + 1
                        new_part = Partition(part.beg-1, part.end, part.id, part.num, part.bootable, part.sectorSize)
                        new_seg = Segment(new_part.beg, new_part.end, new_part.sectorSize)
                        new_part.children.append(new_seg)
                        self.__insert2(part, new_part.children, False)
                        part = new_part
                    if seg.beg < part.beg:
                        # add seg before
                        new_seg = Segment(seg.beg, part.beg - 1, self.sectorSize)
                        segs.append(new_seg)
                    if seg.end > part.end:
                        # add seg after
                        new_seg = Segment(part.end + 1, seg.end, self.sectorSize)
                        segs.append(new_seg)
                    # replace current seg with part
                    segs.remove(seg)
                    segs.append(part)
                    return
                else:
                    raise FDiskErr_occupied()
        raise FDiskErr_cannotFit()
    
    
    def remove(self, partNum):
        self.__sortSegs() # make sure to sort first
        self.__remove(partNum, self.__segs)
        self.__sortSegs()
    def __remove(self, partNum, segs):
        length = len(segs)
        for i in range(length):
            seg = segs[i]
            if seg.id == ID_EMPTY:
                continue
            if seg.num == partNum:
                beg = seg.beg
                end = seg.end
                remove_list = [seg]
                # merge with preceding empty segment
                if i-1 >= 0:
                    if segs[i-1].id == ID_EMPTY:
                        beg = segs[i-1].beg
                        remove_list.append(segs[i-1])
                # merge with following empty segment
                if i+1 < length:
                    if segs[i+1].id == ID_EMPTY:
                        end = segs[i+1].end
                        remove_list.append(segs[i+1])
                for rem in remove_list:
                    segs.remove(rem)
                new_seg = Segment(beg, end, self.sectorSize)
                if (new_seg.beg == 1) and (new_seg.end == self.sectors - 1):
                    new_seg.wholeDevice = True
                segs.append(new_seg)
                return
            elif seg.id in ID_EXTENDS:
                self.__remove(partNum, seg.children)
        
    
    def printout(self):
        print 'device: ' + self.dev
        print str(self.sectorSize * self.sectors), 'bytes,', str(self.sectors), 'sectors,', str(self.cyls), 'cylinders,', str(self.spt), 'sectors/track,', str(self.spc), 'sectors/cylinder'
        print 'partitions:'
        for seg in self.__segs:
            seg.printout()

    
    def __alignLowerBound(self, num):
        if num == self.spt:
            return num
        val = (num / self.spc) * self.spc
        if num == val + 1:
            return num
        val = ((num + self.spc - 1) / self.spc) * self.spc
        if val < 1:
            val = 1
        return val
    def __alignUpperBound(self, num):
        if (num + 1) % self.spc == 0:
            return num
        else:
            return (num / self.spc) * self.spc - 1
    
    def __sortSegs(self):
        return self.__sortSegs2(self.__segs)
    def __sortSegs2(self, segs):
        for seg in segs:
            self.__sortSegs2(seg.children)
        for i in range(len(segs) - 1, 0, -1):
            for j in range(i):
                if segs[j].beg < segs[j+1].beg:
                    tmp = segs[j + 1]
                    segs[j + 1] = segs[j]
                    segs[j] = tmp
        segs.reverse()
        return segs

    def printSupportedPartitions(self):
        result = execWithCapture("/sbin/sfdisk", ['/sbin/sfdisk', '-T'])
        lines = result.splitlines()
        for line in lines:
            if 'Id' in line:
                continue
            if line.strip() == '':
                continue
            id = int(line[:2].strip(), 16)
            name = line[2:].strip()
            print str(id), ':', '\'' + name + '\'' + ','
