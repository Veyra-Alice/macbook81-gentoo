#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Resolve the MacBook8,1 profile with Kconfig, retaining USB peripherals.

Writes only an explicitly supplied, separate kernel output directory.
Does not build, install, or alter the reference configuration.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

# No native SATA, FireWire, expansion slots, discrete GPU, sound card or HBA.
# USB storage retains SCSI core, sd/sr/sg/st, UAS and USB-storage transports.
DISABLE = {
    'ATA': 'No internal SATA/PATA controller; USB SATA bridges use USB storage',
    'PCCARD': 'No PCMCIA/CardBus slot',
    'EISA': 'No EISA slots',
    'ISAPNP': 'No ISA plug-and-play devices',
    'FIREWIRE': 'No FireWire controller or Thunderbolt expansion',
    'USB4': 'USB-C port carries USB/DisplayPort, not Thunderbolt/USB4',
    'DRM_AMDGPU': 'No AMD discrete GPU or eGPU path',
    'DRM_RADEON': 'No Radeon GPU or eGPU path',
    'DRM_NOUVEAU': 'No NVIDIA GPU or eGPU path',
    'DRM_XE': 'Broadwell graphics use i915',
    'SND_SOC': 'No alternative SoC audio machine; retain HDA, USB and Bluetooth',
    'SND_FIREWIRE': 'No FireWire audio transport',
    'INFINIBAND': 'No InfiniBand PCI adapter or external PCI expansion',
    'NET_VENDOR_MELLANOX': 'No Mellanox PCI adapter',
    'NET_VENDOR_BROADCOM': 'No Broadcom wired PCI NIC; brcmfmac is separate',
    'NET_VENDOR_INTEL': 'No Intel wired PCI NIC; USB Ethernet is separate',
    'NET_VENDOR_CHELSIO': 'No Chelsio PCI adapter',
    'NET_VENDOR_QLOGIC': 'No QLogic PCI adapter',
    'NET_VENDOR_NETRONOME': 'No Netronome PCI adapter',
    'NET_VENDOR_SOLARFLARE': 'No Solarflare PCI adapter',
    'NET_VENDOR_SFC': 'No Solarflare PCI adapter',
    'SPEAKUP': 'Avoid inherited Caps Lock interception; desktop accessibility remains',
}

# Assert the whole known USB/peripheral support set survives Kconfig resolution.
# Keep OF infrastructure: it can be selected by useful shared subsystems even
# though this x86 machine boots through ACPI, not a board device tree.
PROTECTED_PREFIXES = ('USB_', 'HID_', 'BT_', 'INPUT_', 'JOYSTICK_',
                      'SND_USB', 'SND_FIREWIRE', 'TYPEC', 'UCSI', 'NLS_')
REQUIRED = {
    'X86_64', 'ACPI', 'EFI', 'PCI', 'BLK_DEV_NVME', 'KEYBOARD_APPLESPI',
    'SPI_PXA2XX', 'SPI_PXA2XX_PCI', 'PINCTRL_LYNXPOINT', 'SERIAL_8250_LPSS',
    'SERIAL_DEV_BUS', 'BRCMFMAC', 'BRCMFMAC_PCIE', 'DRM_I915',
    'SND_HDA_INTEL', 'SND_HDA_CODEC_CS420X', 'SND_HDA_CODEC_HDMI',
    'SND_HDA_GENERIC', 'USB_XHCI_HCD', 'USB_XHCI_PCI', 'USB_STORAGE',
    'USB_UAS', 'SCSI', 'ISCSI_TCP', 'BLK_DEV_SD', 'USB_NET_AX8817X', 'USB_RTL8152',
    'SND_USB_AUDIO', 'HID_APPLE', 'HID_MAGICMOUSE', 'HID_MICROSOFT',
    'BT', 'BT_HCIUART', 'BT_HCIUART_BCM', 'MEDIA_SUPPORT', 'VIDEO_DEV',
    'VIDEOBUF2_DMA_SG', 'I2C', 'I2C_I801', 'INTEL_PCH_THERMAL',
    'SENSORS_APPLESMC', 'SUSPEND', 'EXT4_FS', 'VFAT_FS', 'SQUASHFS',
}


