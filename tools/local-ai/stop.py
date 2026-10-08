#!/usr/bin/env python3
"""Stop only the llama-server started by our launcher."""
import os
from pathlib import Path
import signal

root = Path(__file__).resolve().parent
pidfile = root/'runtime/server.pid'
if pidfile.exists():
    text = pidfile.read_text().strip()
    if text.isdigit():
        pid = int(text)
        if Path(f'/proc/{pid}/exe').resolve() == root/'llama.cpp/build/bin/llama-server':
            os.kill(pid, signal.SIGTERM)
            print('Local AI stopping.')
        else:
            print('Local AI is already stopped.')
else:
    print('Local AI is not running.')
