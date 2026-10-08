#!/usr/bin/env bash
set -euo pipefail
rig_i3_source="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
rig_i3_log="$rig_i3_source/setup.log"
exec > >(tee -a "$rig_i3_log") 2>&1
trap 'printf "\nSetup stopped. XFCE remains installed. See setup.log.\n"; read -r -p "Press Enter to close..."' ERR
printf 'Installing i3. Enter your sudo password here on the laptop.\n'
sudo apt-get install -y i3-wm i3status suckless-tools dex
mkdir -p "$HOME/.config/i3"
if [ -e "$HOME/.config/i3/config" ]; then
    cp -a "$HOME/.config/i3/config" "$HOME/.config/i3/config.backup-$(date +%Y%m%d-%H%M%S)"
fi
cp "$rig_i3_source/config" "$HOME/.config/i3/config"
i3 -C -c "$HOME/.config/i3/config"
test -f /usr/share/xsessions/i3.desktop
printf '\nSUCCESS: i3 installed and config validated.\n'
printf 'Save your work. Log out from XFCE, choose i3 at the login screen, then log in.\n'
printf 'Super+Enter: terminal; Super+d: launcher; Super+b: Firefox; Super+t: Telegram.\n'
printf 'Super+Shift+e: exit i3. XFCE is still available at the login screen.\n'
printf 'SUCCESS\n' > "$rig_i3_source/setup.status"
read -r -p 'Press Enter to close...'
