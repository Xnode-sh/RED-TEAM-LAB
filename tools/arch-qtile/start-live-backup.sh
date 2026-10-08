#!/usr/bin/env bash
# This stage ONLY creates and verifies a backup. It never formats the HDD.
set -euo pipefail
[[ $EUID -eq 0 && -d /run/archiso ]] || { echo 'Run as root in the booted Arch Live environment.' >&2; exit 1; }
source /etc/os-release
[[ "$ID" == arch ]] || { echo 'Expected Arch Live.' >&2; exit 1; }
rig_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
rig_source=/mnt/debian
rig_destination=/mnt/rig-backup
rig_debian_uuid=19fb6bca-4430-4e9f-be15-5a509c25c3ff
rig_debian_device=$(readlink -f "/dev/disk/by-uuid/$rig_debian_uuid")
rig_usb_device=$(readlink -f /dev/disk/by-label/Ventoy)
[[ -b "$rig_debian_device" && -b "$rig_usb_device" ]] || { echo 'Expected Debian/USB filesystems not found.' >&2; exit 1; }
mkdir -p "$rig_source" "$rig_destination"
if ! mountpoint -q "$rig_source"; then
    mount -o ro "$rig_debian_device" "$rig_source"
fi
[[ "$(findmnt -n -o SOURCE --target "$rig_source")" == "$rig_debian_device" ]] || { echo 'Unexpected source mount.' >&2; exit 1; }
if ! mountpoint -q "$rig_destination"; then
    mount "$rig_usb_device" "$rig_destination"
fi
[[ "$(findmnt -n -o SOURCE --target "$rig_destination")" == "$rig_usb_device" ]] || { echo 'Unexpected backup mount.' >&2; exit 1; }
command -v python3 >/dev/null
rig_marker=$(mktemp /tmp/rig-backup-start.XXXXXX)
export GPG_TTY=$(tty)
bash "$rig_directory/backup-live.sh" "$rig_source" "$rig_destination" --migration
mapfile -t rig_archives < <(find "$rig_destination" -maxdepth 2 -type f -name SHA256SUMS -newer "$rig_marker" -printf '%h\n')
[[ ${#rig_archives[@]} -eq 1 ]] || { echo 'Cannot uniquely identify completed backup.' >&2; exit 1; }
rig_backup=${rig_archives[0]}
(cd "$rig_backup" && sha256sum -c SHA256SUMS)
python3 "$rig_directory/verify-backup.py" "$rig_source" "$rig_backup/debian-root.tar.gpg"
printf '%s\n' 'Archive decrypted completely; original project/Codex/GGUF sample hashes matched.' \
    > "$rig_backup/RESTORE-CHECK-PASSED.txt"
sync
echo "VERIFIED BACKUP: $rig_backup"
echo 'HDD remains intact. Installation is a separate next stage.'
