# SPDX-License-Identifier: MIT
"""Safety boundaries for staging and releasing a hardware support kit."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StagingBoundaries(unittest.TestCase):
    def stage(self, root):
        return subprocess.run(['python3', str(ROOT / 'scripts/stage-desktop.py'), '--root', str(root)],
                              capture_output=True, text=True)

    def gentoo(self, root):
        (root / 'etc').mkdir()
        (root / 'etc/gentoo-release').write_text('Gentoo test target\n')

    def test_wrong_target_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = self.stage(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(root.iterdir()), [])

    def test_symlink_escape_rejected_before_copying(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, outside = Path(temporary) / 'root', Path(temporary) / 'outside'
            root.mkdir()
            outside.mkdir()
            self.gentoo(root)
            (root / 'usr').symlink_to(outside)
            self.assertNotEqual(self.stage(root).returncode, 0)
            self.assertEqual(list(outside.iterdir()), [])
            self.assertFalse((root / 'etc/pipewire').exists())

    def test_preflight_preserves_local_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.gentoo(root)
            destination = root / 'etc/modprobe.d/macbook81-speaker.conf'
            destination.parent.mkdir()
            destination.write_text('local custom configuration\n')
            self.assertNotEqual(self.stage(root).returncode, 0)
            self.assertEqual(destination.read_text(), 'local custom configuration\n')
            self.assertFalse((root / 'usr').exists())

    def test_staging_is_idempotent_and_adds_no_remote_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.gentoo(root)
            self.assertEqual(self.stage(root).returncode, 0)
            self.assertEqual(self.stage(root).returncode, 0)
            self.assertTrue((root / 'usr/local/bin/macbook81-desktop-audio.py').is_file())
            self.assertTrue((root / 'usr/local/src/macbook81/fit-macbook81-console.c').is_file())
            self.assertTrue((root / 'etc/systemd/system/macbook81-console-fit.service').is_file())
            self.assertFalse((root / 'etc/ssh').exists())
            self.assertFalse((root / 'etc/sudoers.d').exists())
            self.assertFalse((root / 'etc/fstab').exists())


class SourceRelease(unittest.TestCase):
    def test_archive_is_deterministic_and_manifest_covers_every_input(self):
        package = load('package-source')
        files = package.release_files()
        first = package.build_archive(files)
        self.assertEqual(first, package.build_archive(files))
        with tarfile.open(fileobj=io.BytesIO(first), mode='r:gz') as archive:
            names = archive.getnames()
            self.assertEqual(len(names), len(files) + 1)
            self.assertTrue(all(name.startswith(package.NAME + '/') for name in names))
            self.assertTrue(all(item.isfile() for item in archive))
            self.assertFalse(any('/work/' in name or '/private/' in name for name in names))
            manifest = archive.extractfile(package.NAME + '/MANIFEST.sha256').read().decode()
            self.assertEqual(len(manifest.splitlines()), len(files))

    def test_kernel_config_parser_handles_disabled_options(self):
        config = load('configure-kernel')
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'config'
            path.write_text('CONFIG_USB=y\nCONFIG_SND_USB_AUDIO=m\n# CONFIG_ATA is not set\n')
            self.assertEqual(config.read_config(path), {'USB': 'y', 'SND_USB_AUDIO': 'm', 'ATA': 'n'})


if __name__ == '__main__':
    unittest.main()
