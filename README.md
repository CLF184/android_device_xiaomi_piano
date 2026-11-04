# OrangeFox 16 for Xiaomi Pad 8 Pro

OrangeFox 16 recovery device tree for the Xiaomi Pad 8 Pro (piano).

## USB mass storage

In **Advanced**, tap **Enable USB Mass Storage**. The MSC implementation is
adapted from [ArKT's Nabu recovery](https://github.com/ArKT-7/twrp_device_xiaomi_nabu/tree/9bf1fd3b182d9884f7f9309c40e8376cdc8e37d4):
it exports `/dev/block/sda` read/write and switches SELinux to Permissive with
`setenforce 0`. It has no disable item or automatic reboot. Safely eject the
disk on the computer, then use recovery's existing Reboot menu to leave MSC.

Apply `patches/ofox_bootable_recovery/0017-arkt-mass-storage.patch` after the
existing OrangeFox patches, or use `tools/apply-ofox-patches.sh`. This changes
the recovery sources, not the ramdisk-only boot format or the ROM kernel.

## Fix GPT

In **Advanced**, tap **Fix GPT** and use the existing confirmation slider.
The repair action is the same as the TWRP GPT build: release piano's crypto
mounts and mappings, reject active MSC, then run the Nabu gdisk
`x / j / Enter / k / Enter / w / Y` sequence on each existing
`/dev/block/sda` through `/dev/block/sdf`. Geometry comes from the current disk;
no stock GPT template or fixed partition offsets are installed.

`tools/apply-ofox-patches.sh` applies both the OrangeFox `0018` menu/action
patch and `patches/external_gptfdisk/0001-build-gdisk-with-upstream-backup-table-move.patch`.
The latter builds Android's gdisk and backports the upstream 1.0.10 `k` command
and its last-used-LBA helper. Reboot Recovery after the operation before
mounting partitions or enabling MSC.

`dmctl.recovery` is included for releasing the userdata mapper and is checked
before teardown and in CI. Shared MSC/GPT preparation contains no special
`/esp` or `/win` unmount calls, by-name branches or path handling.

The CI workflow first tests six disposable 4K-sector disks, checking both GPT
copies, CRCs, unchanged partition entries/payload and repeat execution. These
tests do not establish a Piano-specific Windows compatibility fix on hardware.

Path:

```text
device/xiaomi/piano
```

See the [main branch](../../tree/main) for the other device trees.
