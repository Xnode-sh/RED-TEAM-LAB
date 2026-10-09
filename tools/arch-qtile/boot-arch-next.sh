#!/usr/bin/env bash
# Select Arch Live for one boot only; do not reboot or change partitions.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run this script with sudo.' >&2; exit 1; }
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
rig_iso=/boot/iso/archlinux-2026.10.01-x86_64.iso
rig_expected=684ded26c63240ff4a41e8c25ee84ea6da233f557364821f13d12c2b0a9059a5
[[ -f "$rig_iso" ]] || { echo 'Arch ISO is missing.' >&2; exit 1; }
[[ $(sha256sum "$rig_iso" | cut -d ' ' -f 1) == "$rig_expected" ]] || { echo 'ISO hash mismatch.' >&2; exit 1; }
grub-script-check /boot/grub/grub.cfg
grep -q -- '--id rig-arch-live' /boot/grub/grub.cfg
grep -q 'next_entry' /boot/grub/grub.cfg
command -v grub-reboot >/dev/null
grub-reboot rig-arch-live
grub-editenv /boot/grub/grubenv list | grep -Fx 'next_entry=rig-arch-live'
sync
echo 'READY: next reboot selects Arch Live. Debian remains the normal default.'
