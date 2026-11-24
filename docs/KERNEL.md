# Kernel scope

MacBook8,1 is a fixed Intel/ACPI platform. Its USB-C port does not provide
Thunderbolt or PCIe tunnelling. The board has no replaceable PCIe cards.
It is therefore reasonable to remove drivers for hardware that cannot be
present on that board or attached through its supported external buses.

This means changing **Kconfig selections**, not deleting device IDs from
shared drivers or deleting arbitrary source directories. Linux compiles for
one architecture already; most ARM board device trees were never built here.
Keep ACPI, PCI core, I2C/SPI, DMA infrastructure and useful Open Firmware helpers
when selected by shared dependencies. An apparently unused bus controller is
not evidence that all of its supporting code is unnecessary.

## Baseline inventory

The inventory below contains model-level PCI IDs, with no machine serial,
MAC address, filesystem UUID or Bluetooth pairing material.

| Function | PCI identity | Required support |
| --- | --- | --- |
| Host bridge | Intel `8086:1604` | x86/PCI/uncore |
| Intel HD Graphics 5300 | `8086:161e` | i915, DRM/KMS, fbcon |
| Display audio | `8086:160c` | HDA Intel and HDMI codec |
| USB host | `8086:9cb1` | xHCI PCI |
| Serial IO DMA | `8086:9ce0` | DesignWare DMA/Intel LPSS dependencies retained |
| I2C | `8086:9ce2` | Intel LPSS/I2C dependencies retained |
| SPI | `8086:9ce6` | PXA2xx PCI/SPI, applespi, scoped PIO quirk |
| Bluetooth UART | `8086:9ce3` | 8250 LPSS, serdev, HCI UART Broadcom, scoped PIO quirk |
| MEI | `8086:9cba` | mei_me retained |
| Analogue audio | `8086:9ca0`, subsystem `8086:7270` | Patched HDA Intel, generic parser and CS420x codec |
| LPC, SMBus, thermal | `8086:9cc7`, `8086:9ca2`, `8086:9ca4` | lpc_ich, i2c_i801, Intel PCH thermal |
| Wi-Fi | Broadcom `14e4:43a3`, revision 05 | brcmfmac PCIe and matching firmware/calibration |
| Camera | Broadcom `14e4:1570` | External facetimehd module, V4L2 and DMA-SG |
| Internal SSD | Apple `106b:2001` | NVMe, EFI and filesystem support |

## Conservative 1.0 trimming

`scripts/configure-kernel.py` resolves the complete baseline with `olddefconfig`.
It disables native ATA/PATA/SATA controllers, low-level SCSI HBAs, PC Card/EISA/ISA
PnP, FireWire, Thunderbolt/USB4, impossible discrete GPUs, alternative SoC audio,
InfiniBand and selected PCI-only wired NIC families. SCSI core remains because
USB disks, optical drives and other USB storage can depend on it. The low-level
group is resolved empty before restoring software iSCSI/TCP and its boot
helpers: an IP initiator can use USB Ethernet and is also probed by Gentoo's
generic initramfs. It must not be discarded as an impossible physical HBA.
Native USB,
HID, USB Ethernet/Wi-Fi, USB audio, Bluetooth and Type-C support are retained.
The script checks required model drivers and compares peripheral selections
after dependency resolution, then writes `config-report.json`.

Do not use `localmodconfig` on a quiet boot: it would miss the USB devices and
Bluetooth profiles that were not connected during that one observation.
Retain a reference profile and the previous bootable kernel. The trimmed
configuration is a new candidate until a physical reboot and regression pass.
Unused modular drivers usually cost disk/build time rather than runtime RAM;
this is not a promise that pruning will make GNOME substantially faster.

## Patch stack

1. SPI PIO/runtime-PM quirk adapted from Shih-Yuan Lee's work.
2. Skip the conflicting SSD-debug serdev endpoint on MacBook8,1.
3. Use PIO only for the model's internal Broadcom UART.
4. Suppress unsupported S3 registration on this model.
5. Preserve firmware-initialised HDA link state at probe and, with an explicit
   opt-in, through s2idle. DMA still stops normally.
6. Avoid generic codec initialisation that destroys the working TDM state.

The speaker codec comes from the separately pinned upstream source. The EC wake
module verifies Apple/MacBook8,1 and GPE `0x4e` before marking that existing
interrupt wake-capable. Removing the module does not undo the ACPICA flag;
reboot to return to the initial state. It does not rewrite ACPI tables.

The HDA workaround keeps the controller in D0 through s2idle. That passed
physical playback/resume checks, but sleep power consumption is unmeasured.
The ABI depends on the pinned kernel and speaker revision. Rebuild all modules
together when changing either; never transplant old modules across versions.
