#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""MacBook8,1 live-console lid policy, using the tested s2idle path."""
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import time


LED = Path('/sys/class/leds/spi::kbd_backlight/brightness')
MODE = Path('/sys/power/mem_sleep')
GUARD = Path('/var/lock/acpisleep')


def stamp(message):
    print(datetime.now(timezone.utc).isoformat(), message, flush=True)


def lid_closed():
    return any(p.read_text().split()[-1] == 'closed'
               for p in Path('/proc/acpi/button/lid').glob('*/state'))


def main():
    if Path('/sys/class/dmi/id/product_name').read_text().strip() != 'MacBook8,1':
        raise SystemExit('This experimental lid policy is only for MacBook8,1')
    modes = MODE.read_text()
    if 's2idle' not in modes.replace('[', '').replace(']', '').split():
        raise SystemExit('s2idle is unavailable')
    if sys.argv[1:] == ['--check']:
        stamp('checks passed; lid_closed=' + str(lid_closed()) +
              '; backlight=' + LED.read_text().strip())
        return
    if sys.argv[1:]:
        raise SystemExit('Usage: macbook81-lid-sleep.py [--check]')
    if not lid_closed():
        return
    try:
        fd = os.open(GUARD, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        stamp('another sleep transition owns the acpisleep guard; skipped')
        return
    owned = os.fstat(fd)
    os.close(fd)
    brightness = None
    original_mode = None
    try:
        brightness = LED.read_text().strip()
        original_mode = MODE.read_text().split('[')[1].split(']')[0]
        MODE.write_text('s2idle')
        LED.write_text('0')
        time.sleep(0.3)
        os.sync()
        if lid_closed():
            stamp('lid closed; entering s2idle; saved backlight=' + brightness)
            Path('/sys/power/state').write_text('mem')
            stamp('resumed; wake_irq=' +
                  Path('/sys/power/pm_wakeup_irq').read_text().strip())
        else:
            stamp('lid reopened before suspend; cancelled')
    finally:
        try:
            if brightness is not None:
                LED.write_text(brightness)
                stamp('restored backlight=' + brightness)
        finally:
            try:
                if original_mode is not None:
                    MODE.write_text(original_mode)
            finally:
                # acpid must remain free to consume a wake power-button event
                # while its existing shutdown handler still sees this guard.
                time.sleep(10)
                if GUARD.exists():
                    current = GUARD.stat()
                    if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                        GUARD.unlink()
                stamp('sleep guard released')


if __name__ == '__main__':
    main()
