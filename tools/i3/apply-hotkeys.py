#!/usr/bin/env python3
"""Apply only keyboard bindings, their dispatcher, and local help with a backup."""
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

source = Path(__file__).resolve().parent
target = Path.home() / '.config/i3'
backup = Path.home() / '.config/rig-backups' / ('hotkeys-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
subprocess.run(['i3', '-C', '-c', str(source / 'config')], check=True)
for src, dst in [('config', 'config'), ('hotkeys.txt', 'hotkeys.txt'), ('scripts/actions.sh', 'scripts/actions.sh')]:
    destination = target / dst
    if destination.exists():
        saved = backup / 'i3' / dst
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, saved)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / src, destination)
    if dst.endswith('.sh'):
        destination.chmod(0o755)
result = subprocess.run(['i3-msg', 'reload'], check=True, capture_output=True, text=True)
print(result.stdout.strip())
print('Backup:', backup)
print('Hotkeys applied. Super+F1 opens the shortcut list.')
