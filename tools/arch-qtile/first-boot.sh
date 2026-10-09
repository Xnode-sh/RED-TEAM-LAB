#!/usr/bin/env bash
set -euo pipefail
umask 077
rig_evidence=/srv/rig-data/var/lib/rig-arch/evidence
mkdir -p "$rig_evidence"
exec >> "$rig_evidence/first-boot.log" 2>&1
rig_failed() {
    printf '%s\n' 'FAILED; Debian remains the saved/default boot.' > "$rig_evidence/first-boot.status"
    sync
}
trap rig_failed ERR
date -u
source /etc/os-release
[[ $ID == arch && ! -d /run/archiso ]]
[[ $(findmnt -nro UUID /) == "$(cat "$rig_evidence/arch-root.uuid")" ]]
systemctl is-active NetworkManager
systemctl is-active lightdm
[[ -d /home/red-team-lab/RED-TEAM-LAB/.git ]]
[[ $(id -u red-team-lab) == 1000 ]]
rig_graphical=false
for ((rig_attempt=0; rig_attempt<90; rig_attempt++)); do
    if pgrep -u 1000 -f 'qtile start' >/dev/null; then
        rig_graphical=true
        break
    fi
    sleep 2
done
$rig_graphical
nm-online -q --timeout=30
for ((rig_attempt=0; rig_attempt<15; rig_attempt++)); do
    [[ ! -S /run/user/1000/pipewire-0 ]] || break
    sleep 2
done
[[ -S /run/user/1000/pipewire-0 ]]
runuser -u red-team-lab -- env HOME=/home/red-team-lab XDG_RUNTIME_DIR=/run/user/1000 /home/red-team-lab/.local/bin/codex --version
runuser -u red-team-lab -- env HOME=/home/red-team-lab XDG_RUNTIME_DIR=/run/user/1000 wpctl status
lsmod | awk '$1 == "i915" {found=1} END {exit !found}'
grub-editenv /srv/rig-data/boot/grub/grubenv set saved_entry=rig-arch-installed
printf '%s\n' 'Arch root, NetworkManager, LightDM, Qtile process, Codex executable, PipeWire and Intel driver checked.' > "$rig_evidence/first-boot.ok"
printf '%s\n' 'BOOTED_ARCH_QTILE; manual hardware acceptance pending.' > "$rig_evidence/first-boot.status"
sync
if command -v notify-send >/dev/null; then
    runuser -u red-team-lab -- env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
        notify-send 'RIG: Arch + Qtile' 'Основная проверка пройдена. Super+Enter — терминал.' || true
fi
