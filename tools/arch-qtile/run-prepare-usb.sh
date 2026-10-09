#!/usr/bin/env bash
# Local terminal wrapper: sudo reads the password from the terminal, not chat.
set -uo pipefail
umask 077
rig_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mkdir -p "$rig_directory/downloads"
sudo bash "$rig_directory/prepare-usb.sh" 2>&1 | tee "$rig_directory/downloads/usb-preparation.log"
rig_status=${PIPESTATUS[0]}
printf '%s\n' "$rig_status" > "$rig_directory/downloads/usb-preparation.exit"
printf '\nPreparation exit code: %s\n' "$rig_status"
read -r -p 'Press Enter to close this terminal. ' || true
exit "$rig_status"
