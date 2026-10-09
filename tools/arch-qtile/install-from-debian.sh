#!/usr/bin/env bash
# Acer-specific migration: reuse ONLY the confirmed swap partition.
# The Debian/data filesystem and its partition boundaries are retained.
set -euo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
rig_sources=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
rig_bootstrap=/mnt/rig-arch-bootstrap
rig_target=/mnt/rig-arch-target
rig_data=/var/lib/rig-arch
rig_debian_uuid=19fb6bca-4430-4e9f-be15-5a509c25c3ff
rig_swap_uuid=b6336e51-a6f5-44a9-aba7-1b12f70b8351
[[ $EUID -eq 0 ]] || { echo 'Requires root.' >&2; exit 1; }
if [[ ${RIG_ARCH_PRIVATE_MOUNTS:-0} != 1 ]]; then
    exec unshare --mount --propagation private -- env RIG_ARCH_PRIVATE_MOUNTS=1 bash "$rig_sources/install-from-debian.sh" "$@"
fi
[[ $(cat /sys/class/dmi/id/product_name) == 'Aspire E1-570G' ]]
[[ $(findmnt -nro UUID /) == "$rig_debian_uuid" ]]
[[ ! -d /sys/firmware/efi ]]
[[ -x "$rig_bootstrap/usr/bin/pacstrap" ]]
[[ $(blkid -s UUID -o value /dev/sda5) == "$rig_swap_uuid" ]]
[[ $(blkid -s TYPE -o value /dev/sda5) == swap ]]
[[ $(blockdev --getsize64 /dev/sda5) == 12770607104 ]]
[[ $(lsblk -ndo PKNAME /dev/sda5) == sda ]]
! findmnt -rn -S /dev/sda5
mkdir -p "$rig_data" "$rig_data/home" "$rig_data/pkg" "$rig_data/evidence"
chmod 700 "$rig_data"
rig_backup="/var/backups/rig-arch-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$rig_backup"
cp -a /etc/fstab /etc/default/grub /boot/grub/grub.cfg "$rig_backup/"
sfdisk --dump /dev/sda > "$rig_backup/partition-table.sfdisk"
dd if=/dev/sda of="$rig_backup/mbr-first-mib.bin" bs=1M count=1 status=none
printf '%s\n' "$rig_backup" > "$rig_data/evidence/debian-backup-path"

# Check the full fresh-install dependency size, not the ISO's installed set.
mapfile -t rig_packages < "$rig_sources/packages-minimal.txt"
cp "$rig_sources/packages-minimal.txt" "$rig_bootstrap/tmp/rig-packages.txt"
mkdir -p "$rig_bootstrap/tmp/rig-plan-db"
cp -a "$rig_bootstrap/var/lib/pacman/sync" "$rig_bootstrap/tmp/rig-plan-db/"
chroot "$rig_bootstrap" bash -c '
    mapfile -t pkgs < /tmp/rig-packages.txt
    pacman --dbpath /tmp/rig-plan-db -Sp --noconfirm --print-format "%n" "${pkgs[@]}" > /tmp/rig-resolved.txt
    LC_ALL=C pacman -Si $(cat /tmp/rig-resolved.txt) > /tmp/rig-sizes.txt
'
rig_mib=$(awk '/^Installed Size/ { if ($5 == "GiB") n += $4*1024; else if ($5 == "MiB") n += $4; else if ($5 == "KiB") n += $4/1024 } END { printf "%.0f", n }' "$rig_bootstrap/tmp/rig-sizes.txt")
[[ $rig_mib -gt 500 && $rig_mib -lt 8500 ]]
[[ $(df -B1 --output=avail / | tail -n1) -gt 40000000000 ]]
cp "$rig_bootstrap/tmp/rig-resolved.txt" "$rig_data/evidence/packages-resolved.txt"
echo "PACKAGE PLAN: ${rig_mib} MiB; target partition 12179 MiB."

