#!/usr/bin/env bash
# Log the verified one-time boot selection, then reboot only on success.
set -uo pipefail
umask 077
rig_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mkdir -p "$rig_dir/downloads"
sudo bash "$rig_dir/boot-arch-next.sh" 2>&1 | tee "$rig_dir/downloads/boot-arch-next.log"
rig_status=${PIPESTATUS[0]}
printf '%s\n' "$rig_status" > "$rig_dir/downloads/boot-arch-next.exit"
if (( rig_status != 0 )); then
    printf '\nОшибка подготовки, код %s. Перезагрузка отменена.\n' "$rig_status"
    read -r -p 'Нажми Enter, чтобы закрыть. ' || true
    exit "$rig_status"
fi
printf '\nArch Live выбран. Перезагрузка через 15 секунд; Ctrl+C отменяет её.\n'
sleep 15
sudo systemctl reboot
