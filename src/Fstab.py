
import sys
import os

DEVICE = 0
MOUNTPOINT = 1
FSTYPE = 2
OPTIONS = 3
DUMP = 4
FSCK = 5


FSTAB = '/etc/fstab'
FSTAB_TMP = '/tmp/fstab.tmp'
#FSTAB = '/tmp/fstab'
#FSTAB_TMP = '/tmp/fstab.tmp'

    
def add(dev_path, mnt_point, fstype, options='defaults', dump='1', fsck='2'):
    line = dev_path + '\t\t' + mnt_point + '\t\t' + fstype + '\t' + options
    line = line + '\t' + dump + ' ' + fsck + '\n'
    
    fstab = __remove(dev_path, mnt_point)
    fstab.write(line)
    fstab.close()
    
    os.rename(FSTAB_TMP, FSTAB)
    
def remove(dev_path, mnt_point):
    fstab = __remove(dev_path, mnt_point)
    fstab.close()
    os.rename(FSTAB_TMP, FSTAB)
    
def __remove(dev_path, mnt_point):
    fstab = open(FSTAB, 'r')
    lines = fstab.readlines()
    fstab.close()
    
    fstab_new = open(FSTAB_TMP, 'w')
    for line in lines:
        line = line.strip().rstrip('\n')
        words = line.split(' ')
        words_new = []
        for word in words:
            for w in word.split('\t'):
                if w != '':
                    words_new.append(w)
        words = words_new
        
        if len(words) != 6:
            fstab_new.write(line + '\n')
            continue
        
        if words[0] == '#':
            fstab_new.write(line + '\n')
            continue
        
        if (words[DEVICE] == dev_path) and (words[MOUNTPOINT] == mnt_point):
            # line needs to be removed
            pass
        else:
            fstab_new.write(line + '\n')
            
    return fstab_new


def get_mountpoint(dev_path):
    if dev_path == None:
        return None
    
    fstab = open(FSTAB, 'r')
    lines = fstab.readlines()
    fstab.close()
    
    for line in lines:
        line = line.strip().rstrip('\n')
        words = line.split(' ')
        words_new = []
        for word in words:
            for w in word.split('\t'):
                if w != '':
                    words_new.append(w)
        words = words_new
        
        if len(words) != 6:
            continue
        if words[0] == '#':
            continue
        
        if words[DEVICE] == dev_path:
            # line present
            return words[MOUNTPOINT]

    return None
