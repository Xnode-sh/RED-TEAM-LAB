#!/usr/bin/env bash
set -euo pipefail
rig_capture_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$rig_capture_root/recorder-runtime/packages"
cd "$rig_capture_root/recorder-runtime/packages"
apt-get download ffmpeg libavdevice61 libcdio-cdda2t64 libcdio-paranoia2t64
for rig_capture_package in ./*.deb; do
    dpkg-deb -x "$rig_capture_package" "$rig_capture_root/recorder-runtime"
done
LD_LIBRARY_PATH="$rig_capture_root/recorder-runtime/usr/lib/x86_64-linux-gnu"     "$rig_capture_root/recorder-runtime/usr/bin/ffmpeg" -version
