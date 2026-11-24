#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Console-only MacBook8,1 brightness keys; never grabs or records keyboard input.

Disable this service before installing a desktop power manager to avoid handling
the same brightness event twice. Fn+F1/F2 and Fn+F5/F6 retain normal function-key
behaviour with applespi.fnmode=1; the unmodified keys control the lights.
"""
import argparse
import os
from pathlib import Path
import selectors
import signal
import struct
import subprocess
import time

SYS = Path('/sys')
# Native struct input_event: timeval, unsigned short type/code, signed int value.
EVENT = struct.Struct('@llHHi')
KEYS = {224: ('display', -1), 225: ('display', 1),
        229: ('keyboard', -1), 230: ('keyboard', 1)}
AUDIO_KEYS = {113: 'toggle', 114: '5%-', 115: '5%+'}
running = True


def control(kind):
    if kind == 'display':
        candidates = list((SYS / 'class/backlight').glob('intel_backlight'))
        if not candidates:
            candidates = list((SYS / 'class/backlight').glob('*'))
    else:
        candidates = list((SYS / 'class/leds').glob('*::kbd_backlight'))
        candidates = [p for p in candidates if 'spi' in str(p.resolve())]
    if len(candidates) != 1:
        raise RuntimeError(f'Expected one {kind} backlight, found {len(candidates)}')
    return candidates[0]


def adjust(kind, direction):
    device = control(kind)
    maximum = int((device / 'max_brightness').read_text())
    current = int((device / 'brightness').read_text())
    step = max(1, (maximum + 15) // 16)
    # Screen never goes black through this handler. Keyboard may be fully off.
    minimum = max(1, maximum // 100) if kind == 'display' else 0
    target = max(minimum, min(maximum, current + direction * step))
    (device / 'brightness').write_text(str(target))


def stop(_signum, _frame):
    global running
    running = False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    if (SYS / 'class/dmi/id/product_name').read_text().strip() != 'MacBook8,1':
        raise SystemExit('This helper is scoped to MacBook8,1.')
    if args.status:
        for kind in ('display', 'keyboard'):
            try:
                p = control(kind)
                print(kind, p.name, (p / 'brightness').read_text().strip(),
                      '/', (p / 'max_brightness').read_text().strip())
            except (OSError, ValueError, RuntimeError) as exc:
                print(kind, exc)
        return
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    selector = selectors.DefaultSelector()
    opened = {}
    retry = 0.0
    while running:
        if time.monotonic() >= retry:
            for event in (SYS / 'class/input').glob('event*'):
                try:
                    if (event / 'device/name').read_text().strip() != 'Apple SPI Keyboard':
                        continue
                    node = '/dev/input/' + event.name
                    if node not in opened:
                        fd = os.open(node, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
                        selector.register(fd, selectors.EVENT_READ, node)
                        opened[node] = fd
                except (OSError, ValueError):
                    continue
            retry = time.monotonic() + 3
        for key, _ in selector.select(timeout=1):
            try:
                raw = os.read(key.fd, EVENT.size * 64)
                if not raw:
                    raise OSError('Input device removed')
                for _, _, kind, code, value in EVENT.iter_unpack(raw):
                    if kind == 1 and value in (1, 2) and code in AUDIO_KEYS:
                        # Holding mute must not repeatedly toggle it.
                        if code == 113 and value == 2:
                            continue
                        try:
                            audio_socket = Path('/run/shard-audio/control.sock')
                            action = {113: 'mute', 114: 'down', 115: 'up'}[code]
                            command = (['/usr/bin/python3', '/opt/macbook81/shard-audio.py', action]
                                       if audio_socket.exists() else
                                       ['amixer', '-q', '-c', 'PCH', 'sset', 'Master',
                                        AUDIO_KEYS[code]])
                            subprocess.run(
                                command, check=True, timeout=5,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except (OSError, subprocess.SubprocessError) as exc:
                            print(f'Volume change unavailable: {exc}', flush=True)
                    elif kind == 1 and value in (1, 2) and code in KEYS:
                        try:
                            adjust(*KEYS[code])
                        except (OSError, ValueError, RuntimeError) as exc:
                            print(f'Brightness change unavailable: {exc}', flush=True)
            except (OSError, ValueError):
                selector.unregister(key.fd)
                os.close(key.fd)
                opened.pop(key.data, None)
    for fd in opened.values():
        os.close(fd)
    selector.close()


if __name__ == '__main__':
    main()
