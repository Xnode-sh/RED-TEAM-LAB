#!/usr/bin/env bash
set -uo pipefail
umask 077
rig_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
sudo bash "$rig_dir/prepare-hdd-live.sh" 2>&1 | tee "$rig_dir/downloads/hdd-live-preparation.log"
rig_status=${PIPESTATUS[0]}
printf '%s\n' "$rig_status" > "$rig_dir/downloads/hdd-live-preparation.exit"
printf '\nExit code: %s\n' "$rig_status"
read -r -p 'Press Enter to close. ' || true
exit "$rig_status"
