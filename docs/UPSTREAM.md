# Upstream follow-up drafts

These are preparation notes, not messages sent to anyone.

## Speaker licence clarification

Thank you for the MacBook8,1 speaker work. We used your pinned implementation
to bring up a Gentoo installation and have credited the project prominently.
Before distributing a combined kernel/installer, could you clarify the licence
for `patch_cirrus_macbook81_setup.h`, `patch_cirrus_a1534_setup.h` and
`patch_cirrus_a1534_pcm.h`? The codec C files declare GPL-2.0-or-later, but the
additional headers do not carry an explicit declaration and we could not find
a repository-wide licence. We want to retain your and the earlier contributors'
notices accurately rather than assume permission.

## Candidate technical contributions

The integration carries a narrowed HDA probe/parser change, an opt-in
MacBook8,1/PCI-specific controller preservation path that keeps speaker output
working across s2idle, an EC wake-capability quirk, and a Broadwell UART PIO
quirk. Those are candidates for separate upstream review once the complete
patches and power-management trade-offs have been tested and explained.

Do not submit an upstream claim of root cause from a successful workaround
alone. Include the tested hardware IDs, baseline/failed/passing observations,
kernel revision, limitations and attribution with any proposed patch.
