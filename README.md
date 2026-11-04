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

## Fix GPT

In **Advanced**, tap **Fix GPT** and use the normal confirmation slider.
The action runs ArKT's Nabu `x / j / Enter / k / Enter / w / Y` gdisk sequence
on each existing `/dev/block/sda` through `/dev/block/sdf`. It reads the current
GPT and sector size at runtime; no piano partition template or fixed offsets
are installed. Existing partition entries and filesystem contents are retained.

The action rejects active MSC and releases piano's crypto mounts and mappings
before writing. Per-disk gdisk output and failures are shown in the operation
log. Reboot Recovery afterwards before mounting partitions or enabling MSC.

The image also includes `dmctl.recovery` for releasing the userdata mapper.
Required tools are checked before mount teardown and in CI. The shared MSC/GPT
preparation has no special `/esp` or `/win` unmount calls or path handling.

`patches/external_gptfdisk/0001-build-gdisk-with-upstream-backup-table-move.patch`
builds Android's existing gdisk sources and backports the upstream 1.0.10 `k`
command. Apply it to AOSP `external/gptfdisk` at `android-16.0.0_r1`, then apply
the complete `patches/bootable_recovery/` queue, including `0009`.

The CI regression test uses disposable 4096-byte-sector loop disks matching
the six piano GPT table sizes and gaps. It checks both GPT copies, CRCs,
partition entries, payload preservation and repeat execution. It does not
exercise the action on a physical tablet.

Path:

```text
device/xiaomi/piano
```

See the [main branch](../../tree/main) for the other device trees.
