import time
import asyncio

from rich.text import Text
from rich.markdown import Markdown


from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Container, Center, Middle, VerticalScroll, Horizontal, ScrollableContainer
from textual.reactive import reactive
from textual.timer import Timer
from textual.message import Message
from textual.widget import Widget
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

from DownloadScreen import DownloadScreen
from QuitScreen import QuitScreen
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
    folder_path_list = []
    filtered_folder_list = []
    selected = ""
    selected_pat = ""

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
        def __init__(self, folder:str, folder_path:str) -> None:
            self.selected = folder
            self.selected_path = folder_path
            super().__init__()

    def select(self, selected):
        if not selected:
            return
        if self.selected:
            self.query_one(f"#{self.selected}").remove_class("selected")

        self.selected = selected
        self.selected_path = self.folder_path_list[self.folder_list.index(str(selected))]
        self.query_one("#current_folder").update(f"当前：{self.selected}")
        self.query_one(f"#{self.selected}").add_class("selected")
        self.post_message(self.Selected(self.selected, self.selected_path))

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
    country_code = reactive([])
    remote_folder = reactive("")
    ui_file = reactive("")
    def render(self) -> str:
        return f"Folder:   {self.remote_folder}\r\n" + \
                f"UI:       {self.ui_file}\r\n" + \
                f"Country:  {", ".join(self.country_code)}"

class Information(Container):
    country = reactive(["AUT", "MIX"], recompose=True)
    remote_folder = reactive("")
    ui_file = reactive("")
        

    def compose(self) -> ComposeResult:
        # yield Static("Inforamtion", classes="title")
        yield DownloadDesc()

    def on_mount(self) -> None:
        """Initialize the container."""
        # self.styles.border = ("heavy")
        self.border_title = "Information"
        # self.border_subtitle = "by Frank Herbert, in “Dune”"
        self.styles.border_title_align = "center"

    def set_country_code(self, code):
        """Set country."""
        self.query_one(DownloadDesc).country_code = code
    
    def refresh_country_code(self):
        """Set country."""
        self.query_one(DownloadDesc).country_code = get_open_country()
        print(f"Country Code = {get_open_country()}")

    def set_remote_folder(self, folder):
        """Set remote folder."""
        self.query_one(DownloadDesc).remote_folder = folder
    
    def set_ui_file(self, ui):
        """Set ui file."""
        self.query_one(DownloadDesc).ui_file = ui

class Note(TextArea):
    """A widget to display note."""

    def on_mount(self):
        self.border_title = "Note"
        # self.border_subtitle = "by Frank Herbert, in “Dune”"
        self.styles.border_title_align = "center"

    



class GetZPKApp(App):
    """A GetZPK app to manage ZPK Version."""

    # CSS_PATH = "./tcss/getzpk_app.tcss"
    CSS = """
    GetZPKApp {
    layout: vertical;
    background: $boost;
    min-width: 50;
}

FolderContainer {
    content-align: center middle;
    width: 100%;
    height: 100%;
    column-span: 1;
    border: round #7e7e7e;

    Label {
        content-align: center middle;
        margin: 0 0 1 0;
    }
    Input {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
        padding: 0;
    }
    RemoteFloder {
      width: 100%;
      height: 3;
      margin: 0 0 0 0;
      padding: 0;
      border: round #7e7e7e;
    }
}

.table {
  row-span: 1;
  column-span: 8;
}

UIView {
    height: 16;
    max-height: 16;
    margin: 0 0 0 0;
    .table_title {
    }

    .error_message {
        content-align: center middle;
        width: 100%;
        height: 100%;
        background: $error;
    }
    .warning_message {
        content-align: center middle;
        width: 100%;
        height: 100%;
        background: $warning;
    }
    .success_message {
        content-align: center middle;
        width: 100%;
        height: 100%;
        background: $success;
    } 

    .hidden {
        display: none;
    }

    .selected {
        background: $success;
    }
}


.selected {
    background: $primary;
}
.filtered {
    display: none;
}



#container {
  layout:grid;
  grid-size: 4 8;
}
#sider_container {
  row-span: 8;
}
#main_container {
  row-span: 8;
  column-span: 3;

  #main2_container {
    layout: grid;
    grid-size: 8 8;
    border: round #7e7e7e;

    #top {
      row-span: 4;
      column-span: 8;
    }
    #mid {
      row-span: 4;
      column-span: 3;
      padding: 0 0 0 0;
      margin: 0 0 0 0;
      border: panel $primary-lighten-2;
    }
    #bot {
      row-span: 4;
      column-span: 8;
      border: panel $primary-lighten-2;
      margin: 0 0 0 0;
      padding: 0 1;
      width: 100%;
      height: 100%;
    }
  }
}

Note {
  padding: 0 0 0 0;
  margin: 0 0 0 0;
  width: 100%;
  height: 100%;

}

Information {
  margin: 0 0 0 0;
  width: 100%;
  height: 100%;
}

.title {
  content-align-horizontal: center;
  color: $warning;
}

.subtitle {
  color: $warning;
}

#info_folder {
  width: 100%;
  height: 100%;
}

#main {
  layout: grid;
  grid-size: 8 8;
}

#main_top{
  row-span: 4;
}

OptionList {
  width: 50%;
  height: 50%;
}

DownloadScreen {
    align: center middle;

    #dialog {
        grid-size: 2 4;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 16;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        column-span: 2;
        row-span:2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    #progress {
        column-span: 2;
        margin-left: 10;
        content-align: center middle;
    }

    Button {
        column-span: 2;
        width: 100%;
    }

    .loading {
      background: $panel;
    }
}


QuitScreen {
    align: center middle;

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
}
    """

    BINDINGS = [
        ("q", "request_quit", "退出"),
        ("a", "get_zpk", "执行打包下载"),
        ("r", "refresh_floder", "刷新"),
    ]
    folder_list = ["UN60_NEW", "UN60_OLD", "UN60_RUB", "UN60_TOUCH"]
    # SCREENS = {"DownloadScreen": DownloadScreen()}

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
        self.remote_folder = message.selected
        self.remote_folder_path = message.selected_path
        self.query_one(Information).set_remote_folder(message.selected) 
        self.ui_view.update_by_folder(message.selected)

    @on(UIView.Selected)
    def handle_ui_view_selected(self, message:UIView.Selected) -> None:
        """ ui_resource_UN60_NEW.bin """
        self.ui_file = message.selected
        self.query_one(Information).set_ui_file(message.selected)

    def on_mount(self) -> None:
        """Initialize the app."""
        self.folder_container = self.query_one(FolderContainer)
        self.ui_view = self.query_one(UIView)
        self.note = self.query_one(Note)
        self.information = self.query_one(Information)
        self.information.refresh_country_code()

    def action_refresh_floder(self):
        """Refresh remote folders."""
        self.folder_container.folder_refresh()
        self.information.refresh_country_code()
        # self.ui_view.update_by_folder()

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())    

    async def action_get_zpk(self):
        """Get ZPK."""
        await self.push_screen(DownloadScreen())
        await self.query_one(DownloadScreen).download(self.remote_folder_path, self.ui_file)

    def action_toggle_dark(self):
        """Toggle dark mode."""
        self.dark = not self.dark

if __name__ == "__main__":
    app = GetZPKApp()
    app.run()