def read_config(path):
    result = {}
    for line in path.read_text().splitlines():
        if line.startswith('CONFIG_'):
            key, value = line[7:].split('=', 1)
            result[key] = value
        elif re.fullmatch(r'# CONFIG_\w+ is not set', line):
            result[line[9:-11]] = 'n'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--profile', choices=['reference', 'trimmed'], default='trimmed')
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if source == output or source in output.parents:
        parser.error('Use a separate output directory outside the source tree')
    if (output / '.config').exists():
        parser.error('Output already configured; use a new directory')
    output.mkdir(parents=True, exist_ok=True)
    baseline = ROOT / 'kernel/reference.config'
    shutil.copyfile(baseline, output / '.config')
    before = read_config(baseline)
    commands = ['--set-str', 'LOCALVERSION', '-macbook81-1.0.0',
                '--disable', 'LOCALVERSION_AUTO', '--disable', 'BRCMDBG']
    if args.profile == 'trimmed':
        for symbol in DISABLE:
            if symbol in before:
                commands += ['--disable', symbol]
        # Resolve the empty hardware-driver group first, then restore its
        # software initiator. iSCSI can use USB Ethernet and is also probed by
        # the generic Gentoo initramfs; it is not an impossible PCI device.
        commands += ['--disable', 'SCSI_LOWLEVEL']
    # External facetimehd needs its DMA-SG dependency even if media selection changes.
    commands += ['--module', 'VIDEOBUF2_DMA_SG']
    subprocess.run([str(source / 'scripts/config'), '--file', str(output / '.config'),
                    *commands], check=True)
    subprocess.run(['make', '-C', str(source), 'O=' + str(output), 'olddefconfig'], check=True)
    if args.profile == 'trimmed':
        subprocess.run([str(source / 'scripts/config'), '--file', str(output / '.config'),
                        '--enable', 'SCSI_LOWLEVEL', '--module', 'ISCSI_TCP',
                        '--module', 'ISCSI_BOOT_SYSFS', '--enable', 'ISCSI_IBFT_FIND',
                        '--module', 'ISCSI_IBFT'], check=True)
        subprocess.run(['make', '-C', str(source), 'O=' + str(output), 'olddefconfig'], check=True)
    after = read_config(output / '.config')
    missing = [s for s in REQUIRED if after.get(s, 'n') not in ('y', 'm')]
    lost = [s for s, value in before.items()
            if s.startswith(PROTECTED_PREFIXES) and value in ('y', 'm')
            and after.get(s, 'n') == 'n'
            # PCI-only host controllers and explicitly removed FireWire are allowed.
            and s not in {'USB_OHCI_HCD_SSB', 'USB_OHCI_HCD_BCMA',
                          'BT_HCIDTL1', 'BT_HCIBT3C', 'BT_HCIBLUECARD'}
            and not s.startswith('SND_FIREWIRE')]
    report = {'profile': args.profile, 'missing_required': sorted(missing),
              'lost_peripherals': sorted(lost), 'disabled_groups': DISABLE if args.profile == 'trimmed' else {},
              'enabled_before': sum(v in ('y', 'm') for v in before.values()),
              'enabled_after': sum(v in ('y', 'm') for v in after.values()),
              'changes': {s: [before.get(s, 'n'), after.get(s, 'n')]
                          for s in sorted(before.keys() | after.keys())
                          if before.get(s, 'n') != after.get(s, 'n')}}
    (output / 'config-report.json').write_text(json.dumps(report, indent=2) + '\n')
    if missing or lost:
        raise SystemExit('Configuration needs review: ' + json.dumps({'missing': missing, 'lost': lost}))
    print(f"Enabled symbols: {report['enabled_before']} -> {report['enabled_after']}")


if __name__ == '__main__':
    main()
