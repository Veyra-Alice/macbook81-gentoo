# Gentoo for MacBook8,1

A hardware support kit for the **12-inch MacBook, Early 2015 (MacBook8,1)**.
It collects the kernel changes, desktop configuration and installation notes
developed and tested on a real machine, with Gentoo and GNOME on Wayland.

Version **1.0.0**, prepared 23 November 2026. This directory is the curated
source release candidate. The earlier private test ISO is not a public release.
The consolidated, trimmed kernel has booted to a physical console with
owner-supplied firmware. Broader hardware regression remains necessary.

This is ordinary Gentoo with a model-specific support layer. It does not
partition disks, run an unattended installer or replace Portage. USB adapters,
external storage, Bluetooth peripherals and normal desktop software remain
supported. There is no remote-access key, password, saved pairing or Wi-Fi
credential in this source kit.

## Hardware status

The following results describe the working development installation and live
media, not a claim that the new release build has completed physical regression.

| Feature | Observed result |
| --- | --- |
| SPI keyboard and trackpad | Working, including Caps Lock and brightness keys |
| Accelerated graphics | Intel HD Graphics 5300, GNOME Wayland, native 2304×1440 |
| Desktop gestures | Scrolling, pinch and three-finger swipe confirmed |
| Speakers and headphone output | Working, including repeated jack changes across sleep |
| Internal microphone | Recording and audible replay confirmed |
| FaceTime HD camera | Working preview confirmed |
| Lid sleep and wake | s2idle working, with backlight restoration and retained input |
| Bluetooth input | Magic Mouse, Trackpad, Keyboard and Xbox Series controller tested |
| AirPods | AAC playback and CVSD microphone/replay confirmed; see limitations |
| Apple USB 10/100 Ethernet | Working with the stock ASIX driver |
| Apple AV adapter | Extended 4K at 30 Hz and correctly positioned 7.1 LPCM confirmed |
| Charging through AV adapter | Confirmed with an Apple 61 W charger; connector/charger issues remain possible |

Known limits: WPA3 is unresolved; Force Touch haptics are absent; S3 is
explicitly unsupported; hibernation is not configured. The wired headset mic
awaits a working replacement headset. AirPods capture was validated with
simultaneous output, and Bluetooth discovery can disrupt playback. Long calls,
arbitrary application capture, sleep battery drain and Dolby/DTS passthrough
are not validated. Only the baseline CPU board and US keyboard have been
physically tested so far.

## Start here

* [Installation and build instructions](docs/INSTALL.md)
* [Kernel scope and trimming policy](docs/KERNEL.md)
* [Validation matrix](docs/VALIDATION.md)
* [Code and release audit](docs/AUDIT.md)
* [Firmware and redistribution](docs/FIRMWARE.md)
* [Credits and component licences](CREDITS.md)

Our standalone tools and configuration are MIT-licensed. Kernel derivatives
retain GPL terms. Third-party code and firmware retain their own licences:
there is no blanket relicensing of Gentoo, Linux or Apple software.
See [LICENSE](LICENSE).

## Release contents

`kernel/` contains the reference configuration, a reviewed trimming policy
implemented by `scripts/configure-kernel.py`, six Linux patches and the EC wake
module source. `src/` and `config/` contain the installed-desktop support layer.
`console/` retains the separate live-console policy, and `experimental/` keeps
the unsupported wired-headset capture work distinct from the defaults.
`scripts/` prepares sources, resolves configuration, builds kernel/modules,
stages the desktop overlay and assembles a deterministic source archive.

The original lab's experimental probes, raw hardware dumps, private networks,
pairing material, machine identifiers and obsolete failed candidates are not
part of the release. Existing `Shard_*` PipeWire node identifiers are retained
as compatibility identifiers; all visible descriptions use the model name.

Please report the exact MacBook model, kernel version, firmware provenance
and steps needed to reproduce a fault. Review diagnostic output for personal
information before sharing it. Do not hot-unbind the SPI or HDA controllers:
these paths have previously produced kernel faults; reboot between driver tests.
