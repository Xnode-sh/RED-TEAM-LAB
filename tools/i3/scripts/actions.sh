#!/usr/bin/env bash
set -euo pipefail
rig_rofi=(rofi -theme "$HOME/.config/rofi/rig.rasi")
case "${1:-}" in
    local-ai) exec python3 "$HOME/RED-TEAM-LAB/tools/local-ai/launch.py" ;;
    local-ai-stop) exec python3 "$HOME/RED-TEAM-LAB/tools/local-ai/stop.py" ;;
    apps) exec "${rig_rofi[@]}" -show drun ;;
    windows) exec "${rig_rofi[@]}" -show window ;;
    terminal) exec kitty --config "$HOME/.config/kitty/rig.conf" ;;
    files) exec thunar ;;
    browser) exec firefox-esr ;;
    telegram) exec "$HOME/RED-TEAM-LAB/tools/telegram-desktop/Telegram/Telegram" ;;
    cava)
        if i3-msg -t get_tree | python3 -c '
import json,sys
def found(n):
 return n.get("window_properties",{}).get("class")=="rig-cava" or any(found(c) for key in ("nodes","floating_nodes") for c in n.get(key,[]))
sys.exit(0 if found(json.load(sys.stdin)) else 1)'; then
            exec i3-msg '[class="^rig-cava$"] focus'
        fi
        exec "$HOME/.config/i3/scripts/cava.sh"
        ;;
    mixer) exec pavucontrol ;;
    network) exec nm-connection-editor ;;
    network-info)
        exec kitty --hold --config "$HOME/.config/kitty/rig.conf" --title 'RIG / NETWORK' \
            nmcli -f GENERAL.STATE,GENERAL.TYPE,GENERAL.CONNECTION,IP4.ADDRESS device show
        ;;
    dashboard) exec kitty --hold --config "$HOME/.config/kitty/rig.conf" --title 'RIG / SYSTEM' "$HOME/.config/i3/scripts/dashboard.sh" ;;
    display) exec xfce4-display-settings ;;
    power-settings) exec xfce4-power-manager-settings ;;
    screenshot-full) exec python3 "$HOME/.config/i3/scripts/capture.py" screenshot ;;
    screenshot-area) exec python3 "$HOME/.config/i3/scripts/capture.py" area ;;
    recording) exec python3 "$HOME/.config/i3/scripts/capture.py" toggle ;;
    recordings) exec python3 "$HOME/.config/i3/scripts/capture.py" files ;;
    screenshot-window) exec xfce4-screenshooter -w ;;
    help) exec kitty --config "$HOME/.config/kitty/rig.conf" --class rig-help \
        --title 'RIG / HOTKEYS — Q to close' less -R "$HOME/.config/i3/hotkeys.txt" ;;
    lock) exec light-locker-command --lock ;;
    power)
        rig_choice="$(printf '%s\n' 'Lock screen' 'Suspend' 'Log out' 'Reboot' 'Power off' | "${rig_rofi[@]}" -dmenu -i -p POWER)" || exit 0
        case "$rig_choice" in
            'Lock screen') exec light-locker-command --lock ;;
            Suspend) light-locker-command --lock; exec systemctl suspend ;;
            'Log out'|'Reboot'|'Power off')
                # These actions can interrupt work. A deliberate menu click is required.
                rig_confirm="$(printf '%s\n' 'Cancel' "$rig_choice" | "${rig_rofi[@]}" -dmenu -i -p 'Save your work first')" || exit 0
                [[ "$rig_confirm" == "$rig_choice" ]] || exit 0
                case "$rig_choice" in
                    'Log out') exec i3-msg exit ;;
                    Reboot) exec systemctl reboot ;;
                    'Power off') exec systemctl poweroff ;;
                esac
                ;;
        esac
        ;;
    *) printf 'Unknown panel action\n' >&2; exit 2 ;;
esac
