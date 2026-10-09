#!/usr/bin/env python3
"""Apply reversible workstation defaults after installing packages-workstation.txt."""
from pathlib import Path
from datetime import datetime
import configparser
import shutil
import subprocess

root = Path(__file__).resolve().parent
home = Path.home()
backup = home/'.config/rig-backups'/('workstation-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True)

def save(path):
    if path.exists():
        relative = path.relative_to(home)
        target = backup/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)

for source,target in [
    (root/'minimal-config.py',home/'.config/qtile/config.py'),
    (root/'minimal-autostart.sh',home/'.config/qtile/autostart.sh'),
    (root/'picom-minimal.conf',home/'.config/picom/rig-light.conf'),
    (root/'polybar/actions.py',home/'.config/polybar/rig/actions.py'),
    (root/'polybar/dropdown.py',home/'.config/polybar/rig/dropdown.py')]:
    save(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)

for version in ('gtk-3.0','gtk-4.0'):
    path=home/'.config'/version/'settings.ini'
    save(path)
    config=configparser.ConfigParser(interpolation=None)
    if path.exists():
        config.read(path)
    if not config.has_section('Settings'):
        config.add_section('Settings')
    config['Settings'].update({'gtk-theme-name':'Adwaita-dark','gtk-icon-theme-name':'Papirus-Dark',
                              'gtk-font-name':'DejaVu Sans 10','gtk-application-prefer-dark-theme':'true'})
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w') as file:
        config.write(file)

save(home/'.config/mimeapps.list')
save(home/'.local/share/applications/mimeapps.list')
defaults = {
    'firefox.desktop':['x-scheme-handler/http','x-scheme-handler/https','text/html','application/pdf'],
    'thunar.desktop':['inode/directory'],
    'org.xfce.mousepad.desktop':['text/plain'],
    'org.xfce.ristretto.desktop':['image/png','image/jpeg','image/webp'],
    'mpv.desktop':['video/mp4','video/x-matroska','audio/mpeg','audio/flac'],
}
for app,types in defaults.items():
    subprocess.run(['xdg-mime','default',app,*types],check=True)
subprocess.run(['xdg-settings','set','default-web-browser','firefox.desktop'],check=True)
for key,value in [('color-scheme','prefer-dark'),('icon-theme','Papirus-Dark')]:
    subprocess.run(['gsettings','set','org.gnome.desktop.interface',key,value],check=True)
if not (home/'.bashrc').exists():
    shutil.copy2('/etc/skel/.bashrc',home/'.bashrc')
subprocess.run(['qtile','cmd-obj','-o','root','-f','reload_config'],check=True)
for command in ('picom --config '+str(home/'.config/picom/rig-light.conf'),'blueman-applet'):
    name=command.split()[0]
    if subprocess.run(['pgrep','-u',str(__import__('os').getuid()),'-x',name],stdout=subprocess.DEVNULL).returncode:
        subprocess.run(['qtile','cmd-obj','-o','root','-f','spawn','-a',command],check=True)
print('Workstation defaults applied; backup:',backup)
