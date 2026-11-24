# Source and release audit

Reviewed 23 November 2026 by Veyra with Alice's physical validation evidence.
This is a bounded engineering review, not a claim of a complete independent
audit of Linux, Gentoo or every upstream dependency.

## Scope and findings

| Area | Finding | Disposition |
| --- | --- | --- |
| Build closure | Previous scripts depended on a sequence of private experiment directories and replacement modules | Consolidated into six patches against a checksum-pinned pristine kernel, plus a pinned upstream codec and external EC/camera builds |
| Kernel ABI | Replacing selected modules under an old release name hid what had changed | New `6.18.64-macbook81-1.0.0` release name; rebuild matching modules together |
| Hardware trimming | Broad inherited kernel supported impossible PCI cards and other buses | Resolve through Kconfig; enforce required internal drivers and retain supported peripheral selections |
| Generic initramfs dependency | First clean-media boot probe reached an unconditional iSCSI probe and stopped because trimming its parent group had also removed software iSCSI | Restore the IP initiator and boot helpers explicitly; retain it as a required configuration assertion; repeat the boot probe before writing media |
| Packaging | Old directory included diagnostics, unit identity, access keys, network data and proprietary assets | Curated text/source allowlist; archive scanner and hashes; no recursive copy of the lab tree |
| Installed overlay | Disposable deployment recipe created a named account, passwordless sudo, copied authorised keys and embedded UUIDs | None of those operations is included in the release overlay |
| Installed console geometry | Kernel handoff retained 160 by 50 cells, overflowing the native panel at the 16 by 32 font size | Stage the model-scoped helper source and a systemd unit ordered before getty; installation instructions build and enable it for console and desktop installs |
| Repeated login prompts | util-linux 2.42.3 refreshed a clock-bearing banner during network startup; getty had zero restarts | Document removing only the clock escape from the installed banner, with a backup; Alice confirmed the next boot stopped the spam; upstream issue 4306 matches the behaviour |
| Wi-Fi policy | Test helper forced a US-specific firmware country/revision and fixed interface name | Public helper only disables power saving; local firmware and regulatory setup are explicit installation work |
| Firmware rights | Apple extraction did not establish redistribution permission | Blobs/calibration excluded from source archive; binary ISO publication remains gated |
| Speaker licensing | Codec C declares GPL; added upstream headers have no explicit declaration and repo has no top-level licence | Preserve authorship; fetch pinned upstream separately; request clarification before publishing combined speaker binaries |
| Audio lifecycle | Speakers relied on firmware state lost by controller reset | Preserve narrowly scoped boot state; s2idle path requires opt-in, exact DMI/PCI identity and normal DMA stop |
| Audio helper | Runs in the user session, polls jack/nodes, has bounded subprocess calls | No shell interpretation, no network service, no microphone recording; existing moderate-volume first-run policy retained |
| Sleep | S3 broke internal input; EC wake mask failed without runtime capability marking | Model-specific S3 block, s2idle-only desktop policy and exact-model/GPE wake module |
| Desktop and live policy | Console hotkey/audio/lid handlers would compete with GNOME | Release desktop overlay uses ordinary user PipeWire/WirePlumber and GNOME/logind, without the console handlers |
| Headset experiment | Old validation codec included an unvalidated wired headset endpoint and extra register logging | Preserve source under `experimental/headset`; not part of default kernel preparation, pending a working physical headset |
| Rollback | A new build could replace the only working kernel | Build-only scripts never install; instructions retain the previous complete kernel/module/initramfs set |

## Code review observations

All included Python and shell source was read during consolidation. The model
hooks check MacBook8,1 before acting. The desktop audio helper has no arbitrary
command execution path, uses argument arrays rather than a shell, caps each
subprocess call at five seconds, and retries missing devices after resume.
It does not touch Bluetooth codecs or take over the default sink every poll.
Its first-run state file and PipeWire node identifiers are retained to reduce
behavioural changes from the physically tested system.

The keyboard-backlight sleep hook stores only a numeric brightness under
`/run`, blanks on entry and restores it on exit. The EC module checks the
machine vendor, exact model and expected GPE; no ACPI table or EC register
is rewritten. Its runtime wake flag persists until reboot, as documented.

The firmware-preserving audio path is still hardware-specific engineering.
The upstream codec mirrors internal HDA structures and has substantial
register-level setup; pinning the ABI and retaining the known working kernel
are necessary. This review does not turn that code into a generic upstream
driver or prove that every suspend/power-management transition is safe.
No active SPI/HDA hot-unbind is attempted by the release tooling.

Source extraction verifies the archive hash before creating its output tree,
uses the tar data filter and applies patches without fuzz. Speaker inputs are
read from exact Git objects. Target staging preflights every destination,
rejects symlink escapes and refuses differing existing files before copying.
Archive assembly uses an explicit allowlist, rejects symlinks/binary inputs
and common credential patterns, fixes metadata and emits per-file hashes.
The scanner is a backstop alongside manual review, not proof that arbitrary
unreviewed files would be safe to add.

## Verification

The consolidated patch stack applied to the pristine pinned archive without
fuzz. `olddefconfig` resolved the trimmed profile with all required drivers and
no unexpected loss from the protected peripheral set. Enabled symbols changed
from 7486 to 6687. The three PC Card Bluetooth drivers removed with PC Card
support are expected exceptions. The full configuration difference is in
`kernel-config-report.json`.

Final compiler, syntax, staging-boundary and archive checks are recorded in
`verification.json` alongside this document. Build logs and local binary
candidates remain in the private build workspace, outside the source archive.

The consolidated kernel has now booted on a physical MacBook8,1 to a console
with owner firmware, Ethernet, Wi-Fi association and camera enumeration. The
installed geometry correction passed a further reboot: 144 columns by 45
rows, helper exit status zero before getty started, and no failed system units.
The target-compiled helper and exact release unit were used. This is not a
fresh full-reinstall test or the broader audio/sleep/Bluetooth/HDMI regression.

## Remaining publication gates

The source kit may be reviewed independently now. A public binary ISO still
requires resolution or omission of proprietary firmware and unclearly licensed
speaker additions, compliance for every bundled Gentoo package, a clean image
assembly path, auditing both the root filesystem and initramfs, and physical
regression of the consolidated kernel. Existing private media are not cleared
by this source audit. No GitHub repository, release or public upload is created
by these packaging scripts.
