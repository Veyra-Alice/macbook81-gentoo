# Credits

This work depends on years of Linux hardware support and on other people's
specific investigations. We distinguish those contributions from our own.

| Contributor or project | Contribution used here | Licence or treatment |
| --- | --- | --- |
| Linux developers, including the ALSA, ACPI, SPI, serial, graphics, input and networking maintainers | Kernel and drivers underlying every hardware path | Linux GPL-2.0-only as a whole; retain each file's notices |
| Shih-Yuan Lee | Proposed MacBook8,1 SPI PIO/runtime-PM fix, adapted to the pinned kernel | Kernel derivative; original attribution retained in patch |
| Thomas Shirley, `thomas-shirley/macbook8.1-speaker-driver` | Essential CS4208/TDM speaker implementation and investigation of firmware-initialised audio state | Pinned source fetched separately; see licence caveat below |
| `davidjo/snd_hda_macbookpro` | Earlier audio work credited by the speaker implementation | Transitive credit; no independent claim of authorship here |
| `leifliddy/macbook12-audio-driver` | Earlier 12-inch MacBook audio work credited by the speaker implementation | Transitive credit; no independent claim of authorship here |
| Takashi Iwai and ALSA contributors | Original CS420x codec, generic HDA parser and controller infrastructure | Upstream SPDX and copyright notices retained |
| `omnidecker/macbook81-bluetooth` | Independent diagnosis of the conflicting SSD debug endpoint and Bluetooth UART enumeration | Research reference; their code is not vendored |
| Pablo Magana, `pmgart/macbook8-1-debian-guide` | Headset VREF and speaker-clock investigation informed our separate experimental capture endpoint | Research reference; Debian installation scripts not executed or vendored |
| Patrik Jakobsson and `patjak/facetimehd` contributors | FaceTime HD camera driver | GPL-2.0; build from pinned source |
| `patjak/facetimehd-firmware` contributors | Camera firmware download, extraction and hash checking | Extractor licence is separate from Apple's binary firmware rights |
| Gentoo developers | Distribution, stage3, package recipes, signed binary packages and installer foundation | Individual package licences retained; no Gentoo endorsement implied |
| Liberation font contributors, Google and Red Hat | Source font used to generate the readable 32-pixel GRUB font in the clean test media | SIL Open Font License 1.1, retained alongside the font |
| BlueZ, PipeWire and WirePlumber developers | Bluetooth, audio transport, session policy and documented configuration interfaces | System packages retain their own licences; not bundled in source archive |
| `atar-axis/xpadneo` contributors | Published troubleshooting informed the Xbox pairing experiment | Documentation reference; xpadneo is not required or installed |
| Apple, Broadcom and Intel | Hardware and firmware used for testing | Proprietary firmware is separately supplied, not covered by our MIT licence |

## Our contribution

Alice performed the physical testing, hardware work, listening checks and
design review. Veyra developed and reviewed the integration, build tooling,
diagnostics and documentation with Alice. This is explicitly a human/AI
collaboration, not a claim that all the underlying driver work originated here.

Our work includes the Linux 6.18 SPI adaptation, model-specific Bluetooth PIO
quirk, narrowed controller/parser integration, opt-in s2idle HDA-link preservation,
EC wake-capability module, model-specific S3 exclusion, console geometry helper,
desktop audio routing, build integration and the recorded validation programme.
Some fixes combine published upstream ideas with new implementation and tests.
Our speaker support would not exist in its present form without Thomas Shirley's
implementation. His README credits Claude for substantial development work;
we preserve that disclosure without implying that we independently audited
his development history.

## Pinned upstream references

* [Linux licensing rules](https://www.kernel.org/doc/html/latest/process/license-rules.html)
* [Shih-Yuan Lee's SPI patch](https://lists.openwall.net/linux-kernel/2026/09/30/2141)
* [Speaker driver](https://github.com/thomas-shirley/macbook8.1-speaker-driver),
  commit `fe54ad1aa7d8448fc49c0b5c8b353c50e2b1b8a1`
* [davidjo's audio work](https://github.com/davidjo/snd_hda_macbookpro)
* [leifliddy's audio work](https://github.com/leifliddy/macbook12-audio-driver)
* [Bluetooth investigation](https://github.com/omnidecker/macbook81-bluetooth)
* [MacBook8,1 Debian guide](https://github.com/pmgart/macbook8-1-debian-guide),
  commit `86e996c987f01144e671569e56277f9223a1519b`
* [FaceTime HD](https://github.com/patjak/facetimehd),
  commit `4159eef064e4170cbd94fd6c633cbd04bf589c4d`
* [Camera firmware extractor](https://github.com/patjak/facetimehd-firmware),
  commit `961774dc3bbcb77c5b1ed257b179fb37d0d9534e`
* [Xbox troubleshooting](https://github.com/atar-axis/xpadneo/blob/master/docs/TROUBLESHOOTING.md)
* [PipeWire filter chains](https://docs.pipewire.org/page_module_filter_chain.html)
* [WirePlumber ALSA configuration](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/alsa.html)

The pinned speaker repository has GPL-2.0-or-later SPDX headers on its codec C
files but no top-level licence file, and its added setup/PCM headers have no
explicit licence declaration. This release does not silently assign MIT terms
to those headers or vendor them in the source archive. The build reads them
from the pinned upstream checkout. Clarification is needed before describing
a downloadable combined speaker binary as fully cleared for redistribution.
Fetching separately is not itself a resolution of that licence question.
