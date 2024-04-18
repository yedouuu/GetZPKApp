import time
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Grid, Center, Middle, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, ProgressBar, Static
import logging

from xml_Utils import (
    upload_currencys_xml,
    upload_ui_file,
    pack_zpk,
    download_zpk,
    get_ssh_config,
)
from SSHClient import SSH_Client

TEXT = """I must not fear.
Fear is the mind-killer.
Fear is the little-death that brings total obliteration.
I will face my fear.
I will permit it to pass over me and through me.
And when it has gone past, I will turn the inner eye to see its path.
Where the fear has gone there will be nothing. Only I will remain."""

class DownloadScreen(ModalScreen):
    """Screen with a dialog to quit."""
    ssh_client: SSH_Client | None = None

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("连接中...", id="question"),
            ProgressBar(total=100, show_eta=False, id="progress"),
            # Button("取消", variant="error", id="quit"),
            Button("完成", variant="success", disabled=True, id="ok"),
            id="dialog",
        )

    async def on_mount(self) -> None:
        ssh_config = get_ssh_config()
        self.ssh_client = SSH_Client(ssh_config["hostname"], ssh_config["port"], ssh_config["username"], ssh_config["password"])
        await self.ssh_client.connect()
        self.query_one("#question").update(f"连接成功")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.pop_screen()
        else:
            self.app.pop_screen()


    def change_status(self, status:str):
        self.query_one("#question").update(f"{status}")


    def update_progress(self, path, offset, size, _):
        # Ensure offset and size are integers
        if not isinstance(offset, int):
            offset = int.from_bytes(offset, 'big')  # Assuming big-endian byte order if offset is bytes

        if not isinstance(size, int):
            size = int.from_bytes(size, 'big')  # Adjust according to your data's byte order

        new_progress = 90
        # Calculate the percentage of completion
        percentage = float((float(offset) / size) * 10)  # From 90% to 100%
        new_progress += percentage

        # Update the progress bar
        # self.query_one("#progress").update(total=100, progress=new_progress)
        self.query_one("#progress").advance(percentage)
        self.app.refresh()


    def zpk_progress(self, line, total):
        # Ensure offset and size are integers
        if not isinstance(line, float):
            line = float(line)

        new_progress = 20

        # Calculate the percentage of completion
        percentage = ((line / total) * 70)  # From 20% to 90%
        new_progress += percentage
        #print(f"line/total={(line / total)*40}   precentage = {percentage}")

        # Update the progress bar
        self.query_one("#progress").advance(percentage)
        self.app.refresh()


    async def download(self, remote_folder, ui_file):
        try:
            self.change_status("上传currencys.xml...")
            await upload_currencys_xml(self.ssh_client, remote_folder)
            self.query_one("#progress").advance(10)

            self.change_status("上传ui_file...")
            await upload_ui_file(self.ssh_client, remote_folder, ui_file)
            self.query_one("#progress").advance(10)

            self.change_status("打包zpk...")
            await pack_zpk(self.ssh_client, remote_folder, self.zpk_progress)

            self.change_status("下载ZPK...")
            await download_zpk(self.ssh_client, remote_folder, self.update_progress)
            self.query_one("#progress").update(total=100, progress=100)
            self.query_one("#ok").disabled = False
            self.change_status("下载完成...")
        except Exception as e:
            logging.exception(e)
        finally:
            if self.ssh_client:
                await self.ssh_client.close()

class ModalApp(App):
    """An app with a modal dialog."""

    # CSS_PATH = "modal01.tcss"
    CSS = """  
    QuitScreen {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    Button {
        width: 100%;
    }
    """
    BINDINGS = [("q", "request_quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield ProgressBar()
        yield Footer()

    def action_request_quit(self) -> None:
        self.push_screen(DownloadScreen())


if __name__ == "__main__":
    app = ModalApp()
    app.run()