#!/usr/bin/env python3
"""Functional panel controls, using installed tools and Qtile IPC."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
from datetime import datetime
from panel import ipc

HOME = Path.home()
THEME = str(HOME/'.config/polybar/rig/rig.rasi')

def spawn(*args):
    subprocess.Popen(args, start_new_session=True)

def terminal(*args, title='RIG / SYSTEM'):
    spawn('kitty', '--config', str(HOME/'.config/kitty/rig.conf'), '--title', title, *args)

def menu(prompt, choices):
    result = subprocess.run(['rofi','-theme',THEME,'-dmenu','-i','-p',prompt],
                            input='\n'.join(choices), text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else ''

def window_menu():
    choices = ['Split direction', 'Floating / tiled', 'Fullscreen', 'Balance sizes',
               'Focus next', 'Focus previous']
    choice = menu('WINDOW', choices)
    commands = {'Split direction':('layout','toggle_split'), 'Floating / tiled':('window','toggle_floating'),
                'Fullscreen':('window','toggle_fullscreen'), 'Balance sizes':('layout','normalize'),
                'Focus next':('group','next_window'), 'Focus previous':('group','prev_window')}
    if choice in commands:
        obj, cmd = commands[choice]
        ipc(cmd, selectors=[(obj, None)])

def screenshot():
    directory = HOME/'Pictures/RED-TEAM-LAB'
    directory.mkdir(parents=True, exist_ok=True)
    file = directory/f'RIG-{datetime.now():%Y%m%d-%H%M%S}.png'
    subprocess.run(['scrot', str(file)], check=True)
    spawn('notify-send','RIG / SCREENSHOT',str(file))

def main():
    action = sys.argv[1]
    if action in ('apps','windows'):
        spawn('rofi','-theme',THEME,'-show','drun' if action == 'apps' else 'window')
    elif action == 'terminal':
        terminal(title='RIG / TERMINAL')
    elif action == 'files':
        spawn('thunar')
    elif action == 'browser':
        spawn('firefox')
    elif action == 'telegram':
        spawn('telegram-desktop')
    elif action == 'bluetooth':
        spawn('blueman-manager')
    elif action == 'lock':
        spawn('i3lock','--color','171923')
    elif action == 'monitor':
        terminal('htop')
    elif action == 'project':
        terminal('--directory',str(HOME/'RED-TEAM-LAB'),title='RIG / LAB')
    elif action == 'codex':
        terminal(str(HOME/'.local/bin/rig-codex'),'--last',title='RIG / CODEX')
    elif action == 'window-menu':
        window_menu()
    elif action == 'network':
        terminal('--hold','sh','-c','nmcli device status; printf "\\n"; nmcli general status',title='RIG / NETWORK')
    elif action == 'network-menu':
        choice = menu('NETWORK',['Network status','Wi-Fi on','Wi-Fi off'])
        if choice == 'Network status':
            terminal('--hold','nmcli','device','status',title='RIG / NETWORK')
        elif choice in ('Wi-Fi on','Wi-Fi off'):
            subprocess.run(['nmcli','radio','wifi','on' if choice.endswith('on') else 'off'],check=True)
    elif action == 'audio-menu':
        if shutil.which('pavucontrol'):
            spawn('pavucontrol')
        else:
            terminal('--hold','wpctl','status',title='RIG / AUDIO')
    elif action == 'mute':
        subprocess.run(['wpctl','set-mute','@DEFAULT_AUDIO_SINK@','toggle'],check=True)
    elif action in ('volume-up','volume-down'):
        subprocess.run(['wpctl','set-volume','-l','1','@DEFAULT_AUDIO_SINK@','5%+' if action.endswith('up') else '5%-'],check=True)
    elif action in ('bright-up','bright-down'):
        subprocess.run(['brightnessctl','set','+5%' if action.endswith('up') else '5%-'],check=True)
    elif action == 'screenshot':
        screenshot()
    elif action == 'help':
        terminal('less',str(HOME/'.config/polybar/rig/HOTKEYS.txt'),title='RIG / CONTROLS')
    elif action == 'power':
        choice = menu('SESSION',['Cancel','Log out','Reboot','Power off'])
        if choice in ('Log out','Reboot','Power off') and menu('Save work first',['Cancel',choice]) == choice:
            if choice == 'Log out':
                ipc('shutdown')
            else:
                subprocess.run(['systemctl','reboot' if choice == 'Reboot' else 'poweroff'],check=True)

if __name__ == '__main__':
    main()
