#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
if command -v picom >/dev/null && [[ -f "$HOME/.config/picom/rig-light.conf" ]]; then
    pgrep -u "$(id -u)" -x picom >/dev/null || picom --config "$HOME/.config/picom/rig-light.conf" &
fi
setxkbmap -layout us,ru -option grp:alt_shift_toggle
for rig_app in dunst nm-applet xfce4-power-manager; do
    pgrep -u "$(id -u)" -x "$rig_app" >/dev/null || "$rig_app" &
done
if command -v blueman-applet >/dev/null; then
    pgrep -u "$(id -u)" -x blueman-applet >/dev/null || blueman-applet &
fi
if [[ -x /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 ]]; then
    /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
fi
kitty --config "$HOME/.config/kitty/rig.conf" &
if command -v polybar >/dev/null && [[ -f "$HOME/.config/polybar/rig/launch.sh" ]]; then
    bash "$HOME/.config/polybar/rig/launch.sh" &
fi
