#!/usr/bin/env bash
# Operator explicitly authorized erasing the identified Silicon-Power USB.
# This script does NOT modify the internal HDD or replace Debian.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run with sudo in a local terminal.' >&2; exit 1; }
rig_project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
rig_device=/dev/sdb
rig_expected_bytes=15833497600
rig_iso_name=archlinux-2026.10.01-x86_64.iso
rig_expected_hash=684ded26c63240ff4a41e8c25ee84ea6da233f557364821f13d12c2b0a9059a5
rig_downloads="$rig_project/tools/arch-qtile/downloads"
rig_ventoy="$rig_downloads/ventoy-1.1.17"
[[ -b "$rig_device" ]] || { echo 'Expected USB device is absent; re-identify devices.' >&2; exit 1; }
[[ "$(lsblk -bdn -o SIZE "$rig_device")" == "$rig_expected_bytes" ]] || { echo 'USB size mismatch.' >&2; exit 1; }
[[ "$(lsblk -dn -o MODEL "$rig_device" | xargs)" == Silicon-Power16G ]] || { echo 'USB model mismatch.' >&2; exit 1; }
[[ "$(lsblk -dn -o TRAN "$rig_device" | xargs)" == usb ]] || { echo 'Refusing non-USB disk.' >&2; exit 1; }
rig_root_device=$(findmnt -n -o SOURCE /)
if lsblk -s -n -r -o NAME "$rig_root_device" | awk '$0=="sdb"{found=1} END{exit !found}'; then
    echo 'USB unexpectedly contains the running root filesystem.' >&2; exit 1
fi
rig_first_label=$(lsblk -n -o LABEL "${rig_device}1" | xargs)
if [[ "$rig_first_label" != Ventoy ]]; then
    [[ -z "$(lsblk -n -o MOUNTPOINTS "$rig_device" | tr -d '[:space:]')" ]] || {
        echo 'USB has mounted filesystems. Unmount them, then retry.' >&2; exit 1;
    }
    [[ "$rig_first_label" == 22631_3155_Compact_x64 ]] || { echo 'Unexpected existing USB label.' >&2; exit 1; }
fi
printf '%s  %s\n' "$rig_expected_hash" "$rig_downloads/$rig_iso_name" | sha256sum -c -
echo 'Target: Silicon-Power16G, /dev/sdb, 15 833 497 600 bytes.'
echo 'Operator authorized clearing its Windows installer. Internal HDD is not touched.'
if [[ "$rig_first_label" != Ventoy ]]; then
    (cd "$rig_ventoy" && printf 'y\ny\n' | bash ./Ventoy2Disk.sh -i "$rig_device")
    udevadm settle
fi
[[ "$(lsblk -n -o LABEL "${rig_device}1" | xargs)" == Ventoy ]] || { echo 'Ventoy main partition not confirmed.' >&2; exit 1; }
[[ "$(lsblk -n -o LABEL "${rig_device}2" | xargs)" == VTOYEFI ]] || { echo 'Ventoy EFI partition not confirmed.' >&2; exit 1; }
rig_mount=/mnt/rig-ventoy
mkdir -p "$rig_mount"
if mountpoint -q "$rig_mount"; then
    [[ "$(findmnt -n -o SOURCE "$rig_mount")" == "${rig_device}1" ]] || { echo 'Mountpoint belongs to another device.' >&2; exit 1; }
else
    mount -o uid=1000,gid=1000,umask=077 "${rig_device}1" "$rig_mount"
fi
if [[ ! -f "$rig_mount/$rig_iso_name" ]]; then
    cp -- "$rig_downloads/$rig_iso_name" "$rig_mount/$rig_iso_name.partial"
    printf '%s  %s\n' "$rig_expected_hash" "$rig_mount/$rig_iso_name.partial" | sha256sum -c -
    mv -- "$rig_mount/$rig_iso_name.partial" "$rig_mount/$rig_iso_name"
fi
printf '%s  %s\n' "$rig_expected_hash" "$rig_mount/$rig_iso_name" | sha256sum -c -
mkdir -p "$rig_mount/rig-migration"
rsync -rt --no-perms --no-owner --no-group --exclude=downloads/ --exclude=__pycache__/ \
    "$rig_project/tools/arch-qtile/" "$rig_mount/rig-migration/"
cp -- "$rig_downloads/$rig_iso_name.sig" "$rig_downloads/arch-release-key.asc" "$rig_mount/rig-migration/"
printf '%s  %s\n' "$rig_expected_hash" "$rig_iso_name" > "$rig_mount/ARCH-SHA256SUMS"
printf '%s\n' 'Arch ISO and migration tools copied and verified.' \
    'USER DATA BACKUP HAS NOT YET BEEN CREATED.' \
    'Boot Arch via Ventoy. Do not format HDD until backup-live.sh --migration succeeds and restore checks pass.' \
    > "$rig_mount/rig-migration/PREPARATION-STATUS.txt"
sync
df -h "$rig_mount"
echo 'READY: bootable USB prepared. Debian and internal HDD are unchanged.'
echo "USB remains mounted at $rig_mount. Unmount before unplugging."
