#!/usr/bin/env bash
set -euo pipefail
rig_ai_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
rig_ai_model="$(python3 "$rig_ai_root/model-path.py")"
export OMP_NUM_THREADS=2
exec nice -n 10 "$rig_ai_root/llama.cpp/build/bin/llama-server" \
    --model "$rig_ai_model" \
    --alias rig-local --host 127.0.0.1 --port 8087 \
    --cors-origins localhost \
    --threads 2 --threads-batch 2 --ctx-size 4096 --parallel 1 \
    --batch-size 128 --ubatch-size 64 --n-gpu-layers 0 \
    --reasoning off --temp 0.7 --top-p 0.8 --top-k 20 --min-p 0 \
    --sleep-idle-seconds 300 --ui-config-file "$rig_ai_root/ui-config.json"
