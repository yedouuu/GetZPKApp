
import os
from rich.text import Text
from rich.markdown import Markdown
from rich.console import RenderableType

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, ScrollableContainer
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
from SelectCountry import select_country
from textual.widgets import (
    Static, 
    Button, 
    Footer, 
    Header, 
    TextArea, 
    Input, 
    Label, 
    Placeholder, 
    DataTable,
    Switch,
)

from DownloadScreen import DownloadScreen
from QuitScreen import QuitScreen
from FileBrowser import FileBrowser
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
        # yield Label("当前：", id="current_folder")
        

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
        # self.query_one("#current_folder").update(f"当前：{self.selected}")
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
            date = self.get_date(ui)
            ui = ui.replace("ui_resource_", "", 1).replace(".bin", " ", 1)
            row = (date, ui, "")
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
    
    def get_country_code(self):
        return self.query_one(DownloadDesc).country_code

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
    
    template = "客户代码:\r\n备注:"
    customer_code = ""
    note = ""

    def on_mount(self):
        self.border_title = "Note"
        self.styles.border_title_align = "center"
        self.text = self.template

    def analyze_note(self):
        customer, self.note = self.text.split("\n", 2)
        self.customer_code = customer.split(":")[1].strip()
        print(f"Customer Code1 = {customer.split(":")[1].strip()}")

    def get_customer_code(self) -> str:
        print(f"Customer Code2 = {self.customer_code}")
        return self.customer_code
    
    def get_note(self) -> str:
        return self.note

        

class MyMessage(Static):
    pass

class Title(Static):
    pass

class OptionGroup(Container):
    pass

class ErrorMessage(Static):
    msg = reactive([])

    # def render(self) -> RenderableType:
        
    #     return "\n".join(self.msg)
    def on_mount(self) -> None:
        self.border_title = "Information"
        # self.border_subtitle = "by Frank Herbert, in “Dune”"
        self.styles.border_title_align = "center"

    def render(self) -> RenderableType:
        text = Text()
        styles = {
            "Error": "bold red",
            "Success": "bold green",
            "Warning": "bold yellow",
            "Info": "bold blue"
        }
        max_arrow_pos = 0
        for seg in self.msg:
            pos = seg.find("->") + 2
            if pos > max_arrow_pos:
                max_arrow_pos = pos

        for seg in self.msg:

            pos = seg.find("->") + 2
            blank_to_add = max_arrow_pos - pos
            seg = seg.replace("->", " " * blank_to_add + "->", 1)

            original_seg = seg  # 保存原始段落以用于未标记的文本
            # 检查是否包含特定标签，并据此应用样式
            for label, style in styles.items():
                # 构造标签，如"【Info】"
                tag = f"【{label}】"

                if tag in seg:
                    # seg = seg.replace(tag, "")  # 移除标签文本
                    text.append(seg, style=style)
                    break
            else:
                # 如果没有任何标签被应用，添加原始文本
                text.append(original_seg)

            text.append("\n")  # 每个消息后添加新行

        return text

class DarkSwitch(Horizontal):
    def compose(self) -> ComposeResult:
        yield Switch(value=self.app.dark)
        yield Static("Dark mode toggle", classes="label")

    def on_mount(self) -> None:
        self.watch(self.app, "dark", self.on_dark_change, init=False)

    def on_dark_change(self) -> None:
        self.query_one(Switch).value = self.app.dark

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.app.dark = event.value

MESSAGE = """
We hope you enjoy using Textual.
Here are some links. You can click these!
Built with ♥  by [@click="app.open_link('https://www.textualize.io')"]Textualize.io[/]
"""

class Sidebar(Container):

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Title("Select Country"),
            Button("Clear", id="clear_country"),
        )
        # yield Title("Select Country")
        yield Input()
        yield OptionGroup(ErrorMessage())
        # yield DarkSwitch()

    class Submitted(Message):
        def __init__(self, value) -> None:
            self.value = value
            super().__init__()

    def on_input_submitted(self, event:Input.Submitted) -> None:
        val = event.control.value
        self.query_one(Input).value = ""
        self.post_message(self.Submitted(val))

    def on_button_pressed(self, event:Button.Pressed) -> None:
        self.query_one(Input).value = ""
        self.query_one(Input).focus(True)

    


