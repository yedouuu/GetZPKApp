import time
import asyncio

from colorama import Fore, Style, init

from rich.text import Text
from rich.markdown import Markdown


from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Container, Center, Middle, VerticalScroll, Horizontal, ScrollableContainer
from textual.reactive import reactive
from textual.timer import Timer
from textual.message import Message
from textual.widget import Widget
from Get_ZPK_OLD import Get_ZPK_OLD_main
from xml_Utils import (
    get_open_country,
     scan_ui_files,
     get_text,
     get_remote_directorys,
     get_remote_directory_version,
     get_ui_file_time,
     get_open_country,
)
from textual.widgets import (
    Static, 
    Pretty, 
    Button, 
    Footer, 
    Header, 
    TextArea, 
    ProgressBar, 
    Input, 
    OptionList, 
    Label, 
    Placeholder, 
    DataTable,
    
)
# import os
# import sys
# BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# print(BASE_PATH)
# sys.path.append(BASE_PATH)


class RemoteFloder(Button):
    """Display remote folders."""
        

class FolderContainer(VerticalScroll):
    """A container to display remote folders."""
    folder_list = []
    filtered_folder_list = []
    selected = ""

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Input(placeholder="输入文件夹名称")
        yield Label("当前：", id="current_folder")
        

    def on_mount(self) -> None:
        """Initialize the container."""
        self.folder_path_list = get_remote_directorys()
        self.folder_list = [ get_remote_directory_version(folder, "full") for folder in self.folder_path_list ]
        self.folder_mount(self.folder_list)
        self.select(self.folder_list[0])

    def on_button_pressed(self, event:Button.Pressed) -> None:
        self.select(event.button.label)

    def on_input_submitted(self, event:Input.Submitted) -> None:
        val = event.control.value
        self.filter(val)
        self.query_one(Input).value = ""

    def get_selected(self) -> str:
        return self.selected
    
    def print(self, text):
        """Print text to the console."""
        self.mount(Label(text))

    def filter(self, key):
        """Filter remote folders."""
        for folder in self.folder_list:
            self.query_one(f"#{folder}").remove_class("filtered")

        self.filtered_folder_list = [folder for folder in self.folder_list if key not in folder]
        # self.print(self.filtered_folder_list)
        for folder in self.filtered_folder_list:
            self.query_one(f"#{folder}").add_class("filtered")

    class Selected(Message):
        """Color selected message."""
        def __init__(self, folder:str) -> None:
            self.selected = folder
            super().__init__()

    def select(self, selected):
        if not selected:
            return
        if self.selected:
            self.query_one(f"#{self.selected}").remove_class("selected")

        self.selected = selected
        self.query_one("#current_folder").update(f"当前：{self.selected}")
        self.query_one(f"#{self.selected}").add_class("selected")
        self.post_message(self.Selected(self.selected))

    def folder_mount(self, list):
        """Mount remote folder."""
        for folder in list:
            self.mount(RemoteFloder(folder, id=f"{folder}"))
        self.select(self.selected)

    def folder_clear(self):
        """Clear remote folder."""
        for widget in self.query(RemoteFloder):
            widget.remove()

    def folder_refresh(self):
        """Refresh remote folder."""
        self.folder_clear()
        self.folder_mount(self.folder_list)

ROWS = [
        ("Date", "Title", "Note"),
        ("2024-01-01", "WLGL20", ""),
        ("2024-01-01", "UN60_NEW_聚龙", "111"),
        ("2024-01-01", "UN60_NEW_聚龙", "222"),
        ("2024-01-01", "UN60_NEW_聚龙", "33"),
        ("2024-01-01", "UN60_NEW_聚龙", "3333333333333333"),
        ("2024-01-01", "UN60_NEW_聚龙", "22222222"),
        ("2024-01-01", "UN60_NEW_聚龙", ""),
    ]
