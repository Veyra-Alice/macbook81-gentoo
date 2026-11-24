# Validation boundary

Testing was performed collaboratively on one baseline 1.1 GHz MacBook8,1 with
8 GiB RAM, a US keyboard and a 256 GB SSD. Later 1.3 GHz and UK-keyboard variants
are planned, not tested. Results apply to the development system as of
23 November 2026. They do not certify the newly consolidated 1.0 kernel.

| Area | Physical evidence | Remaining limit |
| --- | --- | --- |
| Boot and display | Development GNOME, native panel and readable GRUB; consolidated release kernel booted to live and installed console; installed geometry helper passed reboot | Broader release-build desktop regression pending |
| Input | Internal keyboard/trackpad, Caps LED, brightness, scrolling, pinch, three-finger swipe | Force Touch haptics absent |
| Wi-Fi | WPA2 connection and useful SSH traffic | WPA3 unresolved; firmware/calibration provisioning is local |
| USB Ethernet | Apple 10/100 adapter link and traffic | Other adapters are supported by retained drivers, not all individually tested |
| Speakers/headphones | Audible output, many jack changes and repeated lid cycles | Sleep battery drain unmeasured |
| Internal mic | Audible speech recording/replay | General application/long-session coverage incomplete |
| Wired headset mic | Original headset failed independent macOS and iPhone controls | Await replacement; no driver failure inferred from broken headset |
| Camera | Visible preview and indicator LED confirmed | Not a complete image-quality assessment |
| Sleep | Lid-close s2idle and lid-open wake, restored input/backlights/audio | S3 blocked; hibernation disabled; no battery-life claim |
| Bluetooth input | Magic Mouse, Trackpad and Keyboard working | Power-cycle and suspend regression not exhaustive |
| Xbox Series controller | Solid LED and more than 800 real input events with stock driver | Rumble and reconnect-after-power-cycle not tested |
| AirPods playback | Smooth AAC after stopping discovery | Active discovery can make audio choppy |
| AirPods mic | Intelligible CVSD capture/replay with simultaneous silent output, including after resume | mSBC and capture without simultaneous output not validated |
| Profile policy | Automatic CVSD with one/two capture clients, AAC after last client closes; repeat succeeded | Node policy test alone does not establish intelligibility |
| HDMI display | Extended 3840×2160 at 30 Hz through Apple AV adapter/receiver | 4K60 not advertised by tested path |
| HDMI audio | Seven correctly positioned main speakers plus isolated LFE through PipeWire and direct ALSA | Dolby/DTS bitstream passthrough not tested |

A loose physical subwoofer cable was repaired during HDMI validation. Both
desktop and direct ALSA LFE then passed. It was not established as a kernel
LFE fault. No room calibration or receiver master volume was altered.

The audio controller's s2idle preservation patch was tested by repeatedly
sleeping during playback, switching to headphones across sleep and returning
to speakers. The controller is intentionally retained in D0. The observations
support that workaround, without identifying every lost firmware amplifier
state or quantifying its power cost.

No microphone recordings, raw hardware dumps, saved pairings or private
network configuration form part of this public validation record.

The consolidated installed console also reproduced repeated login banners
with util-linux 2.42.3. Removing the banner's clock escape stopped the repeats
on the next boot, as confirmed by the physical tester. This workaround is
documented in INSTALL.md; it does not change authentication or kernel behaviour.
