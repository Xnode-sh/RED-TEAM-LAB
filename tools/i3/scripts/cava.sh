#!/usr/bin/env bash
set -euo pipefail
exec kitty --hold --config "$HOME/.config/kitty/rig.conf" --class rig-cava \
    --title 'RIG / AUDIO' \
    cava -p "$HOME/.config/cava/config"
