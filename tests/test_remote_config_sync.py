import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import xml_Utils as config


def configuration(model):
    return f"""<Remote_Configuration>
    <Server hostname="build-host">
        <remote_directory IMGDesignScheme="A33" has_ui="false" level="1">/build/{model}/</remote_directory>
        <remote_template_path>/icc/</remote_template_path>
        <remote_currency_template_path>/icc/01_Currencys/</remote_currency_template_path>
        <remote_ui_file_template_path>/icc/20_UI/</remote_ui_file_template_path>
    </Server>
    <IMG_DesignScheme val="A33" />
</Remote_Configuration>""".encode()


class RemoteConfigTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.files = ExitStack()
        self.addCleanup(self.files.close)
        self.folder = Path(self.files.enter_context(tempfile.TemporaryDirectory()))
        self.cache = self.folder / "remote_config.xml"
        self.original = configuration("UN220M")
        self.cache.write_bytes(self.original)
        ssh_settings = ET.fromstring("<ssh><hostname>build-host</hostname></ssh>")
        self.files.enter_context(patch.multiple(
            config, REMOTE_CONFIG_PATH=self.cache, _active_remote_config=self.original,
            remote_config_tree=ET.ElementTree(ET.fromstring(self.original)),
            ssh_config_root=ssh_settings, ssh_config_tree=ET.ElementTree(ssh_settings),
        ))
        self.sftp = MagicMock()
        self.client = AsyncMock()
        self.client.get_sftp.return_value = self.sftp
        self.read = self.sftp.open.return_value.__aenter__.return_value.read

    async def test_upstream_content_replaces_newer_cache_and_live_tree(self):
        self.read.return_value = configuration("UN260")
        os.utime(self.cache, (2_000_000_000, 2_000_000_000))
        self.assertTrue(await config.sync_remote_config(self.client))
        self.assertEqual(self.cache.read_bytes(), self.read.return_value)
        self.assertEqual(config.get_remote_directorys(), ["/build/UN260/"])
        self.assertFalse(config.has_ui("/build/UN260/"))
        self.assertFalse(await config.sync_remote_config(self.client))

    async def test_invalid_or_unavailable_update_preserves_last_working_copy(self):
        for content in (b"<broken", configuration("UN260").replace(b"build-host", b"wrong-host")):
            self.read.return_value = content
            with self.assertRaises(ValueError):
                await config.sync_remote_config(self.client)
        self.read.side_effect = OSError("offline")
        with self.assertRaises(OSError):
            await config.sync_remote_config(self.client)
        self.assertEqual(self.cache.read_bytes(), self.original)
        self.assertEqual(config.get_remote_directorys(), ["/build/UN220M/"])

    async def test_failed_replace_keeps_old_file_and_active_tree(self):
        self.read.return_value = configuration("UN260")
        with patch("xml_Utils.os.replace", side_effect=PermissionError("file in use")):
            with self.assertRaises(PermissionError):
                await config.sync_remote_config(self.client)
        self.assertEqual(self.cache.read_bytes(), self.original)
        self.assertEqual(list(self.folder.iterdir()), [self.cache])
        self.assertEqual(config.get_remote_directorys(), ["/build/UN220M/"])

    async def test_currency_sync_never_installs_a_new_machine_config(self):
        self.sftp.listdir = AsyncMock(return_value=["remote_config.xml"])
        self.sftp.get = AsyncMock()
        with patch.object(config, "get_text", return_value=str(self.folder)), \
             patch.object(config, "get_remote_currency_template_path", return_value="/icc/01_Currencys/"):
            self.assertFalse(await config.sync_currencys_xml(self.client))
        self.sftp.get.assert_not_called()
        self.assertEqual(self.cache.read_bytes(), self.original)

    def test_legacy_startup_then_prefer_configured_currency_directory(self):
        self.cache.write_bytes(configuration("OLD"))
        (self.folder / "ssh_config.xml").write_text(
            "<ssh><hostname>build-host</hostname>"
            "<local_original_currencys_xml_path>./templates/</local_original_currencys_xml_path>"
            "<local_currencys_xml_path>./new_currencys/</local_currencys_xml_path></ssh>",
            encoding="utf-8",
        )
        env = dict(os.environ, PYTHONPATH=str(Path(config.__file__).parent))
        def check_startup(model):
            subprocess.run(
                [sys.executable, "-c", f"import xml_Utils as c; assert c.get_remote_directorys() == ['/build/{model}/']"],
                cwd=self.folder, env=env, check=True, capture_output=True, timeout=15,
            )
        check_startup("OLD")
        templates = self.folder / "templates"
        templates.mkdir(exist_ok=True)
        (templates / "remote_config.xml").write_bytes(configuration("NEW"))
        check_startup("NEW")
