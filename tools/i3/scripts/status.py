#!/usr/bin/env python3
"""Short, private status: no SSIDs, addresses, or hostnames on the panel."""
import pathlib
import subprocess
import sys
import os

def read(path):
    try:
        return path.read_text().strip()
    except OSError:
        return ""

def battery():
    batteries = [p for p in pathlib.Path('/sys/class/power_supply').glob('*')
                 if read(p / 'type') == 'Battery']
    if not batteries:
        return ' AC'
    p = batteries[0]
    capacity = read(p / 'capacity')
    state = read(p / 'status')
    prefix = '' if state == 'Charging' else ''
    text = f'{prefix} {capacity}%' if capacity.isdigit() else 'BAT --'
    if capacity.isdigit() and int(capacity) <= 20 and state == 'Discharging':
        return '%{F#ff426a}' + text + '%{F-}'
    return text

def network():
    try:
        r = subprocess.run(['nmcli', '-t', '-f', 'TYPE,STATE', 'device'],
                           capture_output=True, text=True, timeout=2, check=True,
                           env={**os.environ, 'LC_ALL': 'C'})
        active = {line.split(':', 1)[0] for line in r.stdout.splitlines()
                  if line.endswith(':connected')}
        if 'wifi' in active:
            return ' WiFi'
        if 'ethernet' in active:
            return ' LAN'
        return '%{F#ff426a} OFFLINE%{F-}'
    except (OSError, subprocess.SubprocessError):
        return 'NET --'

def temperature():
    values = []
    for hwmon in pathlib.Path('/sys/class/hwmon').glob('*'):
        if read(hwmon / 'name') not in ('coretemp', 'k10temp', 'zenpower'):
            continue
        for p in hwmon.glob('temp*_input'):
            raw = read(p)
            if raw.isdigit() and 0 < int(raw) < 150000:
                values.append(int(raw) / 1000)
    if not values:
        return ' --'
    temp = max(values)
    color = '#ff426a' if temp >= 85 else '#f3c677' if temp >= 70 else '#36e2ce'
    return f'%{{F{color}}} {temp:.0f}°C%{{F-}}'

def gpu():
    cards = pathlib.Path('/sys/class/drm').glob('card[0-9]*')
    device = next((p / 'device' for p in cards
                   if read(p / 'device/vendor') == '0x10de'), None)
    if device is None:
        return 'GPU --'
    name = 'GT740M' if read(device / 'device') == '0x1292' else 'NVIDIA'
    if read(device / 'power/runtime_status') == 'suspended':
        return f'%{{F#77849f}}GPU {name} SLEEP%{{F-}}'
    values = []
    for sensor in (device / 'hwmon').glob('hwmon*/temp*_input'):
        raw = read(sensor)
        if raw.isdigit() and 0 < int(raw) < 150000:
            values.append(int(raw) / 1000)
    if not values:
        return f'GPU {name} --°C'
    temp = max(values)
    color = '#ff426a' if temp >= 85 else '#f3c677' if temp >= 70 else '#36e2ce'
    return f'%{{F{color}}}GPU {name} {temp:.0f}°C%{{F-}}'

if __name__ == '__main__':
    functions = {'network': network, 'battery': battery, 'temperature': temperature, 'gpu': gpu}
    if len(sys.argv) != 2 or sys.argv[1] not in functions:
        raise SystemExit('usage: status.py network|battery|temperature|gpu')
    print(functions[sys.argv[1]]())
