# 1.0.0 source kit

Prepared 23 November 2026 for the 12-inch MacBook, Early 2015, model MacBook8,1.

This first source kit brings the tested Gentoo hardware support work into one
reviewable package: SPI input, Bluetooth UART quirks, firmware-preserving audio,
s2idle/lid wake, backlight restoration, desktop audio routing, console helpers,
a conservative kernel profile and documented installation steps.

Physical testing established an accelerated GNOME desktop with gestures,
speaker/headphone playback across sleep, internal microphone and camera,
Apple USB Ethernet, common Apple Bluetooth peripherals, Xbox Series input,
AirPods playback/CVSD capture, and 4K30 HDMI with 7.1 LPCM.

WPA3, Force Touch haptics, wired headset-microphone validation, long-duration
Bluetooth calls and sleep power measurements remain open. S3 and hibernation
are unsupported in this release. See the validation matrix for exact limits.

The consolidated kernel and trimmed configuration have booted on physical
hardware to a console with working Ethernet, associated Wi-Fi and camera
enumeration after supplying owner firmware. Broader regression remains open;
this console pass does not inherit all development-system hardware claims.
The installed support overlay now stages the native-panel geometry helper
and boot service; the instructions build and enable it before login prompts.
The instructions also cover a reboot-validated workaround for repeated login
banners with util-linux 2.42.3: remove the changing clock field from `/etc/issue`.
The source package excludes proprietary firmware, radio calibration and lab
access material. It is not a public binary ISO; firmware redistribution and
speaker-header licensing questions must be resolved or the affected content
omitted before such an image is published.

Standalone project tools/configuration use MIT terms. Kernel derivatives keep
their GPL terms. See CREDITS.md for upstream contributions and the explicit
human/AI development attribution.
