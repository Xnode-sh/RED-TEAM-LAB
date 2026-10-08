#!/usr/bin/env bash
# Adds an Arch Live entry; never partitions, formats or reboots.
set -euo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo 'Run with sudo in a local terminal.' >&2; exit 1; }
rig_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
rig_iso="$rig_dir/downloads/archlinux-2026.10.01-x86_64.iso"
rig_expected=684ded26c63240ff4a41e8c25ee84ea6da233f557364821f13d12c2b0a9059a5
[[ -f "$rig_iso" && ! -d /sys/firmware/efi ]] || { echo 'Expected ISO and BIOS boot required.' >&2; exit 1; }
[[ $(sha256sum "$rig_iso" | cut -d ' ' -f 1) == "$rig_expected" ]] || { echo 'ISO hash mismatch.' >&2; exit 1; }
rig_uuid=$(findmnt -nro UUID /)
[[ "$rig_uuid" == 19fb6bca-4430-4e9f-be15-5a509c25c3ff ]] || { echo 'Unexpected root filesystem.' >&2; exit 1; }
command -v grub-mkconfig >/dev/null
command -v grub-script-check >/dev/null
rig_backup="/var/backups/rig-hdd-live-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$rig_backup"
cp -a /boot/grub/grub.cfg "$rig_backup/grub.cfg"
[[ ! -e /etc/grub.d/42_rig_arch_live ]] || cp -a /etc/grub.d/42_rig_arch_live "$rig_backup/42_rig_arch_live"
mkdir -p /boot/iso
cp --reflink=auto "$rig_iso" /boot/iso/archlinux-2026.10.01-x86_64.iso
[[ $(sha256sum /boot/iso/archlinux-2026.10.01-x86_64.iso | cut -d ' ' -f 1) == "$rig_expected" ]]
cat > /etc/grub.d/42_rig_arch_live <<'GRUB_SCRIPT'
#!/bin/sh
exec tail -n +3 "$0"
menuentry 'RIG: Arch Live from HDD (RAM)' --id rig-arch-live {
    insmod part_msdos
    insmod ext2
    insmod loopback
    search --no-floppy --fs-uuid --set=root 19fb6bca-4430-4e9f-be15-5a509c25c3ff
    set isofile='/boot/iso/archlinux-2026.10.01-x86_64.iso'
    loopback loop ($root)$isofile
    linux (loop)/arch/boot/x86_64/vmlinuz-linux archisobasedir=arch img_dev=/dev/disk/by-uuid/19fb6bca-4430-4e9f-be15-5a509c25c3ff img_loop=$isofile copytoram=y
    initrd (loop)/arch/boot/x86_64/initramfs-linux.img
}
GRUB_SCRIPT
chmod 755 /etc/grub.d/42_rig_arch_live
grub-mkconfig -o "$rig_backup/grub.cfg.new"
grub-script-check "$rig_backup/grub.cfg.new"
grep -q -- '--id rig-arch-live' "$rig_backup/grub.cfg.new"
install -m 600 "$rig_backup/grub.cfg.new" /boot/grub/grub.cfg
sync
echo "READY: GRUB entry installed; Debian remains default. Backup: $rig_backup"
echo 'At reboot hold Shift to show GRUB, then select RIG: Arch Live from HDD (RAM).'
echo 'No disk partition or filesystem was changed. Installation is a separate stage.'
