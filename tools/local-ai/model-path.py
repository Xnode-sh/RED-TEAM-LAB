#!/usr/bin/env python3
import json
from pathlib import Path
root = Path(__file__).resolve().parent
profile = json.loads((root/'active-model.json').read_text())['profile']
model = json.loads((root/'models.json').read_text())[profile]
print(root/'models'/next(iter(model['files'])))
