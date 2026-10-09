#!/usr/bin/env python3
"""Start the local server once, wait for readiness, and open a Kitty terminal chat."""
import fcntl
import json
import os
import shutil
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / 'runtime'
URL = 'http://127.0.0.1:8087'

def ready():
    try:
        with urllib.request.urlopen(URL + '/health', timeout=2) as r:
            return json.load(r).get('status') == 'ok'
    except (OSError, ValueError):
        return False

def ours(pid):
    try:
        return Path(f'/proc/{pid}/exe').resolve() == ROOT / 'llama.cpp/build/bin/llama-server'
    except OSError:
        return False

def ensure():
    RUNTIME.mkdir(exist_ok=True)
    process = None
    with (RUNTIME/'launch.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pidfile = RUNTIME/'server.pid'
        pid = int(pidfile.read_text()) if pidfile.exists() and pidfile.read_text().strip().isdigit() else 0
        if ready():
            if not pid or not ours(pid):
                raise RuntimeError('Port 8087 belongs to another server; not using it.')
            return
        if not pid or not ours(pid):
            with (RUNTIME/'server.log').open('a') as log:
                process = subprocess.Popen(['bash', str(ROOT/'server.sh')], stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True,
                                           cwd=ROOT)
            pidfile.write_text(str(process.pid))
            pid = process.pid
        for _ in range(240):
            if ready():
                return
            if (process is not None and process.poll() is not None) or not Path(f'/proc/{pid}').exists():
                raise RuntimeError('Server stopped. See tools/local-ai/runtime/server.log.')
            time.sleep(1)
        raise RuntimeError('Model is still loading. See runtime/server.log.')

if __name__ == '__main__':
    import sys
    try:
        if '--profile' in sys.argv:
            index = sys.argv.index('--profile') + 1
            profile = sys.argv[index] if index < len(sys.argv) else ''
            models = json.loads((ROOT/'models.json').read_text())
            if profile not in models:
                raise RuntimeError('Profiles: general, coder')
            subprocess.run(['python3', str(ROOT/'verify-model.py'), profile], check=True)
            (ROOT/'active-model.json').write_text(json.dumps(
                {'profile': profile, 'name': models[profile]['name']}, indent=2) + '\n')
            if '--restart' not in sys.argv:
                sys.argv.append('--restart')
        if '--restart' in sys.argv:
            subprocess.run(['python3', str(ROOT/'stop.py')], check=True)
            for _ in range(30):
                pidfile = RUNTIME/'server.pid'
                pid = int(pidfile.read_text()) if pidfile.exists() and pidfile.read_text().strip().isdigit() else 0
                if not pid or not ours(pid):
                    break
                time.sleep(1)
        ensure()
        print('Local AI ready:', URL, flush=True)
        if '--no-browser' not in sys.argv:
            if '--browser' in sys.argv:
                subprocess.Popen(['xdg-open', URL], start_new_session=True)
            else:
                socket = 'unix:' + str(RUNTIME/'kitty.sock')
                command = ['python3', str(ROOT/'chat.py')]
                probe = subprocess.run(['kitty', '@', '--to', socket, 'ls'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if probe.returncode == 0:
                    subprocess.run(['kitty', '@', '--to', socket, 'launch',
                                    '--type=tab', '--tab-title=LAB AI', *command], check=True)
                    if shutil.which('i3-msg') and os.environ.get('I3SOCK'):
                        subprocess.run(['i3-msg', '[class="^rig-local-ai$"] focus'],
                                       stdout=subprocess.DEVNULL, check=False)
                else:
                    session = RUNTIME/'kitty-session.conf'
                    session.write_text('new_tab LAB AI\nlaunch python3 ' + str(ROOT/'chat.py') + '\n')
                    subprocess.Popen(['kitty', '--detach', '--config',
                                      str(Path.home()/'.config/kitty/rig.conf'),
                                      '--class', 'rig-local-ai', '--listen-on', socket,
                                      '-o', 'allow_remote_control=socket-only',
                                      '-o', 'tab_bar_min_tabs=1', '--session', str(session)],
                                     start_new_session=True)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        if '--no-browser' not in sys.argv:
            subprocess.run(['notify-send', 'RIG Local AI', str(error)], check=False)
        raise SystemExit(1)
