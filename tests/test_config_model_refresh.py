import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from textual.widgets import Button, Input

from DownloadScreen import DownloadScreen
from GetZPKApp import DownloadDesc, GetZPKApp, RemoteFloder


class ModelRefreshTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.paths = []
        self.next_paths = []
        self.without_ui = set()
        self.sync_completed = asyncio.Event()
        self.files = {"UN220M": ["ui_resource_UN220M_a.bin", "ui_resource_UN220M_b.bin"]}

        async def sync(screen):
            self.paths = self.next_paths.copy()
            screen.query_one("#ok", Button).disabled = False
            self.sync_completed.set()

        self.enterContext(patch.object(DownloadScreen, "on_mount", AsyncMock()))
        self.enterContext(patch.object(DownloadScreen, "sync_files", sync))
        self.enterContext(patch("GetZPKApp.get_remote_directorys", side_effect=lambda: self.paths.copy()))
        self.enterContext(patch("GetZPKApp.has_ui", side_effect=lambda path: path not in self.without_ui))
        self.scan = self.enterContext(patch("GetZPKApp.scan_ui_files", side_effect=lambda model: self.files.get(model, [])))
        self.enterContext(patch("GetZPKApp.get_ui_file_time", return_value="2026-11-07"))

    async def close_sync(self, app, pilot):
        await asyncio.wait_for(self.sync_completed.wait(), timeout=5)
        app.screen.query_one("#ok", Button).press()
        await pilot.pause()
        self.sync_completed.clear()

    async def test_sync_updates_models_paths_capabilities_and_selection(self):
        self.paths = ["/build/UN220M/", "/build/UN260/"]
        self.next_paths = self.paths.copy()
        app = GetZPKApp()
        async with app.run_test(size=(140, 48)) as pilot:
            await self.close_sync(app, pilot)
            app.ui_view.focus()
            await pilot.press("down", "enter")
            selected_ui = self.files["UN220M"][1]
            self.assertEqual(app.ui_file, selected_ui)

            field = app.folder_container.query_one(Input)
            field.value = "220"
            self.next_paths = ["/build/UN320/", "/moved/UN220M/"]
            await pilot.press("ctrl+u")
            await self.close_sync(app, pilot)
            self.assertEqual([button.id for button in app.folder_container.query(RemoteFloder)], ["UN320", "UN220M"])
            self.assertEqual(app.remote_folder_path, "/moved/UN220M/")
            self.assertEqual(app.ui_file, selected_ui)
            self.assertEqual(app.ui_view.cursor_row, 1)
            self.assertEqual(field.value, "220")
            self.assertTrue(app.query_one("#UN320").has_class("filtered"))

            self.without_ui.add("/moved/UN220M/")
            self.scan.reset_mock()
            await pilot.press("ctrl+u")
            await self.close_sync(app, pilot)
            self.assertEqual(app.ui_file, "")
            self.assertFalse(app.ui_view.display)
            self.assertTrue(app.query_one("#upload_ui_btn", Button).disabled)
            self.scan.assert_not_called()

            self.next_paths = ["/build/UN320/"]
            with patch.object(app, "notify") as notify:
                await pilot.press("ctrl+u")
                await self.close_sync(app, pilot)
            self.assertEqual(app.remote_folder_path, "/build/UN320/")
            self.assertEqual(app.query_one(DownloadDesc).remote_folder, "UN320")
            self.assertIn("UN220M", notify.call_args.args[0])

    async def test_empty_cache_can_sync_to_first_model(self):
        app = GetZPKApp()
        async with app.run_test(size=(140, 48)) as pilot:
            await self.close_sync(app, pilot)
            self.assertEqual(app.remote_folder, "")
            self.assertTrue(app.query_one("#information_download_btn", Button).disabled)
            self.assertTrue(app.query_one("#upload_ui_btn", Button).disabled)
            with patch("GetZPKApp.SSH_Client") as ssh:
                await pilot.press("ctrl+d")
                ssh.assert_not_called()

            self.next_paths = ["/build/UN260/"]
            self.without_ui.add(self.next_paths[0])
            await pilot.press("ctrl+u")
            await self.close_sync(app, pilot)
            self.assertEqual(app.remote_folder_path, "/build/UN260/")
            self.assertFalse(app.query_one("#information_download_btn", Button).disabled)
            self.assertTrue(app.query_one("#upload_ui_btn", Button).disabled)
            self.scan.assert_not_called()
