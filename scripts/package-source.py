#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Package only the reviewed release allowlist, with hashes and stable metadata."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
NAME = 'macbook81-gentoo-1.0.0'
EPOCH = 1795392000  # 2026-11-23 00:00:00 UTC
PRIVATE_PATTERNS = (
    rb'-----BEGIN (?:OPENSSH |RSA |EC |ENCRYPTED )?PRIVATE KEY-----',
    rb'(?m)^(?:ssh-ed25519|ssh-rsa|ecdsa-sha2-\S+)\s+AAAA',
    rb'(?im)^\s*(?:psk|password|PrivateKey|LinkKey|LongTermKey)\s*=',
    rb'\b172\.16\.64\.\d+\b',
    rb'\balicepalace\.net\b',
)


def release_files():
    names = json.loads((ROOT / 'RELEASE_FILES.json').read_text())
    if names != sorted(set(names)):
        raise ValueError('Release allowlist must be sorted and unique')
    files = {}
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe allowlist path')
        path = ROOT / relative
        if path.is_symlink() or not path.is_file() or ROOT not in path.resolve().parents:
            raise ValueError('Unexpected release input: ' + name)
        data = path.read_bytes()
        if b'\0' in data or len(data) > 2 * 1024 * 1024:
            raise ValueError('Unexpected binary/large release input: ' + name)
        for pattern in PRIVATE_PATTERNS:
            if re.search(pattern, data):
                raise ValueError('Potential private material, inspect: ' + name)
        files[name] = data
    # The allowlist is itself in the archive, so extraction is independently auditable.
    if 'RELEASE_FILES.json' not in files:
        raise ValueError('Allowlist must include itself')
    return files


def build_archive(files):
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    payload = dict(files)
    payload['MANIFEST.sha256'] = ''.join(f'{digest}  {name}\n' for name, digest in sorted(hashes.items())).encode()
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', filename='', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for name, data in sorted(payload.items()):
                info = tarfile.TarInfo(NAME + '/' + name)
                info.size = len(data)
                info.mtime = EPOCH
                info.uid = info.gid = 0
                info.uname = info.gname = 'root'
                info.mode = 0o755 if data.startswith(b'#!') else 0o644
                archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Audit inputs without writing an archive')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist' / (NAME + '-source.tar.gz'))
    args = parser.parse_args()
    files = release_files()
    if args.check:
        print(f'Allowlist audit passed: {len(files)} text/source files; no firmware or credentials bundled.')
        return
    if args.output.is_symlink():
        parser.error('Output must not be a symlink')
    output = args.output.resolve()
    checksum = output.with_name(output.name + '.sha256')
    if output.exists() or checksum.exists() or checksum.is_symlink():
        parser.error('Output exists; inspect it before rebuilding')
    data = build_archive(files)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(data)
    digest = hashlib.sha256(data).hexdigest()
    with checksum.open('x') as stream:
        stream.write(f'{digest}  {output.name}\n')
    print(f'{output}: {len(data)} bytes, SHA256 {digest}')


if __name__ == '__main__':
    main()
