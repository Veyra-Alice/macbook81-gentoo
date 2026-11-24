#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""MacBook8,1 live-console audio supervisor and hotkey control.

Only owns the private root console's PipeWire instance. Disable this service
and the console hotkey helper when migrating to a normal desktop user session.
No network listeners, recording nodes, keyboard access or SSD writes.
"""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

BASE = Path('/run/shard-audio')
SOCKET = BASE / 'control.sock'
os.environ['PIPEWIRE_RUNTIME_DIR'] = str(BASE / 'runtime')
os.environ['XDG_RUNTIME_DIR'] = str(BASE / 'runtime')
os.environ['XDG_STATE_HOME'] = str(BASE / 'state')
os.environ['XDG_CONFIG_HOME'] = str(BASE / 'config')
running = True


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=3)


def nodes():
    return {o['info']['props'].get('node.name'): o['id']
            for o in json.loads(run('pw-dump'))
            if o.get('type') == 'PipeWire:Interface:Node' and o.get('info')}


def command(action, sink):
    if action == 'mute':
        run('wpctl', 'set-mute', str(sink), 'toggle')
    elif action in ('up', 'down'):
        run('wpctl', 'set-volume', '--limit', '1.0', str(sink),
            '5%+' if action == 'up' else '5%-')
    elif action != 'status':
        raise ValueError('Unknown audio action')
    return run('wpctl', 'get-volume', str(sink)).strip()


def stop(_signum, _frame):
    global running
    running = False


def main():
    if Path('/sys/class/dmi/id/product_name').read_text().strip() != 'MacBook8,1':
        raise SystemExit('This helper is scoped to MacBook8,1.')
    if len(sys.argv) > 1:
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(4)
            client.connect(str(SOCKET))
            client.sendall(sys.argv[1].encode())
            reply = client.recv(2048).decode()
            print(reply)
            if reply.startswith('error:'):
                raise SystemExit(1)
        return
    BASE.mkdir(mode=0o700, exist_ok=True)
    for name in ('runtime', 'state', 'config'):
        (BASE / name).mkdir(mode=0o700, exist_ok=True)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    children = []
    server = socket.socket(socket.AF_UNIX)
    try:
        for executable in ('pipewire', 'wireplumber'):
            log = open(BASE / (executable + '.log'), 'a')
            children.append(subprocess.Popen([executable], stdout=log, stderr=log))
            log.close()
            time.sleep(0.5)
        known = {}
        for _ in range(40):
            if not running:
                return
            if any(p.poll() is not None for p in children):
                raise RuntimeError('Audio child exited; inspect /run/shard-audio logs')
            try:
                known = nodes()
                if all(n in known for n in ('Shard_Audio', 'Shard_Output',
                                             'Shard_Speakers', 'Shard_Headphones')):
                    break
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
            time.sleep(0.25)
        else:
            raise RuntimeError('Expected playback nodes did not appear')
        sink = known['Shard_Audio']
        run('wpctl', 'set-volume', str(sink), '0.35')
        run('wpctl', 'set-mute', str(sink), '0')
        run('wpctl', 'set-default', str(sink))
        # Fixed analogue headroom; the shared virtual sink controls volume.
        run('amixer', '-q', '-c', 'PCH', 'sset', 'Master', '85%', 'unmute')
        if SOCKET.exists():
            SOCKET.unlink()
        server.bind(str(SOCKET))
        os.chmod(SOCKET, 0o600)
        server.listen(4)
        server.settimeout(0.15)
        last = None
        next_check = 0
        while running:
            if any(p.poll() is not None for p in children):
                raise RuntimeError('Audio child exited')
            if time.monotonic() >= next_check:
                jack = run('amixer', '-c', 'PCH', 'cget',
                           "iface=CARD,name='Headphone Jack'")
                plugged = ': values=on' in jack
                if ': values=' not in jack:
                    raise RuntimeError('Cannot determine headphone jack state')
                if plugged != last:
                    target = 'Shard_Headphones' if plugged else 'Shard_Speakers'
                    run('pw-metadata', '-n', 'default', str(known['Shard_Output']),
                        'target.node', str(known[target]), 'Spa:Id')
                    print('Output:', target, flush=True)
                    last = plugged
                next_check = time.monotonic() + 0.25
            try:
                connection, _ = server.accept()
            except socket.timeout:
                continue
            with connection:
                connection.settimeout(1)
                try:
                    action = connection.recv(32).decode()
                    reply = command(action, sink)
                except (OSError, ValueError, subprocess.SubprocessError) as exc:
                    reply = 'error: ' + str(exc)
                connection.sendall(reply.encode())
    finally:
        server.close()
        if SOCKET.exists():
            SOCKET.unlink()
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    main()
