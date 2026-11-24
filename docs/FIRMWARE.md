# Firmware and redistribution

Working firmware is not necessarily freely redistributable firmware. Source
code licences on extractors do not grant rights to Apple's extracted binaries.
No firmware blob, raw memory capture, hardware calibration, macOS component,
IPSW, Windows driver or microcode binary is included in this source archive.

See [owner-supplied firmware instructions](OWNER_FIRMWARE.md) for the exact
IPSW, filesystem paths, hashes, Big Sur research offset and remaining board-data
extraction limitation. The clean test media require Ethernet initially.

| Component | Working development provenance | Public release treatment |
| --- | --- | --- |
| Wi-Fi executable | Broadcom 4350 C2 FullMAC, 7.63.81.2, extracted from Apple iPad software | Separately supplied; no redistribution grant established |
| Wi-Fi regulatory data | Matching `rieslinga` CLM data from that firmware family | Separately supplied; do not mix arbitrary chip revisions |
| Wi-Fi board data | Extracted from the physical test machine's macOS-initialised state | Not bundled; use calibration for the actual machine |
| Camera firmware and sensor files | `patjak/facetimehd-firmware` extractor at pinned revision | Use the upstream extraction/verification workflow; Apple's binaries are separate |
| Bluetooth | Tested with the controller's existing firmware/stock Linux support | No additional private Bluetooth firmware blob required by the tested setup |
| Intel microcode | Intel release file for CPUID family/model/stepping `06-3d-04` | Prefer Gentoo's normal microcode package and retain Intel's licence |
| Graphics firmware, if requested | Distribution firmware package | Use the appropriate distribution package and per-file licence |

The Wi-Fi loader expects the appropriate `brcmfmac4350c2-pcie.bin`, associated
CLM and board-data files under `/lib/firmware/brcm/`. Filenames alone do not
establish compatibility: C2 and C5 firmware are not interchangeable. Do not
rename a random firmware image to force it to load. The working image used
the test machine's board configuration and a US-specific firmware country
selection; that is a record of an experiment, not a worldwide regulatory
configuration. WPA3 was not achieved by this firmware substitution.

Camera assets normally reside under `/lib/firmware/facetimehd/`. The upstream
extractor verifies known firmware and calibration hashes. Camera firmware
should not be confused with the separate GPL camera kernel driver.

Before a binary ISO is published, either establish the relevant redistribution
permission or omit the affected assets and provide a documented owner-supplied
installation path. A firmware-free ISO will have reduced out-of-box wireless
and camera functionality; document that honestly. Public source release can
proceed independently of publishing those proprietary assets.
