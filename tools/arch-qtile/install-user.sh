#!/usr/bin/env bash
# Run as the restored user on installed Arch, outside the Live environment.
set -euo pipefail
umask 077
[[ $EUID -ne 0 ]] || { echo 'Run as red-team-lab, not root.' >&2; exit 1; }
source /etc/os-release
[[ "$ID" == arch && ! -d /run/archiso ]] || { echo 'Requires installed Arch.' >&2; exit 1; }
[[ "$(id -un)" == red-team-lab ]] || { echo 'Preserve username red-team-lab for paths and session history.' >&2; exit 1; }
rig_project="$HOME/RED-TEAM-LAB"
rig_sources="$rig_project/tools/arch-qtile"
rig_backup="$HOME/.config/rig-backups/arch-qtile-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$rig_backup" "$HOME/.config/qtile" "$HOME/.config/kitty" "$HOME/.config/picom" "$HOME/.local/bin" "$HOME/.local/share/applications"
for rig_item in qtile/config.py qtile/autostart.sh kitty/rig.conf picom/picom.conf; do
    if [[ -e "$HOME/.config/$rig_item" ]]; then
        mkdir -p "$rig_backup/$(dirname "$rig_item")"
        cp -a -- "$HOME/.config/$rig_item" "$rig_backup/$rig_item"
    fi
done
install -m 600 "$rig_sources/config.py" "$HOME/.config/qtile/config.py"
install -m 700 "$rig_sources/autostart.sh" "$HOME/.config/qtile/autostart.sh"
install -m 600 "$rig_project/tools/i3/kitty/rig.conf" "$HOME/.config/kitty/rig.conf"
install -m 600 "$rig_project/tools/i3/picom/picom.conf" "$HOME/.config/picom/picom.conf"
if [[ -f "$HOME/.config/i3/wallpaper.png" ]]; then
    cp -n -- "$HOME/.config/i3/wallpaper.png" "$HOME/.config/qtile/wallpaper.png"
fi
# Keep the observed Codex version for the first migration validation.
npm install --global --prefix "$HOME/.local" @openai/codex@0.160.1
if [[ -e "$HOME/.local/bin/rig-codex" ]]; then
    cp -a "$HOME/.local/bin/rig-codex" "$rig_backup/rig-codex"
fi
cat > "$HOME/.local/bin/rig-codex" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/RED-TEAM-LAB"
exec "$HOME/.local/bin/codex" resume "$@"
EOF
chmod 700 "$HOME/.local/bin/rig-codex"
if [[ -e "$HOME/.local/share/applications/rig-codex.desktop" ]]; then
    cp -a "$HOME/.local/share/applications/rig-codex.desktop" "$rig_backup/rig-codex.desktop"
fi
cat > "$HOME/.local/share/applications/rig-codex.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=RIG — Codex / RED TEAM LAB
Exec=kitty --config $HOME/.config/kitty/rig.conf $HOME/.local/bin/rig-codex
Icon=utilities-terminal
Terminal=false
Categories=Development;
EOF
if ! rg -q '^export PATH="\$HOME/\.local/bin:\$PATH"$' "$HOME/.profile" 2>/dev/null; then
    [[ ! -f "$HOME/.profile" ]] || cp -a "$HOME/.profile" "$rig_backup/profile"
    printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$HOME/.profile"
fi
xdg-user-dirs-update
echo "Prepared Qtile, Kitty and Codex; previous configs: $rig_backup"
echo 'Check: ~/.local/bin/codex --version; ~/.local/bin/codex login status'
echo 'Credentials were not printed. OS keyring authentication may require a new login.'
