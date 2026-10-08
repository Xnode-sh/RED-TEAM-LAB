#!/usr/bin/env python3
"""Install the reviewed theme with a timestamped backup; never delete user files."""
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

source = Path(__file__).resolve().parent
config = Path.home() / '.config'
backup = config / 'rig-backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
files = {
    'config': 'i3/config',
    'hotkeys.txt': 'i3/hotkeys.txt',
    'polybar/config.ini': 'polybar/config.ini',
    'picom/picom.conf': 'picom/picom.conf',
    'cava/config': 'cava/config',
    'kitty/rig.conf': 'kitty/rig.conf',
    'rofi/rig.rasi': 'rofi/rig.rasi',
    'scripts/session.sh': 'i3/scripts/session.sh',
    'scripts/cava.sh': 'i3/scripts/cava.sh',
    'scripts/status.py': 'i3/scripts/status.py',
    'scripts/actions.sh': 'i3/scripts/actions.sh',
    'scripts/dashboard.sh': 'i3/scripts/dashboard.sh',
    'scripts/workspaces.py': 'i3/scripts/workspaces.py',
    'scripts/traffic.py': 'i3/scripts/traffic.py',
}
for original, target in files.items():
    dest = config / target
    if dest.exists():
        saved = backup / target
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, saved)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / original, dest)
    if target.startswith('i3/scripts/'):
        dest.chmod(0o755)

wallpaper = config / 'i3/wallpaper.png'
if wallpaper.exists():
    saved = backup / 'i3/wallpaper.png'
    saved.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wallpaper, saved)
subprocess.run(['rsvg-convert', str(source / 'wallpapers/rig.svg'),
                '-o', str(wallpaper)], check=True)
print('Backup:', backup if backup.exists() else 'no previous files')
subprocess.run(['i3', '-C', '-c', str(config / 'i3/config')], check=True)
print('Theme installed; i3 configuration validated.')
