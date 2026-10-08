#!/usr/bin/env bash
set -euo pipefail
rig_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$rig_root"
mkdir -p models runtime
if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
fi
.venv/bin/pip install -r requirements-build.txt
if [[ ! -d llama.cpp/.git ]]; then
    git clone https://github.com/ggml-org/llama.cpp.git llama.cpp
    git -C llama.cpp checkout 18b5f8b1862ebfe0f1c33d2355b81a54d2fec867
fi
.venv/bin/cmake -S llama.cpp -B llama.cpp/build -G Ninja \
    -DCMAKE_MAKE_PROGRAM="$rig_root/.venv/bin/ninja" -DCMAKE_BUILD_TYPE=Release \
    -DGGML_NATIVE=OFF -DGGML_AVX=ON -DGGML_AVX2=OFF -DGGML_BMI2=OFF \
    -DGGML_FMA=OFF -DGGML_F16C=ON -DGGML_AVX512=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_OPENSSL=OFF -DBUILD_SHARED_LIBS=OFF
nice -n 15 .venv/bin/cmake --build llama.cpp/build --target llama-server llama-bench -j 2
python3 download-model.py
printf '\nInstalled. Start: python3 tools/local-ai/launch.py (from repository root).\n'
