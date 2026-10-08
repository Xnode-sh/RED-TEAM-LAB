#!/usr/bin/env python3
"""Verify sample file hashes while decrypting the entire migration archive."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tarfile


def digest(stream):
    result = hashlib.sha256()
    while data := stream.read(1024 * 1024):
        result.update(data)
    return result.hexdigest()


def verify(source, archive):
    relative = [
        "home/red-team-lab/RED-TEAM-LAB/.git/HEAD",
        "home/red-team-lab/RED-TEAM-LAB/agents/RIG/STATE.md",
        "home/red-team-lab/.codex/config.toml",
        "home/red-team-lab/RED-TEAM-LAB/tools/local-ai/models/Qwen3.5-4B-Q4_K_M.gguf",
    ]
    expected = {}
    for name in relative:
        with (source / name).open("rb") as stream:
            expected[name] = digest(stream)
    found = {}
    process = subprocess.Popen(["gpg", "--decrypt", str(archive)], stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as stream:
            for member in stream:
                name = member.name.removeprefix("./")
                if name in expected:
                    if name in found or not member.isfile():
                        raise RuntimeError("Duplicate or non-regular verification sample")
                    with stream.extractfile(member) as contents:
                        found[name] = digest(contents)
        while process.stdout.read(1024 * 1024):
            pass
        if process.wait() != 0:
            raise RuntimeError("GPG did not confirm complete decryption")
        if found != expected:
            raise RuntimeError("Missing sample or mismatch with the original Debian data")
        print("Verified: complete decryption and four sample hashes (project, Codex, GGUF).")
    finally:
        process.stdout.close()
        if process.poll() is None:
            process.terminate()
            process.wait()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 verify-backup.py /mnt/debian ARCHIVE.tar.gpg")
    verify(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
