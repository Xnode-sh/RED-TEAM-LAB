#!/usr/bin/env bash
# Explicitly authorized Debian removal; never format the shared data partition.
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'Run with sudo'; exit 1; }
source /etc/os-release
[[ $ID == arch && ! -d /sys/firmware/efi ]]
rig_data=/srv/rig-data
[[ $(findmnt -nro UUID /) == 7fbd462e-248f-465c-bf51-d982f54ded68 ]]
[[ $(findmnt -nro UUID "$rig_data") == 19fb6bca-4430-4e9f-be15-5a509c25c3ff ]]
[[ -s /boot/grub/grub.cfg && -s /boot/vmlinuz-linux-lts && -s /boot/initramfs-linux-lts.img ]]
grub-script-check /boot/grub/grub.cfg
grep -q 'vmlinuz-linux-lts' /boot/grub/grub.cfg
! grep -Eiq 'menuentry .*Debian|rig-arch-installed|rig-arch-live' /boot/grub/grub.cfg
# No mounted old system tree may be removed, including bootstrap overlay mounts.
python3 - <<'PY'
from pathlib import Path
import os
base = '/srv/rig-data/'
blocked = ('usr', 'boot', 'etc', 'root', 'opt', 'dev', 'proc', 'sys', 'run', 'tmp', 'mnt', 'media', 'srv')
for line in Path('/proc/self/mountinfo').read_text().splitlines():
    mount = line.split()[4].replace('\\040', ' ')
    if any(mount == base + x or mount.startswith(base + x + '/') for x in blocked):
        raise SystemExit('Mounted legacy tree: ' + mount)
# Preserve every user symlink dependency; fail before deleting any old binaries.
for tree in ('/home', base + 'home'):
    for root, dirs, files in os.walk(tree, followlinks=False):
        for name in dirs + files:
            path = os.path.join(root, name)
            if os.path.islink(path):
                target = os.path.realpath(path)
                if any(target == base+x or target.startswith(base+x+'/') for x in ('usr', 'boot', 'etc', 'root', 'opt')):
                    raise SystemExit('User dependency on Debian: ' + path)
PY
umask 077
rig_archive="$rig_data/.migration-archive/debian-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$rig_archive/var/lib" "$rig_archive/var/cache"
rig_before=$(df -B1 --output=avail "$rig_data" | tail -1)
# Reinstall the BIOS loader from Arch before touching the legacy boot directory.
grub-install --target=i386-pc --boot-directory=/boot --recheck /dev/sda
grub-script-check /boot/grub/grub.cfg
systemctl disable rig-arch-first-boot.service 2>/dev/null || true
if [[ -f /etc/systemd/system/rig-arch-recover.service ]]; then
    mv /etc/systemd/system/rig-arch-recover.service "$rig_archive/rig-arch-recover.service"
fi
systemctl daemon-reload
# Preserve private configuration, root files, custom installs and service state.
for rig_name in etc root opt; do
    [[ ! -e "$rig_data/$rig_name" ]] || mv "$rig_data/$rig_name" "$rig_archive/"
done
if [[ -d "$rig_data/usr/local" ]]; then mv "$rig_data/usr/local" "$rig_archive/usr-local"; fi
for rig_path in "$rig_data"/var/lib/*; do
    [[ -e "$rig_path" || -L "$rig_path" ]] || continue
    rig_name=${rig_path##*/}
    case "$rig_name" in
        rig-arch) continue ;;
        dpkg|apt) rm -rf --one-file-system -- "$rig_path" ;;
        *) mv "$rig_path" "$rig_archive/var/lib/" ;;
    esac
done
for rig_path in "$rig_data"/var/cache/*; do
    [[ -e "$rig_path" || -L "$rig_path" ]] || continue
    rig_name=${rig_path##*/}
    case "$rig_name" in
        apt) rm -rf --one-file-system -- "$rig_path" ;;
        *) mv "$rig_path" "$rig_archive/var/cache/" ;;
    esac
done
for rig_name in log spool mail tmp; do
    [[ ! -e "$rig_data/var/$rig_name" ]] || mv "$rig_data/var/$rig_name" "$rig_archive/var/"
done
# Only distribution binaries, obsolete kernels and their top-level symlinks.
for rig_name in usr boot bin sbin lib lib64 initrd.img initrd.img.old vmlinuz vmlinuz.old; do
    rm -rf --one-file-system -- "$rig_data/$rig_name"
done
e2label /dev/sda1 RIG_DATA
sync
[[ -d /home/red-team-lab/RED-TEAM-LAB/.git ]]
[[ -d /home/red-team-lab/.codex ]]
[[ -s "$rig_data/var/lib/rig-arch/swapfile" ]]
runuser -u red-team-lab -- /home/red-team-lab/.local/bin/codex --version
rig_after=$(df -B1 --output=avail "$rig_data" | tail -1)
echo "DEBIAN_REMOVED; reclaimed bytes: $((rig_after-rig_before))"
echo "Private configuration/service archive: $rig_archive"
echo 'Arch BIOS loader checked; home/project/Codex/swap preserved. Reboot timing remains to be measured.'
