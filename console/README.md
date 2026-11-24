# Live-console reference support

These original helpers preserve the working OpenRC live-console behaviour for
future clean ISO assembly. They are not installed by the GNOME desktop overlay.
Never run both policies together: GNOME/logind and a user PipeWire session own
the desktop's keys, audio and sleep.

`shard-hotkeys.py` reads only the Apple SPI Keyboard event device, does not grab
it and acts only on the media/backlight keys. It never stores ordinary key
events. `shard-audio.py` runs an isolated playback-only PipeWire/WirePlumber
instance under `/run/shard-audio`, accepts only four named actions over a
root-only UNIX socket, and starts no network listener or microphone capture.

The live-console files retain their tested compatibility names. The lid event
and asynchronous sleep helper require the inherited acpid power-button action
to respect `/var/lock/acpisleep`; otherwise a fallback wake-button press can
immediately shut the resumed machine down. That guard is a prerequisite, not
an optional line to omit when remastering. The sleep service loads the exact
kernel's EC wake module and selects s2idle before acpid starts.

For a live console, use the supplied playback-only PipeWire configuration,
the isolated WirePlumber configuration and the console helper service. Keep
Speakup available as an explicit boot choice rather than unconditionally
loading its Caps Lock keyboard hook. Integrate the console geometry helper
before the initramfs keymap prompt as well as after font selection.

These files are source references, not a standalone live-image installer.
No firmware, credentials, host keys, package binaries or old image-assembly
scripts are bundled in this directory.