# Minimal migration requested by the operator: no home/model transfer.
# Retain the interrupted copy as well as the original; neither is deleted.
if [[ -d "$rig_data/home/red-team-lab" ]]; then
    mv "$rig_data/home" "$rig_data/home-incomplete-$(date -u +%Y%m%dT%H%M%SZ)"
fi
install -d -m755 "$rig_data/home"
install -d -o1000 -g1000 -m700 "$rig_data/home/red-team-lab"
install -d -o1000 -g1000 -m700 "$rig_data/home/red-team-lab/.config"
if [[ -d /home/red-team-lab/.config/kitty ]]; then
    cp -a /home/red-team-lab/.config/kitty "$rig_data/home/red-team-lab/.config/"
fi
if [[ -f /home/red-team-lab/.gitconfig ]]; then
    cp -a /home/red-team-lab/.gitconfig "$rig_data/home/red-team-lab/"
fi
ln -s /srv/rig-data/home/red-team-lab/RED-TEAM-LAB "$rig_data/home/red-team-lab/RED-TEAM-LAB"
ln -s /srv/rig-data/home/red-team-lab/.codex "$rig_data/home/red-team-lab/.codex"
chown -h 1000:1000 "$rig_data/home/red-team-lab/RED-TEAM-LAB" "$rig_data/home/red-team-lab/.codex"
echo 'MINIMAL HOME READY: project and Codex history linked; original files retained.'

# Replace unused swap with a file before formatting ONLY its old partition.
[[ ! -e "$rig_data/swapfile" ]]
fallocate -l 4G "$rig_data/swapfile"
chmod 600 "$rig_data/swapfile"
mkswap "$rig_data/swapfile"
swapon "$rig_data/swapfile"
swapoff /dev/sda5
! awk '$1 == "/dev/sda5" {found=1} END {exit !found}' /proc/swaps
python3 - "$rig_swap_uuid" "$rig_data/swapfile" <<'PY'
import pathlib, sys
p = pathlib.Path('/etc/fstab')
lines = p.read_text().splitlines()
lines = ['# RIG replaced old swap: ' + line if line.startswith('UUID=' + sys.argv[1]) else line for line in lines]
lines.append(sys.argv[2] + ' none swap sw 0 0')
p.write_text('\n'.join(lines) + '\n')
PY
systemctl daemon-reload
[[ $(blkid -s TYPE -o value /dev/sda5) == swap ]]
[[ $(blkid -s UUID -o value /dev/sda5) == "$rig_swap_uuid" ]]
mkfs.ext4 -F -L RIG_ARCH /dev/sda5
rig_arch_uuid=$(blkid -s UUID -o value /dev/sda5)
printf '%s\n' "$rig_arch_uuid" > "$rig_data/evidence/arch-root.uuid"
mkdir -p "$rig_target"
mount /dev/sda5 "$rig_target"
mkdir -p "$rig_target/home" "$rig_target/srv/rig-data" "$rig_target/var/cache/pacman/pkg" "$rig_bootstrap/mnt/target"
chmod 755 "$rig_target/home" "$rig_target/srv" "$rig_target/srv/rig-data" "$rig_target/var" "$rig_target/var/cache" "$rig_target/var/cache/pacman"
mount --bind / "$rig_target/srv/rig-data"
mount --bind "$rig_data/home" "$rig_target/home"
mount --bind "$rig_data/pkg" "$rig_target/var/cache/pacman/pkg"
mount --rbind "$rig_target" "$rig_bootstrap/mnt/target"
mount --make-rslave "$rig_bootstrap/mnt/target"
echo 'Installing Arch packages; no changes to the data partition.'
umask 022
chroot "$rig_bootstrap" pacstrap -K /mnt/target "${rig_packages[@]}"
umask 077
chmod 755 "$rig_target" "$rig_target/etc"
bash "$rig_sources/finish-installed-target.sh"
