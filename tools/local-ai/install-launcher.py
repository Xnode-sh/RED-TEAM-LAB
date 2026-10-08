#!/usr/bin/env python3
"""Add a local application shortcut; no background autostart or system service."""
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parent
backup_root = Path.home()/'.config/rig-backups'/('local-ai-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
app = Path.home()/'.local/share/applications/rig-local-ai.desktop'
if app.exists():
    backup = app.with_name('rig-local-ai.desktop.backup-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    shutil.copy2(app, backup)
app.parent.mkdir(parents=True, exist_ok=True)
app.write_text(f'''[Desktop Entry]
Type=Application
Name=RIG Local AI
Name[ru]=RIG — локальный AI
Comment=Qwen3.5-4B on this laptop
Exec=/usr/bin/python3 "{root}/launch.py"
Icon=utilities-terminal
Terminal=false
Categories=Development;Utility;
Actions=Stop;

[Desktop Action Stop]
Name=Stop local AI
Name[ru]=Остановить локальный AI
Exec=/usr/bin/python3 "{root}/stop.py"
''')
if shutil.which('update-desktop-database'):
    subprocess.run(['update-desktop-database', str(app.parent)], check=True)
print('Application shortcut installed:', app)
i3_source = root.parent/'i3'
if shutil.which('i3-msg') and (Path.home()/'.config/i3/config').exists():
    subprocess.run(['i3', '-C', '-c', str(i3_source/'config')], check=True)
    for src, dst in [('config', 'i3/config'), ('hotkeys.txt', 'i3/hotkeys.txt'),
                     ('scripts/actions.sh', 'i3/scripts/actions.sh'),
                     ('scripts/status.py', 'i3/scripts/status.py'),
                     ('scripts/capture.py', 'i3/scripts/capture.py'),
                     ('polybar/config.ini', 'polybar/config.ini')]:
        destination = Path.home()/'.config'/dst
        if destination.exists():
            saved = backup_root/dst
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, saved)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(i3_source/src, destination)
        if src.endswith('.sh'):
            destination.chmod(0o755)
    subprocess.run(['i3-msg', 'reload'], check=True)
    keyboard = subprocess.run(['setxkbmap', '-query'], capture_output=True, text=True, check=True).stdout
    if 'us,ru' not in keyboard or 'grp:alt_shift_toggle' not in keyboard:
        subprocess.run(['setxkbmap', '-layout', 'us,ru', '-option', 'grp:alt_shift_toggle'], check=True)
    # Reload does not run exec_always: refresh the owned panels explicitly.
    subprocess.run(['i3-msg', 'exec --no-startup-id ~/.config/i3/scripts/session.sh'], check=True)
    print('Super+Shift+A and AI panel button installed. Backup:', backup_root)
