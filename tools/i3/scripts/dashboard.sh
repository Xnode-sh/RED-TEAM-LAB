#!/usr/bin/env bash
set -euo pipefail
printf '\033[1;36mRIG / SYSTEM OVERVIEW\033[0m\n\n'
uptime
printf '\nMEMORY\n'
free -h
printf '\nFILESYSTEMS\n'
df -h / "$HOME"
printf '\nTEMPERATURES\n'
sensors || true
printf '\nAUDIO SERVER\n'
pactl info | sed -n '/Server Name:/p; /Default Sink:/p'
printf '\nNETWORK\n'
LC_ALL=C nmcli -t -f TYPE,STATE device || true
printf '\nThis view reads system state. Close the window when finished.\n'
