#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Stage MacBook8,1 console and desktop support into a mounted Gentoo root.

Does not partition, format, install a bootloader, enable SSH or create users.
The supplied root may be a staging directory. Service enabling and initramfs
creation are explicit subsequent steps inside the target Gentoo installation.
"""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'src/fit-macbook81-console.c': ('usr/local/src/macbook81/fit-macbook81-console.c', 0o644),
    'config/macbook81-console-fit.service': ('etc/systemd/system/macbook81-console-fit.service', 0o644),
    'src/macbook81-desktop-audio.py': ('usr/local/bin/macbook81-desktop-audio.py', 0o755),
    'src/macbook81-backlight-sleep': ('usr/lib/systemd/system-sleep/macbook81-backlight', 0o755),
    'src/macbook81-wifi': ('usr/local/sbin/macbook81-wifi', 0o755),
    'config/60-macbook81.conf': ('etc/pipewire/pipewire.conf.d/60-macbook81.conf', 0o644),
    'config/51-macbook81-alsa.conf': ('etc/wireplumber/wireplumber.conf.d/51-macbook81-alsa.conf', 0o644),
    'config/macbook81-desktop-audio.service': ('etc/systemd/user/macbook81-desktop-audio.service', 0o644),
    'config/macbook81-sleep.conf': ('etc/systemd/sleep.conf.d/macbook81.conf', 0o644),
    'config/macbook81-wifi.service': ('etc/systemd/system/macbook81-wifi.service', 0o644),
    'config/macbook81-speaker.conf': ('etc/modprobe.d/macbook81-speaker.conf', 0o644),
    'config/macbook81-modules.conf': ('etc/modules-load.d/macbook81.conf', 0o644),
    'config/macbook81-networkmanager.conf': ('etc/NetworkManager/conf.d/20-macbook81.conf', 0o644),
    'config/macbook81-dracut.conf': ('etc/dracut.conf.d/macbook81.conf', 0o644),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    target = args.root.resolve()
    if target == Path('/'):
        parser.error('Stage into a mounted target, not the running system')
    if not (target / 'etc/gentoo-release').is_file():
        parser.error('Target must be a prepared Gentoo filesystem')
    # Permit Gentoo usr-merge symlinks only when they resolve within the target.
    destinations = []
    for source, (relative, mode) in FILES.items():
        destination = target / relative
        if target not in destination.resolve().parents:
            parser.error('Target contains an escaping symlink: ' + relative)
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or not destination.is_file():
                parser.error('Unexpected existing destination: ' + relative)
            if destination.read_bytes() != (ROOT / source).read_bytes():
                parser.error('Existing file differs; inspect before replacing: ' + relative)
        destinations.append((ROOT / source, destination, mode))
    for source, destination, mode in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        destination.chmod(mode)
    print('Staged support overlay; no services started and no credentials changed.')
    print('Build the console helper and enable its service as documented in docs/INSTALL.md.')
    print('That document also covers firmware, boot and optional desktop steps.')


if __name__ == '__main__':
    main()
