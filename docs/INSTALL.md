# Build and installation

Use the [Gentoo AMD64 Handbook](https://wiki.gentoo.org/wiki/Handbook:AMD64)
for partitioning, stage3 installation, networking, accounts and the bootloader.
This kit supplies the model-specific layer. It deliberately contains no
hard-coded partition names, UUIDs, saved accounts or remote-access credentials.

## Build host and pinned inputs

Use an x86-64 Linux build host with Python 3.9 or newer with tarfile data-filter
support, Git, GNU make, GCC, binutils, flex, bison, OpenSSL development headers,
libelf development headers, patch, tar, xz and kmod. The tested reference kernel
is Linux 6.18.64. Building is unprivileged and does not install on the build host.
Use `JOBS` to fit available RAM; compiling a large kernel on the Mac itself can
take a long time. Do not compile with another host's `-march=native` flags.

Fetch `linux-6.18.64.tar.xz` from
[kernel.org](https://cdn.kernel.org/pub/linux/kernel/v6.x/). The preparation script
checks its pinned SHA256:
`020d45510c539972e6f14c5c71566878d3b7ef56fb082b3e09134f2ebaade562`.

```sh
mkdir -p work
git clone https://github.com/thomas-shirley/macbook8.1-speaker-driver work/speaker
git -C work/speaker checkout --detach fe54ad1aa7d8448fc49c0b5c8b353c50e2b1b8a1
git clone https://github.com/patjak/facetimehd work/facetimehd
git -C work/facetimehd checkout --detach 4159eef064e4170cbd94fd6c633cbd04bf589c4d

python3 scripts/prepare-kernel.py \
  --linux /path/to/linux-6.18.64.tar.xz \
  --speaker-source work/speaker --output work/linux-6.18.64
python3 scripts/configure-kernel.py work/linux-6.18.64 work/build --profile trimmed
FACETIMEHD_SOURCE="$PWD/work/facetimehd" JOBS=8 \
  bash scripts/build-kernel.sh work/linux-6.18.64 work/build
```

Preparation reads the speaker files directly from the pinned Git objects.
There is no dependency on a dirty checkout or on the old experiments directory.
Existing prepared/configured directories are refused; use new directories for
a different profile. `--profile reference` retains the broad hardware support
baseline for comparison. Both profiles build a new `-macbook81-1.0.0` ABI.

The consolidated and trimmed build has booted to a physical console with
owner firmware. Its broader hardware regression is still pending.
Build results and outstanding checks are in [AUDIT.md](AUDIT.md).

## Desktop packages

The development installation started with the verified
`stage3-amd64-desktop-systemd-20261122T164601Z.tar.xz` and profile
`default/linux/amd64/23.0/desktop/gnome/systemd`. Use Gentoo's published signature
verification procedure for installation media and stage3. Keep normal Portage
metadata and package licences; these are not replaced by this source kit.

Required facilities include GNOME/GDM, NetworkManager, BlueZ, PipeWire with
PulseAudio compatibility, WirePlumber, ALSA utilities, iw, Python 3, kmod,
dracut, GRUB with EFI support, Mesa/i915, Intel microcode, a suitable console
font and a camera viewer for validation. The tested audio stack was PipeWire
1.6.9 and WirePlumber 0.5.18; BlueZ was 5.87. Use systemd for this desktop
overlay. The earlier OpenRC live-console policy is separate historical work.

## Stage into the mounted installation

With the Gentoo root mounted at `/mnt/gentoo` and its EFI partition mounted
under `/mnt/gentoo/boot/efi`, run:

```sh
sudo python3 scripts/stage-desktop.py --root /mnt/gentoo
```

The script requires `/etc/gentoo-release` in the target and refuses `/`.
It refuses different existing files instead of silently replacing local
configuration. Review those files manually if customising an existing install.

Despite its historical filename, the script stages both console support and
optional desktop configuration. It installs no desktop packages and enables
no services. A console-only installation can use it too.

## Console sizing, required for either installation

Inside the target chroot, build and enable the staged geometry helper:

```sh
cc -O2 -Wall -Wextra -Werror \
  /usr/local/src/macbook81/fit-macbook81-console.c \
  -o /usr/local/sbin/fit-macbook81-console
/usr/local/sbin/fit-macbook81-console --help
systemctl enable macbook81-console-fit.service
```

The unit runs after device discovery and virtual-console setup, before the
login prompts. It checks the exact model, Intel driver, connected internal
panel mode and current font dimensions. With the 16 by 32 pixel font, it fits
144 columns by 45 rows to the native 2304 by 1440 panel. Without this step,
the installed console can retain 160 by 50 cells from the boot framebuffer
and draw beyond the screen. The live image already performs this correction;
copying its kernel alone does not install the boot service.

For a console-first installation, enable the intended networking services
and select `systemctl set-default multi-user.target`. Leave GDM disabled until
choosing a desktop. The desktop enablement commands below are optional.

### Repeated login banners during network startup

The tested util-linux 2.42.3 can repeatedly redraw the login prompt while
network interfaces come up when `/etc/issue` contains the `\t` clock escape.
This matches [upstream issue 4306](https://github.com/util-linux/util-linux/issues/4306).
It is a banner refresh, not a login-service crash. On the physical test system,
removing that escape stopped the repeated prompts on the next boot.

Inside the installed target, preserve the banner and remove only its clock:

```sh
python3 - <<'PY'
from pathlib import Path
import shutil

banner = Path('/etc/issue')
original = banner.read_text()
clock = chr(92) + 't'
if clock in original:
    backup = banner.with_name('issue.before-static-banner')
    if backup.exists() or backup.is_symlink():
        raise SystemExit('Backup already exists; inspect it before changing the banner.')
    shutil.copy2(banner, backup)
    banner.write_text(original.replace(' ' + clock, '').replace(clock, ''))
PY
```

No service restart is required; check the result on the next normal boot.
The stage script does not overwrite a distribution's or owner's login banner.

## Kernel, firmware and boot

Copy `work/build/modules/lib/modules/6.18.64-macbook81-1.0.0` to the target's
`/lib/modules/`, and the matching `arch/x86/boot/bzImage`, `.config` and
`System.map` into `/boot` with the version in each filename. Retain the previous
working kernel and initramfs as a separate GRUB entry. Remove or relocate the
module tree's `build` and `source` links if they point to another build host.

Supply your own matching firmware as described in [FIRMWARE.md](FIRMWARE.md).
Do not use another machine's radio calibration or force a foreign country code.
The release Wi-Fi helper only disables power saving; it does not apply the
test machine's US-specific firmware country workaround automatically.

Merge `config/bluetooth-main.conf.fragment` into the corresponding sections of
`/etc/bluetooth/main.conf` if using the tested controller-pairing setup. These
settings were tested together; no claim is made that each is individually
necessary. Pair locally with an agent. Close Bluetooth discovery after pairing
before judging audio quality. No bonds are included or transferred from macOS.

Inside the target chroot, enable the installed desktop services and build the
matching initramfs. Do not execute these commands on the build host:

```sh
depmod 6.18.64-macbook81-1.0.0
systemctl enable gdm NetworkManager bluetooth macbook81-wifi
systemctl --global enable pipewire.socket pipewire-pulse.socket wireplumber.service
systemctl --global enable macbook81-desktop-audio.service
systemctl set-default graphical.target
dracut --force --no-hostonly --early-microcode \
  --kver 6.18.64-macbook81-1.0.0 /boot/initramfs-6.18.64-macbook81-1.0.0.img
```

Set `mem_sleep_default=s2idle fbcon=font:TER16x32` in GRUB's kernel command line
with a suitable console font installed. A 32-pixel GRUB font and gfxterm avoid
an unreadably small menu on the Retina panel. Generate the font from an
installed monospaced TTF with `grub-mkfont -s 32`, set `GRUB_FONT` to its path,
then regenerate `grub.cfg`. Complete EFI bootloader installation through the
Handbook, choosing the target EFI partition explicitly. No bootloader-writing
script is run by this kit.

## First boot and regression

Check graphics and scaling, typing/Caps Lock, both backlights, speaker and
headphone playback, the internal microphone, camera and USB networking. Close
and open the lid repeatedly, both during playback and after changing the jack.
Verify `/sys/power/mem_sleep` offers only s2idle. Test Bluetooth and HDMI with
the devices actually used. Record the new kernel version with the results.
No old physical pass automatically validates the newly trimmed kernel.

Rollback is selecting the previous kernel and matching modules/initramfs in
GRUB. Do not unload and reload the active audio or SPI drivers to switch builds.

## Building an ISO

This 1.0 source package is the reproducible support layer, not a complete
Gentoo distribution build system. A private clean live candidate has booted
on physical hardware and excludes the owner-supplied Apple Wi-Fi, camera and
radio-calibration files. Earlier private hardware-validation images contain
those assets and must remain private. Redistribution permission for the Apple
assets has not been established. Do not mistake source-archive checks for an
image audit or permission to publish the private test images.

A public ISO needs the same source/configuration closure, a clean Gentoo live
base, matching kernel/initramfs modules, a user-supplied firmware workflow,
package licence/source compliance, removal of all test access material from
both root filesystem and initramfs, and a fresh physical boot test. These are
explicit release gates, not implied by the source-kit version number.
