#!/usr/bin/env python3
"""A short, reproducible local smoke benchmark; no user conversation is used."""
import json
import sys
from pathlib import Path
import threading
import time
import urllib.request

root = Path(__file__).resolve().parent
pid = int((root/'runtime/server.pid').read_text())
samples = []
stop = threading.Event()

def sample():
    while not stop.is_set():
        temperatures = []
        for hwmon in Path('/sys/class/hwmon').glob('*'):
            try:
                if (hwmon/'name').read_text().strip() != 'coretemp':
                    continue
                temperatures.extend(int(p.read_text())/1000 for p in hwmon.glob('temp*_input'))
            except (OSError, ValueError):
                pass
        rss = 0
        try:
            for line in Path(f'/proc/{pid}/status').read_text().splitlines():
                if line.startswith('VmRSS:'):
                    rss = int(line.split()[1])/1024
        except OSError:
            pass
        samples.append({'rss_mib': rss, 'temperature_c': max(temperatures, default=0)})
        stop.wait(0.5)

monitor = threading.Thread(target=sample, daemon=True)
monitor.start()
results = []
cases = [
    ('linux', 'Кратко объясни поле available в free -h. Дай одну команду для просмотра памяти.', 96),
    ('code', 'Напиши функцию Python unique_keep_order(items), убирающую повторы чисел с сохранением порядка. Только код.', 128),
    ('arithmetic', 'Сколько будет 17 умножить на 23? Ответь только числом.', 16),
]
if '--coding' in sys.argv:
    cases = [
        ('deduplicate', 'Only Python code. Write unique_equal(items) returning a new list without duplicate values in original order. Items can be unhashable dictionaries and lists. Do not mutate the input.', 256),
        ('intervals', 'Only Python code. Write merge_intervals(intervals) returning sorted merged overlapping or touching [start,end] intervals. Input may be unsorted or empty; do not mutate the input.', 256),
    ]
try:
    for name, prompt, limit in cases:
        payload = {'model': 'rig-local', 'messages': [
            {'role':'system','content':(root/'system-prompt.txt').read_text()},
            {'role':'user','content':prompt}], 'stream':True,
            'stream_options':{'include_usage':True}, 'temperature':0.2,
            'max_tokens':limit, 'chat_template_kwargs':{'enable_thinking':False}}
        request = urllib.request.Request('http://127.0.0.1:8087/v1/chat/completions',
            data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        start = time.monotonic()
        first = None
        text = ''
        usage = {}
        timings = {}
        with urllib.request.urlopen(request,timeout=300) as response:
            for line in response:
                if not line.startswith(b'data: '):
                    continue
                data = line[6:].strip()
                if data == b'[DONE]':
                    break
                chunk = json.loads(data)
                content = chunk.get('choices',[{}])[0].get('delta',{}).get('content','') if chunk.get('choices') else ''
                if content:
                    if first is None:
                        first = time.monotonic()
                    text += content
                if chunk.get('usage'):
                    usage = chunk['usage']
                if chunk.get('timings'):
                    timings = chunk['timings']
        end = time.monotonic()
        item = {'case':name, 'first_token_seconds':round(first-start,2) if first else None,
                'total_seconds':round(end-start,2), 'usage':usage, 'timings':timings, 'answer':text}
        if usage.get('completion_tokens') and first and end>first:
            item['observed_generation_tokens_per_second'] = round(max(0,usage['completion_tokens']-1)/(end-first),2)
        results.append(item)
        print(json.dumps(item,ensure_ascii=False),flush=True)
finally:
    stop.set()
    monitor.join(timeout=2)
    report = {'engine_commit':'18b5f8b1862ebfe0f1c33d2355b81a54d2fec867',
              'model':json.loads((root/'active-model.json').read_text())['name'] if (root/'active-model.json').exists() else 'Qwen3.5-4B-Q4_K_M', 'threads':2, 'context':4096,
              'peak_rss_mib':round(max((x['rss_mib'] for x in samples),default=0),1),
              'max_temperature_c':max((x['temperature_c'] for x in samples),default=0),
              'results':results}
    (root/'runtime'/('coding-benchmark.json' if '--coding' in sys.argv else 'benchmark.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Peak RSS MiB:',report['peak_rss_mib'],'max CPU temperature:',report['max_temperature_c'],flush=True)
