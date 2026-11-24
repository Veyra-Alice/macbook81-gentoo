#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Route the tested analogue nodes in an ordinary desktop PipeWire session.

GNOME owns media keys, PipeWire/WirePlumber own audio and Bluetooth. This
helper only initialises analogue gain and switches the physical jack target.
It never starts an audio server or opens a microphone.
"""
import json
import os
from pathlib import Path
import subprocess
import time


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE,
                                   timeout=5)


def main():
    if Path('/sys/class/dmi/id/product_name').read_text().strip() != 'MacBook8,1':
        return
    previous = None
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state')))
    initialised = state / 'macbook81/audio-initialised'
    while True:
        try:
            objects = json.loads(run('pw-dump'))
            nodes = {o['info']['props'].get('node.name'): o['id']
                     for o in objects
                     if o.get('type') == 'PipeWire:Interface:Node'
                     and o.get('info')}
            jack = run('amixer', '-c', 'PCH', 'cget',
                       "iface=CARD,name='Headphone Jack'")
            if ': values=' not in jack:
                raise ValueError('Headphone jack state is unavailable')
            target = 'Shard_Headphones' if ': values=on' in jack else 'Shard_Speakers'
            current = (nodes['Shard_Output'], nodes[target])
            if not initialised.exists():
                run('wpctl', 'set-volume', str(nodes['Shard_Audio']), '0.35')
                run('wpctl', 'set-default', str(nodes['Shard_Audio']))
                initialised.parent.mkdir(parents=True, exist_ok=True)
                initialised.touch(mode=0o600)
            if current != previous:
                run('amixer', '-q', '-c', 'PCH', 'sset', 'Master', '85%', 'unmute')
                run('pw-metadata', '-n', 'default', str(current[0]),
                    'target.node', str(current[1]), 'Spa:Id')
                print('MacBook8,1 analogue output:', target, flush=True)
                previous = current
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            if previous is not None:
                print('Audio routing will retry:', exc, flush=True)
            previous = None
            time.sleep(2)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
