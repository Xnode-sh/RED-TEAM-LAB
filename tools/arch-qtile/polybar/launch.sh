#!/usr/bin/env bash
set -euo pipefail
rig_panel_dir="$HOME/.config/polybar/rig"
rig_runtime="${XDG_RUNTIME_DIR:-/tmp/rig-panel-$UID}/rig-polybar"
mkdir -p "$rig_runtime"
chmod 700 "$rig_runtime"
exec 9>"$rig_runtime/launch.lock"
flock -n 9 || exit 0
# Only stop our own panels, not unrelated Polybar instances.
for rig_name in control clock status telemetry; do
    if [[ -f "$rig_runtime/$rig_name.pid" ]]; then
        read -r rig_pid < "$rig_runtime/$rig_name.pid"
        if [[ "$rig_pid" =~ ^[0-9]+$ ]] && [[ "$(cat "/proc/$rig_pid/comm" 2>/dev/null || true)" == polybar ]]; then
            polybar-msg -p "$rig_pid" cmd quit >/dev/null 2>&1 || true
        fi
    fi
done
for rig_name in control clock status telemetry; do
    polybar -c "$rig_panel_dir/config.ini" "$rig_name" 9>&- >"$rig_runtime/$rig_name.log" 2>&1 &
    printf '%s\n' "$!" > "$rig_runtime/$rig_name.pid"
done
python "$rig_panel_dir/shape.py" >"$rig_runtime/shape.log" 2>&1