class UIView(DataTable):
    
    def compose(self) -> ComposeResult:
        yield Static("当前文件夹下没有ui文件", id="ui_message", classes="error_message hidden")
        
    ui_files = []
    origin_rows = []
    ui_file_idx = 0

    def on_mount(self) -> None:
        table = self
        table.cursor_type = "row"
        table.zebra_stripes = False
        # table.add_columns(*ROWS[0])
        for col in ROWS[0]:
            styled_col = Text(col, style="width:25;")
            table.add_column(styled_col)
        # table.add_style(ROWS[1:])
        # table.add_rows(ROWS[1:])

    def add_rows_with_Idx(self, rows=None):
        """Add rows to table."""
        for number, row in enumerate(rows, start=1):
            label = Text(str(number), style="#B0FC38 italic")
            # styled_row = [
            #     Text(str(cell), style="padding=1 0 0 0; height=2;", justify="center") for cell in row
            # ]
            self.add_row(*row, label=label, height=1, key=f"row_{number}")

    class Selected(Message):
        """pass selected message."""
        def __init__(self, file_name) -> None:
            self.selected = file_name
            super().__init__()

    def on_data_table_row_selected(self, message:DataTable.RowSelected) -> None:
        """pass seleted row message"""
        row_idx = message.cursor_row
        self.post_message(self.Selected(self.origin_rows[row_idx]))

    def get_date(self, ui):
        """Get date from ui file."""
        return get_ui_file_time(ui)
    
    def get_ui_note(self, ui):
        """Get note from ui filename"""
        return ui.split("_")[-1]

    def list2view(self, list):
        """list to view"""
        self.origin_rows = list
        self.coverted_rows = []
        # 将ui文件列表转换为DataTable的行数据
        for ui in list:
            # self.get_date(ui)
            # self.get_desc(ui)
            row = (self.get_date(ui), ui, "")
            self.coverted_rows.append(row)
        self.add_rows_with_Idx(self.coverted_rows)

    def update_by_folder(self, folder=None):
        """Update table by folder."""
        self.clear()
        list = scan_ui_files(str(folder))
        self.list2view(list)
        if not list:
            self.query_one("#ui_message").remove_class("hidden")
        else:
            self.query_one("#ui_message").add_class("hidden")
            self.post_message(self.Selected(self.origin_rows[0]))

class DownloadDesc(Widget):
    """A widget to display download desc."""
    country = reactive([])
    remote_folder = reactive("")
    ui_file = reactive("")
    def render(self) -> str:
        return f"Folder:   {self.remote_folder}\r\n" + \
                f"UI:       {self.ui_file}\r\n" + \
                f"Country:  {", ".join(self.country)}"

class Information(Container):
    country = reactive(["AUT", "MIX"], recompose=True)
    remote_folder = reactive("")
    ui_file = reactive("")
        

    def compose(self) -> ComposeResult:
        yield Static("Inforamtion", classes="title")
        yield DownloadDesc()



class Note(Container):
    """A widget to display note."""
    def compose(self) -> ComposeResult:
        yield Static("Note", classes="title")
        yield TextArea(id="note")
    pass

class GetZPKApp(App):
    """A GetZPK app to manage ZPK Version."""

    CSS_PATH = "./tcss/getzpk_app.tcss"
    CSS = """
    
    """

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "get_zpk", "执行打包下载"),
        ("r", "refresh_floder", "刷新文件夹")
    ]
    folder_list = ["UN60_NEW", "UN60_OLD", "UN60_RUB", "UN60_TOUCH"]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        
        yield VerticalScroll(
            Container(
                FolderContainer(id="folder_container"),
                id="sider_container",
            ),
            Container(
                ScrollableContainer(
                    # Static(example_table, classes="table pad"),
                    UIView(
                        cell_padding = 2,
                        show_header=True,
                        show_cursor=True,
                        id="top"
                    ),
                    Note(
                        id="mid"
                    ),
                    Information(
                        
                        id="bot"
                    ),
                    id="main2_container"
                ),
                id="main_container"
            ),
            id = "container"
        )
        
                
        
    @on(FolderContainer.Selected)
    def handle_folder_selected(self, message:FolderContainer.Selected) -> None:
        self.remote_floder = message.selected
        self.query_one(DownloadDesc).remote_folder = message.selected
        self.ui_view.update_by_folder(message.selected)

    @on(UIView.Selected)
    def handle_ui_view_selected(self, message:UIView.Selected) -> None:
        """ ui_resource_UN60_NEW.bin """
        self.ui_file = message.selected
        self.query_one(DownloadDesc).ui_file = message.selected

    def on_mount(self) -> None:
        """Initialize the app."""
        self.folder_container = self.query_one(FolderContainer)
        self.ui_view = self.query_one(UIView)
        self.note = self.query_one("#note")
        self.downloadDesc = self.query_one(DownloadDesc)
        self.downloadDesc.country = get_open_country()

    def action_refresh_floder(self):
        """Refresh remote folders."""
        self.folder_container.folder_refresh()
        # self.ui_view.update_by_folder()

    def on_click(self, event:events.Click) -> None:
        """Handle click events."""
        

    def action_get_zpk(self):
        """Get ZPK."""
        # if self.remote_floder and self.ui_file:
            # self.ui_view.mount(Static("请先选择目录和对应的ui文件后，再进行打包！", classes="error_message"))
        self.note.text = f"{self.remote_floder}\r\n{self.ui_file}"
        pass

    def action_toggle_dark(self):
        """Toggle dark mode."""
        self.dark = not self.dark

if __name__ == "__main__":
    app = GetZPKApp()
    app.run()