#!/usr/bin/env python3
"""Network throughput from kernel counters; ignore loopback and virtual interfaces."""
import pathlib
import time

def sample():
    result = {}
    for p in pathlib.Path('/sys/class/net').glob('*'):
        if not (p / 'device').exists():
            continue
        try:
            result[p.name] = (int((p/'statistics/rx_bytes').read_text()),
                              int((p/'statistics/tx_bytes').read_text()))
        except (OSError, ValueError):
            continue
    return result

def rate(value):
    if value >= 1024 * 1024:
        return f'{value/(1024*1024):.1f}M'
    return f'{value/1024:.0f}K'

previous = sample()
start = time.monotonic()
print('↓ 0K  ↑ 0K', flush=True)
while True:
    time.sleep(2)
    current = sample()
    now = time.monotonic()
    elapsed = max(now - start, 0.01)
    received = sum(max(0, pair[0] - previous[name][0]) for name, pair in current.items() if name in previous)
    sent = sum(max(0, pair[1] - previous[name][1]) for name, pair in current.items() if name in previous)
    print(f'↓ {rate(received/elapsed)}  ↑ {rate(sent/elapsed)}', flush=True)
    previous, start = current, now
