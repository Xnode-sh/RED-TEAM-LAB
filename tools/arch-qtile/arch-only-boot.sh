#!/usr/bin/env bash
# Run on the installed Arch host with sudo. Keep user data on sda1 intact.
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
source /etc/os-release
[[ $ID == arch ]]
[[ ! -d /sys/firmware/efi ]]
[[ $(findmnt -nro UUID /) == 7fbd462e-248f-465c-bf51-d982f54ded68 ]]
[[ $(findmnt -nro UUID /srv/rig-data) == 19fb6bca-4430-4e9f-be15-5a509c25c3ff ]]
[[ $(lsblk -ndo TYPE /dev/sda) == disk ]]
[[ -s /boot/vmlinuz-linux-lts && -s /boot/initramfs-linux-lts.img ]]
for rig_cmd in grub-install grub-mkconfig grub-script-check; do command -v "$rig_cmd" >/dev/null; done
umask 077
rig_backup=/var/backups/arch-only-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$rig_backup"
cp -a /etc/default/grub /etc/fstab "$rig_backup/"
cp -a /srv/rig-data/boot/grub "$rig_backup/debian-grub"
dd if=/dev/sda of="$rig_backup/mbr-and-embedding.bin" bs=512 count=2048 status=none
systemd-analyze > "$rig_backup/startup-before.txt"
systemd-analyze critical-chain > "$rig_backup/critical-chain-before.txt"
python3 - <<'PY'
from pathlib import Path
p = Path('/etc/default/grub')
settings = {'GRUB_DEFAULT': '0', 'GRUB_TIMEOUT': '1',
            'GRUB_TIMEOUT_STYLE': 'hidden', 'GRUB_DISABLE_OS_PROBER': 'true',
            'GRUB_SAVEDEFAULT': 'false'}
lines = [line for line in p.read_text().splitlines()
         if not any(line.startswith(key + '=') for key in settings)]
p.write_text('\n'.join(lines + [f'{key}={value}' for key, value in settings.items()]) + '\n')
PY
# Generate and validate before replacing the BIOS loader.
grub-mkconfig -o "$rig_backup/arch-grub.cfg"
grub-script-check "$rig_backup/arch-grub.cfg"
grep -q 'vmlinuz-linux-lts' "$rig_backup/arch-grub.cfg"
if grep -Eiq 'menuentry .*Debian|rig-arch-live|rig-arch-installed' "$rig_backup/arch-grub.cfg"; then
    echo 'Unexpected migration/Debian entry; stopping.'; exit 1
fi
mkdir -p /boot/grub
install -m600 "$rig_backup/arch-grub.cfg" /boot/grub/grub.cfg
grub-install --target=i386-pc --boot-directory=/boot --recheck /dev/sda
grub-script-check /boot/grub/grub.cfg
systemctl disable rig-arch-first-boot.service 2>/dev/null || true
mkdir -p /etc/systemd/system/rig-arch-first-boot.service.d
printf '[Unit]\nOnFailure=\nConditionPathExists=/nonexistent-arch-migration-disabled\n' > /etc/systemd/system/rig-arch-first-boot.service.d/disabled.conf
systemctl daemon-reload
sync
echo "ARCH_BOOT_READY; backup: $rig_backup"
echo 'Debian data untouched. Verify a reboot into Arch before removing its old boot/system files.'
