import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from rich.syntax import Syntax
from textual.app import App
from textual.widgets import Button, Input, Static

from DownloadScreen import DownloadScreen
from FileBrowser import FileBrowser, FilteredDirectoryTree
from GetZPKApp import GetZPKApp, RemoteFloder


class TextualMigrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_startup_sync_and_model_refresh(self):
        scanned = []
        cached_files = {}
        sync_complete = asyncio.Event()

        def scan(folder):
            scanned.append(folder)
            return cached_files.get(folder, [])

        async def finish_sync(screen):
            cached_files["UN220M"] = ["ui_resource_UN220M.bin"]
            screen.query_one("#ok", Button).disabled = False
            sync_complete.set()

        with (
            patch.object(DownloadScreen, "on_mount", AsyncMock()),
            patch.object(DownloadScreen, "sync_files", finish_sync),
            patch("GetZPKApp.get_remote_directorys", return_value=["/build/UN220M/", "/build/UN260/"]),
            patch("GetZPKApp.has_ui", side_effect=lambda path: path != "/build/UN260/"),
            patch("GetZPKApp.scan_ui_files", side_effect=scan),
            patch("GetZPKApp.get_ui_file_time", return_value="2026-11-07"),
        ):
            app = GetZPKApp()
            async with app.run_test(size=(140, 48)) as pilot:
                await asyncio.wait_for(sync_complete.wait(), timeout=5)
                self.assertIsInstance(app.screen, DownloadScreen)
                done = app.screen.query_one("#ok", Button)
                self.assertFalse(done.disabled)
                done.press()
                await pilot.pause()
                self.assertEqual(len(app.screen_stack), 1)
                self.assertEqual(app.ui_file, "ui_resource_UN220M.bin")

                app.folder_container.select("UN260")
                await pilot.pause()
                await pilot.press("ctrl+r")
                self.assertEqual(app.ui_file, "")
                self.assertNotIn("UN260", scanned)
                self.assertTrue(app.query_one("#upload_ui_btn", Button).disabled)
                self.assertEqual(len(app.folder_container.query(RemoteFloder)), 2)

                app.folder_container.select("UN220M")
                await pilot.pause()
                self.assertEqual(app.ui_file, "ui_resource_UN220M.bin")
                self.assertFalse(app.query_one("#upload_ui_btn", Button).disabled)

    async def test_browser_filter_highlight_and_upload_shortcut(self):
        class BrowserApp(App):
            BINDINGS = [("ctrl+u", "sync_files", "Sync")]
            upload_calls = 0

            def action_sync_files(self):
                raise AssertionError("FileBrowser Ctrl+U invoked global sync")

            def action_upload_ui_file(self):
                self.upload_calls += 1

        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "UN260").mkdir()
            app = BrowserApp()
            async with app.run_test() as pilot:
                screen = FileBrowser()
                screen.path = folder
                await app.push_screen(screen)
                tree = screen.query_one(FilteredDirectoryTree)
                field = screen.query_one("#file_filter_input", Input)
                field.focus()
                field.value = "UN"
                await pilot.pause(0.4)
                self.assertEqual(tree.keywords, "UN")
                field.value = "UN260"
                await pilot.press("enter")
                await pilot.pause(0.4)
                self.assertIs(screen.query_one(FilteredDirectoryTree), tree)
                self.assertEqual(tree.keywords, "UN260")

                preview = screen.query_one("#code", Static)
                preview.update(Syntax("first\nsecond\n", "markdown"))
                screen.highlight_line(2)
                self.assertIn(2, preview.content.highlight_lines)
                tree.focus()
                await pilot.press("ctrl+u")
                self.assertEqual(app.upload_calls, 1)
