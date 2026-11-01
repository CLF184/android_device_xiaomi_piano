# TWRP 16 for Xiaomi Pad 8 Pro

TWRP 16 recovery device tree for the Xiaomi Pad 8 Pro (piano).

## USB mass storage

In **Advanced**, tap **Enable USB Mass Storage**. The MSC implementation is
adapted from [ArKT's Nabu recovery](https://github.com/ArKT-7/twrp_device_xiaomi_nabu/tree/9bf1fd3b182d9884f7f9309c40e8376cdc8e37d4):
it exports `/dev/block/sda` read/write and switches SELinux to Permissive with
`setenforce 0`. It has no disable item or automatic reboot. Safely eject the
disk on the computer, then use recovery's existing Reboot menu to leave MSC.

The new source patch is `patches/bootable_recovery/0008-arkt-mass-storage.patch`;
apply it after the existing patches when building this branch. This changes
the recovery sources, not the ramdisk-only boot format or the ROM kernel.

Path:

```text
device/xiaomi/piano
```

See the [main branch](../../tree/main) for the other device trees.
