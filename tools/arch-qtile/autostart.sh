#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
export RIG_CAPTURE_SYSTEM_FFMPEG=1
setxkbmap -layout us,ru -option grp:alt_shift_toggle
[[ ! -f "$HOME/.config/qtile/wallpaper.png" ]] || feh --no-fehbg --bg-fill "$HOME/.config/qtile/wallpaper.png"
rig_start_once() {
    pgrep -u "$(id -u)" -x "$1" >/dev/null || "$@" &
}
rig_start_once picom --config "$HOME/.config/picom/picom.conf"
rig_start_once dunst
rig_start_once nm-applet
rig_start_once xfce4-power-manager
if [[ -x /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 ]]; then
    pgrep -u "$(id -u)" -f '^/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1$' >/dev/null || \
        /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
fi
