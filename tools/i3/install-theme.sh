#!/usr/bin/env bash
set -euo pipefail
rig_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$rig_source"
exec > >(tee -a "$rig_source/theme-install.log") 2>&1
trap 'printf "\nInstallation stopped. See theme-install.log.\n"; read -r -p "Press Enter..."' ERR
rig_missing=()
for rig_package in polybar cava picom rofi feh librsvg2-bin pavucontrol; do
    if ! dpkg-query -W -f='${Status}' "$rig_package" 2>/dev/null | grep -q 'ok installed'; then
        rig_missing+=("$rig_package")
    fi
done
if (( ${#rig_missing[@]} )); then
    printf 'Enter your sudo password here to install the theme dependencies.\n'
    sudo apt-get install -y "${rig_missing[@]}"
fi
python3 "$rig_source/install-theme.py"
printf 'SUCCESS\n' > "$rig_source/theme-install.status"
if i3-msg -t get_version >/dev/null 2>&1; then
    i3-msg reload
    bash "$HOME/.config/i3/scripts/session.sh"
    printf '\nTheme activated. Super+Shift+v opens Cava.\n'
else
    printf '\nTheme ready. Log out and select i3 at the login screen.\n'
fi
read -r -p 'Press Enter to close...'
