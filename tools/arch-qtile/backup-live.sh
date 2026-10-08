#!/usr/bin/env bash
# Run from a Live system with Debian mounted read-only and an external backup disk.
set -euo pipefail
umask 077
if [[ $# -ne 2 ]]; then
    echo 'Usage: bash backup-live.sh /mnt/debian /mnt/backup' >&2
    exit 2
fi
rig_source=$(realpath -- "$1")
rig_destination=$(realpath -- "$2")
[[ $EUID -eq 0 ]] || { echo 'Run as root in the Live system.' >&2; exit 1; }
[[ "$rig_source" != / ]] || { echo 'Refusing the running root filesystem.' >&2; exit 1; }
mountpoint -q "$rig_source" || { echo 'Debian source must be a mountpoint.' >&2; exit 1; }
mountpoint -q "$rig_destination" || { echo 'Backup destination must be a mountpoint.' >&2; exit 1; }
[[ -d "$rig_source/home/red-team-lab/RED-TEAM-LAB/.git" ]] || { echo 'Expected project not found.' >&2; exit 1; }
findmnt -n -o OPTIONS --target "$rig_source" | tr ',' '\n' | awk '$0=="ro"{found=1} END{exit !found}' || {
    echo 'Mount Debian read-only before archiving.' >&2; exit 1;
}
rig_source_device=$(findmnt -n -o SOURCE --target "$rig_source")
rig_destination_device=$(findmnt -n -o SOURCE --target "$rig_destination")
[[ "$rig_source_device" == /dev/* && "$rig_destination_device" == /dev/* ]] || {
    echo 'This helper requires two local block-device filesystems.' >&2; exit 1;
}
rig_source_disks=$(lsblk -s -n -r -o NAME,TYPE "$rig_source_device" | awk '$2=="disk"{print $1}')
rig_destination_disks=$(lsblk -s -n -r -o NAME,TYPE "$rig_destination_device" | awk '$2=="disk"{print $1}')
[[ -n "$rig_source_disks" && -n "$rig_destination_disks" ]] || { echo 'Cannot identify physical disks.' >&2; exit 1; }
for rig_disk in $rig_source_disks; do
    if printf '%s\n' "$rig_destination_disks" | awk -v disk="$rig_disk" '$0==disk{found=1} END{exit !found}'; then
        echo 'Backup must be on a different physical disk.' >&2; exit 1
    fi
done
command -v gpg >/dev/null
rig_bytes=$(du -sx --block-size=1 "$rig_source" | awk '{print $1}')
rig_free=$(df --output=avail -B1 "$rig_destination" | tail -n 1 | tr -d ' ')
(( rig_free > rig_bytes + 1073741824 )) || { echo 'Not enough free space for uncompressed backup plus margin.' >&2; exit 1; }
rig_directory="$rig_destination/rig-debian-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -m 700 -- "$rig_directory"
export GPG_TTY=$(tty)
echo 'Choose an encryption passphrase in the local terminal; do not send it to chat.'
tar --one-file-system --acls --xattrs --numeric-owner \
    --exclude='./proc/*' --exclude='./sys/*' --exclude='./dev/*' \
    --exclude='./run/*' --exclude='./tmp/*' --exclude='./mnt/*' --exclude='./media/*' \
    -C "$rig_source" -cf - . | \
    gpg --symmetric --cipher-algo AES256 --output "$rig_directory/debian-root.tar.gpg.partial"
echo 'Verifying decryption and archive structure; enter the same passphrase if requested.'
gpg --decrypt "$rig_directory/debian-root.tar.gpg.partial" | tar -tf - >/dev/null
mv -- "$rig_directory/debian-root.tar.gpg.partial" "$rig_directory/debian-root.tar.gpg"
(cd "$rig_directory" && sha256sum debian-root.tar.gpg > SHA256SUMS)
sync
echo "Verified backup: $rig_directory"
