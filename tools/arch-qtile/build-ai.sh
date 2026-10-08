#!/usr/bin/env bash
# Rebuild the preserved llama.cpp source with Arch's native build tools.
set -euo pipefail
[[ $EUID -ne 0 ]] || { echo 'Run as the restored user, not root.' >&2; exit 1; }
source /etc/os-release
[[ "$ID" == arch && ! -d /run/archiso ]] || { echo 'Requires installed Arch.' >&2; exit 1; }
rig_root="$HOME/RED-TEAM-LAB/tools/local-ai"
rig_expected=18b5f8b1862ebfe0f1c33d2355b81a54d2fec867
[[ "$(git -C "$rig_root/llama.cpp" rev-parse HEAD)" == "$rig_expected" ]] || {
    echo 'Unexpected llama.cpp revision; inspect preserved sources before building.' >&2; exit 1;
}
python3 "$rig_root/verify-model.py" general
python3 "$rig_root/verify-model.py" coder
rig_stamp=$(date -u +%Y%m%dT%H%M%SZ)
if [[ -e "$rig_root/llama.cpp/build" ]]; then
    mv -T -- "$rig_root/llama.cpp/build" "$rig_root/llama.cpp/build.debian-$rig_stamp"
fi
cmake -S "$rig_root/llama.cpp" -B "$rig_root/llama.cpp/build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=OFF \
    -DGGML_AVX=ON -DGGML_AVX2=OFF -DGGML_BMI2=OFF -DGGML_FMA=OFF \
    -DGGML_F16C=ON -DGGML_AVX512=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_OPENSSL=OFF -DBUILD_SHARED_LIBS=OFF
nice -n 15 cmake --build "$rig_root/llama.cpp/build" --target llama-server llama-bench -j 2
echo 'Arch build completed. Validate with launch.py and a short terminal chat.'
