#!/usr/bin/env python3
"""PNG capture and owned X11 recording with an explicit visible REC indicator."""
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import time

ENGINE = Path.home()/'RED-TEAM-LAB/tools/i3/recorder-runtime'
USE_SYSTEM_FFMPEG = os.environ.get('RIG_CAPTURE_SYSTEM_FFMPEG') == '1' or not (ENGINE/'usr/bin/ffmpeg').exists()
FFMPEG = Path(shutil.which('ffmpeg') or '/usr/bin/ffmpeg').resolve() if USE_SYSTEM_FFMPEG else ENGINE/'usr/bin/ffmpeg'
FFPROBE = Path(shutil.which('ffprobe') or '/usr/bin/ffprobe').resolve() if USE_SYSTEM_FFMPEG else ENGINE/'usr/bin/ffprobe'
RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))/f'rig-capture-{os.getuid()}'
STATE = RUNTIME/'record.json'
ENV = dict(os.environ)
if not USE_SYSTEM_FFMPEG:
    ENV['LD_LIBRARY_PATH'] = str(ENGINE/'usr/lib/x86_64-linux-gnu')

def notify(text):
    subprocess.run(['notify-send', '-t', '3500', 'RIG / CAPTURE', text], check=False)

def folder(kind):
    result = subprocess.run(['xdg-user-dir', kind], capture_output=True, text=True, check=True)
    base = Path(result.stdout.strip())
    if base == Path.home() or not base.is_absolute():
        base = Path.home()/('Pictures' if kind == 'PICTURES' else 'Videos')
    destination = base/'RED-TEAM-LAB'
    destination.mkdir(parents=True, exist_ok=True)
    return destination

def state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}

def running(data):
    try:
        pid = int(data['pid'])
        return (Path(f'/proc/{pid}/exe').resolve() == FFMPEG and
                str(data['file']).encode() in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0'))
    except (OSError, ValueError, KeyError):
        return False

def screenshot(area=False):
    output = folder('PICTURES')/('screen-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.png')
    subprocess.run(['xfce4-screenshooter', '-r' if area else '-f', '-s', str(output)], check=True)
    if output.exists():
        notify('PNG сохранён: '+str(output))
        print(output)
    return output

def start():
    if not FFMPEG.exists():
        raise RuntimeError('FFmpeg не установлен: см. tools/i3/CAPTURE.md')
    if not os.environ.get('DISPLAY'):
        raise RuntimeError('Нет X11 DISPLAY')
    display = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, check=True)
    dimensions = re.search(r'current (\d+) x (\d+)', display.stdout)
    if not dimensions:
        raise RuntimeError('Не удалось определить размер экрана')
    size = 'x'.join(dimensions.groups())
    output = folder('VIDEOS')/('screen-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.mp4')
    command = ['nice', '-n', '10', str(FFMPEG), '-nostdin', '-hide_banner', '-loglevel', 'warning',
               '-n', '-thread_queue_size', '512', '-f', 'x11grab', '-framerate', '30',
               '-video_size', size, '-draw_mouse', '1', '-probesize', '32', '-analyzeduration', '0', '-i', os.environ['DISPLAY']]
    audio = False
    try:
        sink = subprocess.run(['pactl', 'get-default-sink'], capture_output=True, text=True, check=True, timeout=3).stdout.strip()
        sources = subprocess.run(['pactl', 'list', 'short', 'sources'], capture_output=True, text=True, check=True, timeout=3).stdout
        if sink+'.monitor' in [line.split()[1] for line in sources.splitlines() if len(line.split())>1]:
            command += ['-thread_queue_size', '512', '-f', 'pulse', '-probesize', '32', '-analyzeduration', '0', '-i', sink+'.monitor']
            audio = True
    except (OSError, subprocess.SubprocessError):
        pass
    command += ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '18', '-pix_fmt', 'yuv420p',
                '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-threads', '2']
    if audio:
        command += ['-c:a', 'aac', '-b:a', '192k']
    command += ['-r', '30', '-fps_mode', 'cfr', '-movflags', '+faststart', str(output)]
    with (RUNTIME/'record.log').open('w') as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log,
                                   stderr=log, env=ENV, start_new_session=True)
    data = {'pid':process.pid, 'file':str(output), 'started':time.time(), 'audio':audio}
    STATE.write_text(json.dumps(data))
    time.sleep(1)
    if process.poll() is not None:
        raise RuntimeError('Запись не запустилась. Журнал: '+str(RUNTIME/'record.log'))
    notify('Запись началась · '+('системный звук' if audio else 'без звука'))
    print('Recording:', output, flush=True)
    return data

def stop(data):
    os.kill(int(data['pid']), signal.SIGINT)
    for _ in range(100):
        if not running(data):
            break
        time.sleep(0.1)
    else:
        raise RuntimeError('Запись ещё завершает файл; повторно не запускайте')
    STATE.write_text('{}')
    result = subprocess.run([str(FFPROBE), '-v', 'error', '-show_entries', 'format=duration',
                             '-of', 'default=noprint_wrappers=1:nokey=1', data['file']],
                            capture_output=True, text=True, env=ENV)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError('Проверьте запись и журнал: '+str(RUNTIME/'record.log'))
    notify('Запись сохранена: '+data['file'])
    print('Saved:', data['file'], 'duration:', result.stdout.strip(), flush=True)

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv)>1 else 'status'
    if action in ('status', 'status-plain'):
        data = state()
        if running(data):
            seconds = max(0,int(time.time()-data['started']))
            value = f'REC {seconds//60:02d}:{seconds%60:02d}'
            print(value if action == 'status-plain' else f'%{{F#ff426a}} {value}%{{F-}}')
        else:
            print('REC OFF' if action == 'status-plain' else '%{F#36e2ce} REC%{F-}')
        sys.exit(0)
    try:
        RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
        if action in ('screenshot', 'area'):
            screenshot(action == 'area')
            sys.exit(0)
        if action == 'files':
            subprocess.Popen(['thunar', str(folder('VIDEOS'))], start_new_session=True)
            sys.exit(0)
        with (RUNTIME/'capture.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if action == 'toggle':
                data = state()
                stop(data) if running(data) else start()
            elif action == 'selftest':
                if running(state()):
                    raise RuntimeError('Есть активная запись; тест не запускается')
                screenshot()
                data = start()
                time.sleep(5)
                stop(data)
                result = subprocess.run([str(FFPROBE), '-v', 'error', '-show_streams',
                                         '-show_format', '-of', 'json', data['file']],
                                        capture_output=True, text=True, env=ENV, check=True)
                metadata = json.loads(result.stdout)
                print(json.dumps({'streams':[{k:s.get(k) for k in ('codec_type','codec_name','width','height','avg_frame_rate','nb_frames')} for s in metadata['streams']],
                                  'duration':metadata['format']['duration']},ensure_ascii=False))
            else:
                raise RuntimeError('Неизвестное действие')
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        notify(str(error))
        print(error, file=sys.stderr)
        sys.exit(1)
