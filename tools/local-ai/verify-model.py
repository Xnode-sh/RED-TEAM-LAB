#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parent
profile = sys.argv[1] if len(sys.argv) > 1 else json.loads((root/'active-model.json').read_text())['profile']
model = json.loads((root/'models.json').read_text())[profile]
for filename, expected in model['files'].items():
    with (root/'models'/filename).open('rb') as f:
        actual = hashlib.file_digest(f, 'sha256').hexdigest()
    if actual != expected:
        raise SystemExit('Model checksum mismatch: '+filename)
    print('SHA256 verified:', filename, flush=True)