class GetZPKApp(App):
    """A GetZPK app to manage ZPK Version."""

    # CSS_PATH = "./tcss/getzpk_app.tcss"
    CSS="""
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

Sidebar {
    width: 70%;
    background: $panel;
    transition: offset 500ms in_out_cubic;
    layer: overlay;
    column-span: 3;
    row-span: 8;

    Input {
      margin: 1;
    }

    ErrorMessage {
      width: 100%;
      height: 100%;
      margin-left: 1;
      border: round $primary-lighten-2;
    }
    
    Horizontal {
      height: 0.2fr;
    }

    #clear_country {
      margin-top: 1;
    }
}

Sidebar:focus-within {
    offset: 0 0 !important;
}

Sidebar.-hidden {
    offset-x: -100%;
}

Sidebar Title {
    background: $boost;
    color: $secondary;
    padding: 1 0;
    margin-top: 1;
    border-right: vkey $background;
    text-align: center;
    text-style: bold;
    width:75%
}

OptionGroup {
    background: $boost;
    color: $text;
    height: 1fr;
    padding: 0 1;
    border-right: vkey $background;
}


ZPK_View {
  margin-top: 1;

  #zpk_path {
    width: 50%;
    border: round #7e7e7e;
  }

  Button {
    width: 20%;
  }
}

"""

    BINDINGS = [
        ("ctrl+b", "toggle_sidebar", "选择币种"),
        ("ctrl+d", "get_zpk", "执行打包下载"),
        ("ctrl+f", "toggle_file_browser", "打开文件浏览器"),
        ("ctrl+r", "refresh_floder", "刷新"),
        ("ctrl+q", "request_quit", "退出"),
    ]
    folder_list = ["UN60_NEW", "UN60_OLD", "UN60_RUB", "UN60_TOUCH"]
    SCREENS = {"FileBrower": FileBrowser()}
    # MODES = {"FileBrower": FileBrowser()}
    show_sidebar = reactive(False)

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Header(show_clock=True),
            Sidebar(classes="-hidden"),
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
            Footer(),
            id = "container"
        )
        
                
    def on_mount(self) -> None:
        """Initialize the app."""
        self.folder_container = self.query_one(FolderContainer)
        self.ui_view = self.query_one(UIView)
        self.note = self.query_one(Note)
        self.information = self.query_one(Information)
        self.information.refresh_country_code()
        self.sidebar = self.query_one(Sidebar)
        # self.mount(Footer())

    def on_load(self) -> None:
        pass

    def action_refresh_floder(self):
        """Refresh remote folders."""
        self.folder_container.folder_refresh()
        self.information.refresh_country_code()
        # self.ui_view.update_by_folder()

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())    

    def create_readme(self, customer_path: str, latest_file: str) -> None:
        """Create a readme file."""
        readme_file_path = f"{customer_path}/README.md"
        with open(readme_file_path, "a+", encoding="utf-8") as f:
            f.write(
                f"""
# 文件名: {latest_file}
- UI文件: {self.ui_file}
- 币种 : {self.information.get_country_code()}
- 备注 : {self.note.get_note().split(":")[-1]}\r\n
""")
    

    async def action_get_zpk(self):
        """Get ZPK."""
        self.note.analyze_note()
        customer_code = self.note.get_customer_code()
        customer_path = ""
        if customer_code:
            customer_path = f"./ZPK/{customer_code}/"
            if not os.path.exists(customer_path):
                os.mkdir(customer_path)

        await self.push_screen(DownloadScreen())
        latest_file = await self.query_one(DownloadScreen).download(self.remote_folder_path, self.ui_file, customer_path)
        self.create_readme(customer_path, latest_file)

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        self.set_focus(None)
        if sidebar.has_class("-hidden"):
            self.sidebar.query_one(Input).value = " ".join(get_open_country()[2:])
            self.sidebar.query_one(Input).focus(True)
            sidebar.remove_class("-hidden")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden")

    def action_toggle_file_browser(self) -> None:
        """Toggle file browser."""
        self.set_focus(None)
        # self.query_one(Footer).remove()
        self.app.push_screen("FileBrower")

    def action_toggle_dark(self):
        """Toggle dark mode."""
        self.dark = not self.dark

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

    @on(Sidebar.Submitted)
    def handle_sidebar_submitted(self, message:Sidebar.Submitted) -> None:
        """ 根据输入，更新对应的货币信息 """
        val = message.value
        if val:
            self.sidebar.query_one(ErrorMessage).msg = ""
            error_msg = select_country(val)
            if error_msg:
                self.sidebar.query_one(ErrorMessage).msg = error_msg
            else:
                self.sidebar.query_one(ErrorMessage).msg = [" 【Success】Success!"]
            self.query_one(Information).refresh_country_code()
        else:
            self.action_toggle_sidebar()

if __name__ == "__main__":
    app = GetZPKApp()
    app.run()