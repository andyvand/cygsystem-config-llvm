import gettext
_ = gettext.gettext


PROGNAME = "system-config-lvm"
INSTALLDIR="/usr/share/system-config-lvm/"

LVM_PATH="/usr/sbin/"
LVM_BIN_PATH = LVM_PATH + 'lvm'
LVMDISKSCAN_BIN_PATH = LVM_PATH + 'lvmdiskscan'
LVDISPLAY_BIN_PATH = LVM_PATH + 'lvdisplay'
LVCREATE_BIN_PATH = LVM_PATH + 'lvcreate'
LVRENAME_BIN_PATH = LVM_PATH + 'lvrename'
LVEXTEND_BIN_PATH = LVM_PATH + 'lvextend'
LVREDUCE_BIN_PATH = LVM_PATH + 'lvreduce'
LVREMOVE_BIN_PATH = LVM_PATH + 'lvremove'
PVCREATE_BIN_PATH = LVM_PATH + 'pvcreate'
PVREMOVE_BIN_PATH = LVM_PATH + 'pvremove'
PVMOVE_BIN_PATH = LVM_PATH + 'pvmove'
VGCREATE_BIN_PATH = LVM_PATH + 'vgcreate'
VGCHANGE_BIN_PATH = LVM_PATH + 'vgchange'
VGEXTEND_BIN_PATH = LVM_PATH + 'vgextend'
VGREDUCE_BIN_PATH = LVM_PATH + 'vgreduce'
VGREMOVE_BIN_PATH = LVM_PATH + 'vgremove'


###Types of views to render
UNSELECTABLE_TYPE = 0
VG_TYPE = 1
VG_PHYS_TYPE = 2
VG_LOG_TYPE = 3
PHYS_TYPE = 4
LOG_TYPE = 5
UNALLOCATED_TYPE = 6
UNINITIALIZED_TYPE = 7

NAME_COL = 0
TYPE_COL = 1
PATH_COL = 2
SIMPLE_LV_NAME_COL = 3
OBJ_COL = 4

#INIT_ENTITY=_("Are you certain that you wish to initialize disk entity %s? All data will be lost on this device/partition.")
INIT_ENTITY=_("All data on disk entity %s will be lost! Are you certain that you wish to initialize it?")
INIT_ENTITY_MOUNTED=_("Disk entity %s contains data of folder %s. All data in it will be lost! Are you certain that you wish to initialize disk entity %s?")
INIT_ENTITY_FREE_SPACE=_("Are you certain that you wish to initialize %s of free space on disk %s?")
INIT_ENTITY_DEVICE_CHOICE=_("You are about to initialize unpartitioned disk %s. It is advisable, although not required, to create a partition on it. Do you want to create a single partition encompassing the whole drive? Choosing No will initialize unpartitioned disk.")

NEW_LV_NAME_ARG = 0
NEW_LV_VGNAME_ARG = 1
NEW_LV_SIZE_ARG = 2
NEW_LV_UNIT_ARG = 3
NEW_LV_IS_STRIPED_ARG = 4
NEW_LV_STRIPE_SIZE_ARG = 5
NEW_LV_NUM_STRIPES_ARG = 6
NEW_LV_MAKE_FS_ARG = 7
NEW_LV_FS_TYPE_ARG = 8
NEW_LV_MAKE_MNT_POINT_ARG = 9
NEW_LV_MNT_POINT_ARG = 10
NEW_LV_FSTAB_ARG = 11

EXTENT_IDX = 0
GIGABYTE_IDX = 1
MEGABYTE_IDX = 2
KILOBYTE_IDX = 3

UNUSED=_("Unused")
FREE=_("Free")
FREE_SPACE=_("Free space")

GIG_SUFFIX=_("G")
MEG_SUFFIX=_("M")
KILO_SUFFIX=_("K")
BYTE_SUFFIX=_("B")


#File System Types
NO_FILESYSTEM=_("No Filesystem")
EXT2_T=_("Ext2")
EXT3_T=_("Ext3")
JFS_T=_("JFS")
MSDOS_T=_("MSDOS")
REISERFS_T=_("Reiserfs")
VFAT_T=_("VFAT")
XFS_T=_("XFS")
CRAMFS_T=_("Cramfs")

