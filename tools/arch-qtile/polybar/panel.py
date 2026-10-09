#!/usr/bin/env python3
"""Qtile IPC buttons and bounded, real system telemetry for Polybar."""
import os
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime

HOME = Path.home()
HERE = Path(__file__).resolve().parent
CYAN, RED, MUTED, WHITE, AMBER = '#89ddca', '#f08095', '#8794b0', '#eff4ff', '#ffc774'
GROUPS = ['CODE', 'LAB', 'COMMS', 'SYS', '5', '6', '7', '8', '9', '10']
ICONS = json.loads((HERE/'lucide.json').read_text())

def icon(name):
    return '%{T3}'+ICONS[name]+'%{T-}'

def ipc(command, *args, selectors=None, **kwargs):
    from libqtile.ipc import Client, find_sockfile
    status, result = Client(find_sockfile()).send((selectors or [], command, args, kwargs, False))
    if status != 0:
        raise RuntimeError(result)
    return result

def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return ''

def run(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=3,
                          check=True, env={**os.environ, 'LC_ALL': 'C'}).stdout.strip()

def color(text, shade=CYAN):
    for old,name in {'':'volume-x','':'volume-2','':'thermometer','':'cpu',
                     '':'hard-drive','':'wifi','':'ethernet-port','':'wifi-off','☀':'sun'}.items():
        text=text.replace(old,icon(name))
    return f'%{{F{shade}}}{text}%{{F-}}'

def meter(value):
    n = max(0, min(5, round(value / 20)))
    return color('━' * n, RED if value >= 90 else CYAN) + color('─' * (5-n), MUTED)

def workspaces():
    groups = ipc('get_groups')
    current = ipc('get_screens')[0]['group']
    number = GROUPS.index(current) + 1
    return color(f'{number:02d}', '#b4a4ed') + ' ' + icon('chevron-down')

def audio():
    value = run('wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@')
    if 'MUTED' in value:
        return color(' MUTE', RED)
    return color(icon('volume-2'))

def thermal():
    values = []
    for hwmon in Path('/sys/class/hwmon').glob('*'):
        if read(hwmon / 'name') == 'coretemp':
            values.extend(int(read(p)) / 1000 for p in hwmon.glob('temp*_input') if read(p).isdigit())
    if not values:
        return color('TEMP --', MUTED)
    temp = max(values)
    return color(f' {temp:.0f}°C', RED if temp >= 85 else AMBER if temp >= 70 else CYAN)

def gpu():
    for card in Path('/sys/class/drm').glob('card[0-9]'):
        device = card / 'device'
        if read(device / 'vendor') != '0x10de':
            continue
        state = read(device / 'power/runtime_status')
        if state == 'suspended':
            return color(' SLEEP', MUTED)
        values = [int(read(p))/1000 for p in device.glob('hwmon/hwmon*/temp*_input') if read(p).isdigit()]
        return color(f' {max(values):.0f}°C' if values else ' ACTIVE', AMBER)
    return color('GPU --', MUTED)

def disk(path, label):
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize / 1024**3
    usage = 100 * (1 - st.f_bavail / max(1, st.f_blocks))
    return color(f' {label} {free:.0f}G', RED if usage > 90 else MUTED)

def network():
    result = run('nmcli', '-t', '-f', 'TYPE,STATE', 'device')
    kinds = {line.split(':')[0] for line in result.splitlines() if line.endswith(':connected')}
    return color(icon('wifi' if 'wifi' in kinds else 'ethernet-port' if 'ethernet' in kinds else 'wifi-off'), CYAN if kinds else RED)

def brightness():
    for p in Path('/sys/class/backlight').glob('*'):
        raw, maximum = read(p/'brightness'), read(p/'max_brightness')
        if raw.isdigit() and maximum.isdigit() and int(maximum):
            return color(f'☀ {int(raw)*100/int(maximum):.0f}%', AMBER)
    return color('LIGHT --', MUTED)

def stream(mode):
    previous = None
    while True:
        try:
            if mode == 'cpu':
                numbers = list(map(int, read('/proc/stat').splitlines()[0].split()[1:9]))
                now = (sum(numbers), numbers[3] + numbers[4])
                if previous is None:
                    text = color('CPU ───── --', MUTED)
                else:
                    total, idle = now[0]-previous[0], now[1]-previous[1]
                    value = 100 * (1-idle/max(1,total))
                    text = icon('cpu') + color(f' {value:02.0f}%')
                previous = now
            elif mode == 'traffic':
                now = {}
                for p in Path('/sys/class/net').glob('*'):
                    if (p/'device').exists():
                        now[p.name] = (int(read(p/'statistics/rx_bytes')), int(read(p/'statistics/tx_bytes')))
                stamp = time.monotonic()
                values = [0, 0]
                if previous is not None:
                    old, start = previous
                    values = [sum(max(0, v[i]-old[k][i]) for k,v in now.items() if k in old) / max(.01, stamp-start) for i in (0,1)]
                def rate(v):
                    return f'{v/1024**2:.1f}M' if v >= 1024**2 else f'{v/1024:.0f}K'
                text = color(f'↓{rate(values[0])} ↑{rate(values[1])}', MUTED)
                previous = (now, stamp)
            else:
                text = workspaces()
            print(text, flush=True)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            print(color(f'{mode.upper()} --', MUTED), flush=True)
        time.sleep(1 if mode == 'workspaces' else 3)

def main():
    mode = sys.argv[1]
    if mode in ('workspace-next','workspace-prev'):
        ipc('next_group' if mode.endswith('next') else 'prev_group', selectors=[('screen',None)])
        return
    if mode == 'workspace':
        n = int(sys.argv[2])
        if 1 <= n <= len(GROUPS):
            ipc('toscreen', selectors=[('group', GROUPS[n-1])])
        return
    if mode in ('workspaces', 'cpu', 'traffic'):
        stream(mode)
        return
    if mode == 'memory':
        values = {key: int(value.split()[0]) for key,value in (line.split(':',1) for line in read('/proc/meminfo').splitlines())}
        used = (values['MemTotal']-values['MemAvailable']) / 1024**2
        print(f'{icon("database")} {color(f"{used:.1f}G")}')
        return
    if mode == 'clock':
        print(icon('clock')+'  '+datetime.now().strftime('%H:%M')+'  '+icon('chevron-down'))
        return
    modes = {'audio':audio, 'temperature':thermal, 'gpu':gpu, 'network':network,
             'root':lambda:disk('/', 'ROOT'), 'data':lambda:disk('/srv/rig-data', 'DATA'),
             'brightness':brightness,
             'uptime':lambda:color(f'UP {float(read("/proc/uptime").split()[0])/3600:.1f}h', MUTED)}
    try:
        print(modes[mode]())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print(color(f'{mode.upper()} --', MUTED))

if __name__ == '__main__':
    main()
