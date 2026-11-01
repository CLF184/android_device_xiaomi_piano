#!/system/bin/sh
set -eu
for service in vendor.piano_prepdecrypt vendor.piano_boot_adsp \
    vendor.piano_batterysecret vendor.weaver_hos3 vendor.weaver_hos4 \
    vendor.keymint vendor.gatekeeper_default vendor.ssgtzd vendor.qwesd \
    vendor.minkdaemon vendor.qseecomd; do
    [ -n "$(getprop init.svc.$service)" ] || continue
    setprop ctl.stop "$service"
    retries=0
    while [ "$(getprop init.svc.$service)" != stopped ]; do
        retries=$((retries + 1))
        [ "$retries" -lt 50 ] || exit 1
        sleep 0.1
    done
done
# Only unmount filesystems backed by the exported UFS logical disk.
on_export_disk() {
    case "$1" in sda|sda[0-9]*) return 0 ;; esac
    for slave in /sys/class/block/"$1"/slaves/*; do
        [ -e "$slave" ] || continue
        if on_export_disk "${slave##*/}"; then return 0; fi
    done
    return 1
}
sync
while read -r source target rest; do
    case "$source" in /dev/block/*) ;; *) continue ;; esac
    device=$(readlink -f "$source")
    if on_export_disk "${device##*/}"; then printf '%s\n' "$target"; fi
done < /proc/mounts | sort -r > /tmp/piano-msc-mounts
while read -r target; do
    printf 'Unmounting %s\n' "$target"
    umount "$target" || exit 1
done < /tmp/piano-msc-mounts
sync
echo 'All mounted filesystems on sda were unmounted normally.'
