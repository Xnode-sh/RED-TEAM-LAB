#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parent
profile = sys.argv[1] if len(sys.argv)>1 else json.loads((root/'active-model.json').read_text())['profile']
model = json.loads((root/'models.json').read_text())[profile]
(root/'models').mkdir(exist_ok=True)
for filename in model['files']:
    subprocess.run(['curl', '--fail', '--location', '--retry', '3', '--continue-at', '-',
                    '--output', str(root/'models'/filename), model['source']+'/resolve/main/'+filename], check=True)
subprocess.run(['python3', str(root/'verify-model.py'), profile], check=True)
