#!/usr/bin/env bash
set -euo pipefail
rig_runtime="${XDG_RUNTIME_DIR:-/tmp}/rig-i3-$UID"
mkdir -p "$rig_runtime"
chmod 700 "$rig_runtime"
exec 9>"$rig_runtime/session.lock"
flock 9

# Restart only the services started by this configuration.
stop_owned() {
    local name="$1" executable="${2:-$1}" pid=""
    if [[ -r "$rig_runtime/$name.pid" ]]; then
        read -r pid < "$rig_runtime/$name.pid" || true
        if [[ "$pid" =~ ^[0-9]+$ ]] && [[ -O "/proc/$pid" ]] &&
           [[ "$(basename "$(readlink "/proc/$pid/exe" 2>/dev/null || true)")" == "$executable" ]]; then
            kill "$pid" 2>/dev/null || true
            for _ in {1..20}; do
                kill -0 "$pid" 2>/dev/null || break
                sleep 0.1
            done
        fi
    fi
}

stop_owned polybar
stop_owned polybar-telemetry polybar
polybar --config="$HOME/.config/polybar/config.ini" rig > "$rig_runtime/polybar.log" 2>&1 9>&- &
printf '%s\n' "$!" > "$rig_runtime/polybar.pid"
polybar --config="$HOME/.config/polybar/config.ini" telemetry > "$rig_runtime/polybar-telemetry.log" 2>&1 9>&- &
printf '%s\n' "$!" > "$rig_runtime/polybar-telemetry.pid"

stop_owned picom
# Never compete with an unrelated compositor.
if ! pgrep -u "$UID" -x picom >/dev/null; then
    picom --config "$HOME/.config/picom/picom.conf" > "$rig_runtime/picom.log" 2>&1 9>&- &
    printf '%s\n' "$!" > "$rig_runtime/picom.pid"
fi
if [[ -r "$HOME/.config/i3/wallpaper.png" ]]; then
    feh --no-fehbg --bg-fill "$HOME/.config/i3/wallpaper.png"
fi
