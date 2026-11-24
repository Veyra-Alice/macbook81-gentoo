#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prepare pinned kernel sources; nothing is installed or loaded on the host."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
KERNEL_SHA256 = '020d45510c539972e6f14c5c71566878d3b7ef56fb082b3e09134f2ebaade562'
SPEAKER_COMMIT = 'fe54ad1aa7d8448fc49c0b5c8b353c50e2b1b8a1'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--linux', type=Path, required=True, help='linux-6.18.64.tar.xz')
    parser.add_argument('--speaker-source', type=Path, required=True, help='Pinned upstream Git checkout')
    parser.add_argument('--output', type=Path, required=True, help='New source directory')
    args = parser.parse_args()
    if sha256(args.linux) != KERNEL_SHA256:
        parser.error('Kernel archive checksum mismatch')
    speaker = args.speaker_source.resolve()
    commit = subprocess.check_output(['git', '-C', str(speaker), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != SPEAKER_COMMIT:
        parser.error('Unexpected speaker source revision')
    output = args.output.resolve()
    if output.exists():
        parser.error('Output exists; use a new source directory')
    output.mkdir(parents=True)
    # The verified archive has a single known root; data filter rejects links
    # outside extraction root, device nodes and other unsafe archive entries.
    with tarfile.open(args.linux) as archive:
        for item in archive:
            if item.name.rstrip('/') == 'linux-6.18.64' and item.isdir():
                continue
            if not item.name.startswith('linux-6.18.64/'):
                raise ValueError('Unexpected kernel archive root')
            item.name = item.name[len('linux-6.18.64/'):]
            if item.name:
                archive.extract(item, output, filter='data')
    for name in (ROOT / 'kernel/patches/series').read_text().splitlines():
        if not name or name.startswith('#'):
            continue
        with (ROOT / 'kernel/patches' / name).open('rb') as patch:
            subprocess.run(['patch', '--batch', '--fuzz=0', '-d', str(output), '-p1'], stdin=patch, check=True)
    destination = output / 'sound/hda/codecs/cirrus'
    receipt = {'linux_sha256': KERNEL_SHA256, 'speaker_commit': commit, 'speaker_files_sha256': {}}
    # Read Git objects at the pinned commit, never a potentially modified worktree.
    for name in ('cs420x.c', 'patch_cirrus_macbook81_setup.h',
                 'patch_cirrus_a1534_setup.h', 'patch_cirrus_a1534_pcm.h'):
        data = subprocess.check_output(['git', '-C', str(speaker), 'show', f'{commit}:patch_cirrus/{name}'])
        receipt['speaker_files_sha256'][name] = hashlib.sha256(data).hexdigest()
        if name == 'patch_cirrus_a1534_pcm.h':
            # Linux 6.18 renamed the HDA codec cleanup callback.
            data = data.replace(b'.free', b'.remove')
        (destination / name).write_bytes(data)
    (output / 'macbook81-source-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(output)


if __name__ == '__main__':
    main()
