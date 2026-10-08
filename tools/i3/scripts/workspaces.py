#!/usr/bin/env python3
"""Event-driven i3 workspace buttons; render all five without creating empty workspaces."""
import json
import subprocess
import time

ICONS = {1: '', 2: '', 3: '', 4: '', 5: ''}

def render():
    result = subprocess.run(['i3-msg', '-t', 'get_workspaces'],
                            capture_output=True, text=True, timeout=3, check=True)
    spaces = json.loads(result.stdout)
    by_number = {s['num']: s for s in spaces}
    buttons = []
    for number, icon in ICONS.items():
        space = by_number.get(number, {})
        focused = space.get('focused', False)
        color = '#ff426a' if space.get('urgent') else '#36e2ce' if focused else '#e6edf5' if space else '#77849f'
        style = '%{B#252d40}%{u#36e2ce}%{+u}' if focused else ''
        reset = '%{-u}%{B-}' if focused else ''
        buttons.append(f'%{{A1:i3-msg workspace number {number}:}}{style}%{{F{color}}}  {icon} {number}  %{{F-}}{reset}%{{A}}')
    # Nonstandard workspaces remain visible and accessible via normal i3 shortcuts.
    extras = [s for s in spaces if s['num'] not in ICONS]
    if extras:
        buttons.append('%{F#f3c677} +' + str(len(extras)) + '%{F-}')
    print(' '.join(buttons), flush=True)

while True:
    subscriber = None
    try:
        subscriber = subprocess.Popen(['i3-msg', '-t', 'subscribe', '-m', '["workspace"]'],
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                      text=True)
        render()
        for event in subscriber.stdout:
            if '"change"' in event:
                render()
    except (OSError, ValueError, subprocess.SubprocessError):
        print('1  2  3  4  5', flush=True)
    finally:
        if subscriber is not None and subscriber.poll() is None:
            subscriber.terminate()
            try:
                subscriber.wait(timeout=2)
            except subprocess.TimeoutExpired:
                subscriber.kill()
                subscriber.wait()
    time.sleep(2)
