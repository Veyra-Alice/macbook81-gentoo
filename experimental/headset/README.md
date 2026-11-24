# Experimental wired headset capture

The private validation kernel also carried this separate CS4208 headset ADC
endpoint and its register diagnostics. It is retained here for reproducibility
and further work, under its existing GPL-2.0-or-later notice. It is **not** part
of the default 1.0 kernel preparation: no working wired headset mic was
established, because the available physical headset failed independent controls.

The endpoint adds a separate PCM rather than changing the working internal mic
or speaker path. It applies VREF only while explicitly opened. The diagnostic
bias parameter is root-writable and must only be changed with capture closed.
This is a hardware experiment, not a supported recording interface.

To reconstruct the private codec candidate, apply `cs420x-headset.patch` with
`-p1` inside the already prepared `sound/hda/codecs/cirrus` directory and copy
`macbook81-headset-pcm.h` alongside it, then rebuild the complete matching
kernel/module set. That addition explains one intentional difference between
the audited default build and the old test machine's codec. Do not hot-reload
the active HDA stack.
