# Owner-supplied Apple firmware

The clean test media omit Broadcom Wi-Fi firmware, CLM data, unit-specific
radio calibration and FaceTime camera firmware. USB Ethernet works without
these files. They are not needed to boot or install Gentoo. Other firmware
already shipped by Gentoo, including licensed Intel microcode, is a separate
category; this is not an entirely firmware-free distribution.

These notes identify the exact development inputs. They do not establish
permission to redistribute Apple's files, nor promise that the board data
from one MacBook are appropriate for another. Work from software you are
entitled to use. Keep extracted files and hardware captures local.

## Wi-Fi executable and matching CLM

The working experiment used the iPad Air 2 (`iPad5,3`) iOS 15.8.8 restore,
build `19H422`. Downloaded archive:

* Filename: `iPad_64bit_TouchID_15.8.8_19H422_Restore.ipsw`
* Size: `5046203202` bytes
* SHA256: `4de5c8c453328205b1e741faae218ee0f7848993334ff77f690c5a64a765a623`
* [Apple CDN archive](https://updates.cdn-apple.com/2025FallFCS/fullrestores/122-77369/9704B32E-FACF-4595-93E4-E35EDD25E793/iPad_64bit_TouchID_15.8.8_19H422_Restore.ipsw)

The IPSW is a ZIP. Its root filesystem is `098-68727-067.dmg`. Our extraction
used 7-Zip 26.06, which read its LZFSE/APFS contents without mounting or
decrypting it. Check the archive hash before extraction; offsets and paths
below are specific to this version.

```sh
unzip iPad_64bit_TouchID_15.8.8_19H422_Restore.ipsw 098-68727-067.dmg
7zz e -so 098-68727-067.dmg \
  usr/share/firmware/wifi/C-4350__s-C2/rieslinga.trx \
  > brcmfmac4350c2-pcie.bin
7zz e -so 098-68727-067.dmg \
  usr/share/firmware/wifi/C-4350__s-C2/rieslinga.clmb \
  > brcmfmac4350c2-pcie.clm_blob
sha256sum brcmfmac4350c2-pcie.bin brcmfmac4350c2-pcie.clm_blob
```

Expected outputs:

| Linux filename | Bytes | SHA256 |
| --- | --- | --- |
| `brcmfmac4350c2-pcie.bin` | 610480 | `fb1c8d1d73c6742226bd12a19d09630190f4cac053792a6bae96aab6bc1e59f8` |
| `brcmfmac4350c2-pcie.clm_blob` | 7250 | `3d833615a2abb45d0e601c58344118eb22360576aeb59f8fa36ef02c854a0963` |

The executable identifies itself as `7.63.81.2`, dated September 2019.
The `.trx` file is copied whole. The CLM file must also remain the complete
7250-byte BLOB container: extracting only its inner CLM DATA segment failed
with error `-52` in our test. Do not substitute the C5 `zinfandela` files.

## Board data are a separate requirement

The tested configuration also needed a NVRAM board-variable file for the actual
MacBook, installed as `brcmfmac4350c2-pcie.txt`. It contains antenna/radio
calibration and device identity. We obtained ours through a temporary,
instrumented Linux driver, sampling the firmware-initialised chip RAM during
boot. It was not a simple universally located file in Big Sur.

That diagnostic driver and another machine's calibration are deliberately
not part of the release defaults. We do not yet provide a general, validated
owner-extraction tool for this step. If you do not already have verified board
data for your unit, use Ethernet while that workflow is developed. Do not
invent calibration values, copy another unit's MAC address or blindly force
the US-only country/revision used in the laboratory experiment.

With all three appropriate files available, install them under
`/lib/firmware/brcm/` in the live system or installed target, then reboot.
Files copied into a RAM-backed live session disappear on reboot unless also
installed into the target filesystem. Rebuild the target initramfs if it
contains an earlier copy. WPA3 remains unresolved with this combination.

## Replacement-board validation plan

The next extraction-procedure test will use a replacement logic board with a
fresh Big Sur installation. Collect that board's identity and owner calibration
before replacing macOS, then validate the result with this Linux support kit.
This is planned work, not an available general extraction utility. Do not
carry the previous board's radio data across merely because the Mac model
is unchanged. Board-specific private images remain distinct from the public
source kit and firmware-omitting live media; extraction tooling can follow in
a later maintenance release once validated.

## Why the Big Sur executable is not an alternative

For comparison, the investigated Big Sur file was:

`/System/Library/Extensions/IO80211Family.kext/Contents/PlugIns/AirPortBrcmNIC.kext/Contents/MacOS/AirPortBrcmNIC`

Its SHA256 was
`4b3469b370e43237081a5c161d64656d0150c91c81ed419d389262f6099823f7`.
The embedded `4350pci-bmac` 7.77.0.0 image starts at **file offset
`0x5eb590`**, length **616276** bytes, with extracted SHA256
`3a06933d1396a7f12538f0678b1df588f70172b1d6014f82f0e5d9a445505acc`.
Those offsets apply only to that exact input. This is an Apple BMAC/RPC image,
not the PCIe MSGBUF executable expected by Linux `brcmfmac`. Renaming it does
not make it compatible. It was a research input, not the working Linux blob.

## Camera

Use [Patrik Jakobsson's firmware extractor](https://github.com/patjak/facetimehd-firmware)
at pinned commit `961774dc3bbcb77c5b1ed257b179fb37d0d9534e`, following its
documented download, extraction and checksum workflow. Install its verified
firmware and appropriate calibration files under `/lib/firmware/facetimehd/`
in the target. The separately compiled GPL camera module is included; the
Apple firmware is not. Reboot after installing it rather than experimenting
with live controller unbinds.
