import time
import os
import asyncio
from rich.text import Text
from rich.markdown import Markdown
from rich.console import RenderableType
# 不能删除这个模块(win32timezone)，否则PyInstaller打包后执行会报错
import win32timezone
import tkinter as tk
import exe_handler

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, ScrollableContainer
from textual.reactive import reactive
from textual.binding import Binding
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
    set_language,
    get_languages,
    get_mode,
    get_local_currencyXML_path,
    get_scheme,
    GL18_get_image_app_path,
    GL18_get_boot_path,
    GL18_get_mainboard_app_path
)
from CopyFile import (
    select_and_upload_file, 
    open_file_path, 
    copy_to_clipboard, 
    GL18_create_rootfs_image
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
    OptionList,
    ContentSwitcher,
)

from DownloadScreen import DownloadScreen
from QuitScreen import QuitScreen
from FileBrowser import FileBrowser
from AutoComplete import AutoCompleteContainer, AutoCompleteInput
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

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Called when the user types in the input."""
        self.filter_text = event.value
        # 取消已有的延时任务，如果存在
        if hasattr(self, 'delay_task') and not self.delay_task.done():
            self.delay_task.cancel()
        # 创建一个新的延时任务
        self.delay_task = asyncio.create_task(self.handle_delayed_update(event.value))

    async def handle_delayed_update(self, value):
        """Handle the update with a delay."""
        await asyncio.sleep(0.3)  # 非阻塞延时0.3秒
        # 执行需要延时后处理的任务
        self.filter(value)

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
            self.mount(RemoteFloder(folder, variant="primary", id=f"{folder}"))
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
        yield Static("当前文件夹下没有对应的ui文件", id="ui_message", classes="error_message hidden")
    
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

class Customercode_Input(Static):
    customer_code = reactive("WL")

    def compose(self) -> ComposeResult:
        yield Input(placeholder="请输入客户编码", classes="grey_input")

    def on_amount(self):
        self.query_one(Input).value = self.customer_code

    class Customercode_Changed(Message):
        def __init__(self, customer_code) -> None:
            self.value = customer_code
            super().__init__()
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Called when the user types in the input."""
        self.customer_code = event.value
        # 取消已有的延时任务，如果存在
        if hasattr(self, 'delay_task') and not self.delay_task.done():
            self.delay_task.cancel()
        # 创建一个新的延时任务
        self.delay_task = asyncio.create_task(self.handle_delayed_update(event.value))

    async def handle_delayed_update(self, value):
        """Handle the update with a delay."""
        await asyncio.sleep(0.3)  # 非阻塞延时0.3秒
        self.post_message(self.Customercode_Changed(self.customer_code))
    
    def get_custoemr_code(self):
        return self.customer_code

class DownloadDesc(Widget):
    """A widget to display download desc."""
    country_code = reactive([])
    remote_folder = reactive("")
    mode = reactive("")
    ui_file = reactive("")
    
    def render(self) -> str:
        text = Text()
        styles = {
            "Error": "bold red",
            "Success": "bold green",
            "Warning": "bold yellow",
            "Info": "bold blue"
        }
        text.append("Folder:   ", style=styles["Info"])
        text.append(self.remote_folder)
        text.append("\r\n")

        text.append("UI:       ", style=styles["Info"])
        text.append(self.ui_file.replace("ui_resource_", "", 1))
        text.append("\r\n")
        
        text.append("Mode:     ", style=styles["Info"])
        text.append(self.mode.replace(",", ", "))
        text.append("\r\n")

        text.append("Country:  ", style=styles["Info"])
        text.append(  ", ".join(self.country_code) )
        #text.append(  "USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD, USD" )
        text.append( f"({len(self.country_code)-2})", style=styles["Info"] )
        text.append("\r\n")
        
        return text

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

    def refresh_country_code(self, remote_folder):
        """Set country."""
        country_code = get_open_country(remote_folder)
        self.query_one(DownloadDesc).country_code = country_code
        print(f"Country Code = {country_code}")

    def set_remote_folder(self, folder):
        """Set remote folder."""
        self.query_one(DownloadDesc).remote_folder = folder
    
    def set_ui_file(self, ui):
        """Set ui file."""
        self.query_one(DownloadDesc).ui_file = ui

    def set_mode(self, mode):
        """Set mode."""
        self.query_one(DownloadDesc).mode = mode

class Language(Static):
    languages = reactive([])

    def compose(self) -> ComposeResult:
        yield OptionList(
            "English",
        )

    def on_mount(self) -> None:
        """Initialize the container."""
        # self.styles.border = ("heavy")
        self.border_title = "Language"
        # self.border_subtitle = "by Frank Herbert, in “Dune”"
        self.styles.border_title_align = "center"

    class LanguageSelected(Message):
        """Handle language selection."""
        def __init__(self, selected) -> None:
            self.selected = selected
            super().__init__()

    def on_option_list_option_selected(self, event:OptionList.OptionSelected):
        # print(self.languages[event.option_index])
        self.post_message(self.LanguageSelected(self.languages[event.option_index]))

    def get_languages(self):
        return self.languages

    def add_languages(self, items):
        self.query_one(OptionList).add_options(items)
        self.languages = items
    
    def clear_languages(self):
        self.query_one(OptionList).clear_options()
        self.languages = []


class Function_area(ScrollableContainer):
    """A container to hold the download area."""
    
    def compose(self) -> ComposeResult:
        # yield Static("Inforamtion", classes="title")
        yield Horizontal(
            Button("修改币种", "primary", id="information_country_btn"),
            Button("上传UI","primary", id="upload_ui_btn"),
            Button("下载","primary", id="information_download_btn"),
        )
        yield Horizontal(
            Button("查看文件","primary", id="information_filebrowser"),
            Button("打开配置文件", "primary", id="user_config_btn"),
            Button("复制货币文件", "primary", id="information_copy_currency_btn")
        )

    def on_mount(self) -> None:
        """Initialize the container."""
        # self.styles.border = ("heavy")
        # self.border_title = "Function"
        # self.border_subtitle = "by Frank Herbert, in “Dune”"
        # self.styles.border_title_align = "center"

    class CurrenciesBtnPressed(Message):
        """Handle currency button presses."""
        def __init__(self) -> None:
            super().__init__()

    class LanguageBtnPressed(Message):
        """Handle download button presses."""
        def __init__(self) -> None:
            super().__init__()

    class DownloadBtnPressed(Message):
        """Handle download button presses."""
        def __init__(self) -> None:
            super().__init__()

    class uploadBtnPressed(Message):
        """Handle download button presses."""
        def __init__(self) -> None:
            super().__init__()

    class CopyCurrencyXMLBtnPressed(Message):
        """Handle download button presses."""
        def __init__(self) -> None:
            super().__init__()

    class FileBrowserBtnPressed(Message):
        """Handle download button presses."""
        def __init__(self) -> None:
            super().__init__()
            

    def on_button_pressed(self, event:Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "information_country_btn":
            print("Currencies Button Pressed PostMessage")
            self.post_message(self.CurrenciesBtnPressed())
        elif event.button.id == "information_download_btn":
            self.post_message(self.DownloadBtnPressed())
        elif event.button.id == "upload_ui_btn":
            self.post_message(self.uploadBtnPressed())
        elif event.button.id == "user_config_btn":
            print("user_config_btn Pressed PostMessage")
            open_file_path("./user_config.xml")
        elif event.button.id == "information_copy_currency_btn":
            self.post_message(self.CopyCurrencyXMLBtnPressed())
        elif event.button.id == "information_filebrowser":
            self.post_message(self.FileBrowserBtnPressed())       


class Note(TextArea):
    """A widget to display note."""
    
    # template = reactive("客户代码:\r\n备注:")
    template = reactive("备注:")
    # customer_code = ""
    note = ""

    def on_mount(self):
        self.border_title = "Note"
        self.styles.border_title_align = "center"
        self.text = self.template

    def analyze_note(self):
        # customer, self.note = self.text.split("\n", 1)
        # self.customer_code = customer.split(":")[1].strip()
        # print(f"Customer Code1 = {customer.split(":")[1].strip()}")
        # print(f"Note = {self.note}")
        # self.text = self.template

        self.note = self.text
        print(f"Note = {self.note}")
        self.text = self.template

    def get_customer_code(self) -> str:
        return self.customer_code
    
    def get_note(self) -> str:
        return self.note

    def refresh_note(self):
        self.text = self.template

    @on(TextArea.Changed)
    def handle_change(self, event:TextArea.Changed) -> None:
        """Handle text area changes."""
        # self.analyze_note()
        pass

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
    CSS = """
GetZPKApp {
    layout: vertical;
    background: $boost;
    min-width: 50;
    scrollbar-size: 0 0;
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

    .selected {
      border: round $warning !important; 
    }

    .filtered {
        display: none;
    }
    

    RemoteFloder {
      width: 100%;
      height: 3;
      margin: 0 0 0 0;
      padding: 0;
      border: round #7e7e7e;
      background: #1e1e1e;

      &:focus {
        text-style: bold;
      }

      &.-primary {
        background: $primary;
        color: $text;
        border: round #7e7e7e;
        background: #1e1e1e;

        &:hover {
            border: round #4f4f4f;
            color: #4f4f4f;
        }
      }
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
    scrollbar-size: 0 0;
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




#container {
  layout:grid;
  grid-size: 4 8;
  width: 100%;
  height: 200%;
  scrollbar-size: 0 0;
}
#sider_container {
  row-span: 8;
}
#main_container {
  row-span: 8;
  column-span: 3;
  scrollbar-size: 0 0;

  #main2_container {
    layout: grid;
    grid-size: 16 16;
    border: round #7e7e7e;
    scrollbar-size: 0 0;
    padding: 0 0 0 0;

    #top {
      row-span: 4;
      column-span: 16;
    }
    #autocomplete_container {
      row-span: 1;
      column-span: 16;
      height: 100%;
      overflow: auto;
      layers: above;
      scrollbar-size: 0 0;
      margin: 0 0 0 0;
    }
    #customer_code_input {
      row-span: 1;
      column-span: 10;
      height: 100%;
      layers: above;
      scrollbar-size: 0 0;
      margin: 0 0 0 0;
    }
    #note {
      row-span: 3;
      column-span: 6;
      padding: 0 0 0 0;
      margin: 0 0 0 0;
      height: 100%;
      layers: below;
      border: panel $primary-lighten-2;
    }
    #note:focus {
      border: panel $secondary;
    }
    #information {
      row-span: 3;
      column-span: 10;
      border: panel $primary-lighten-2;
      margin: 0 0 0 0;
      padding: 0 1;
      width: 100%;
      layers: below;
      height: 100%;
    }
    #function_area {
      row-span: 4;
      column-span: 10;
      # border: panel $primary-lighten-2;
      margin: 1 0 0 0;
      padding: 0 0;
      width: 100%;
      height: 100%;
    }
    #language {
      row-span: 4;
      column-span: 6;
      border: panel $primary-lighten-2;
      margin: 1 0 0 0;
      width: 100%;
      height: 100%;
    }
  }
}

.grey_input {
  margin: 0 0 0 0;
  padding: 0 0 0 0;
  border: round gray;
  background: #1e1e1e;

  &:focus {
    text-style: bold;
    border: round #ffa62b; 
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
  background: #1e1e1e;

  DownloadDesc {
    row-span: 3;
    height: 80%;
  }

  Horizontal {
    row-span: 1;
    height: 100%;
  }
}

Function_area {
  OptionList {
    width: 100%;
    height: 100%;
    margin: 0;
  }

  Button {
    height: 3;
    margin: 0 1;
    padding: 0;
    border: round #7e7e7e;
    background: #1e1e1e;

    &:focus {
      text-style: bold;
    }
    &.-active {

    }

    .selected {
      border: round $warning !important; 
    }

    &.-primary {
      background: $primary;
      color: $text;
      border: round #7e7e7e;
      background: #1e1e1e;

      &:hover {
          border: round #4f4f4f;
          color: #4f4f4f;
      }
    }
  }
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
        margin-left: 5;
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

LanguageSidebar,
Sidebar {
    width: 100%;
    background: $panel;
    transition: offset 500ms in_out_cubic;
    layer: overlay;
    column-span: 2;
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

LanguageSidebar {
    offset-x: -100% !important;
}

LanguageSidebar:focus-within,
Sidebar:focus-within {
    offset: 0 0 !important;
}

LanguageSidebar.-hidden200 {
    offset-x: -200%;
}
Sidebar.-hidden100 {
    offset-x: -100%;
}

LanguageSidebar Title,
Sidebar Title {
    background: $boost;
    color: $secondary;
    padding: 1 0;
    margin-top: 1;
    border-right: vkey $background;
    text-align: center;
    text-style: bold;
    width:75%;
}

LanguageSidebar Title {
    width:100% !important;
}

OptionGroup {
    background: $boost;
    color: $text;
    height: 1fr;
    padding: 0 1;
    border-right: vkey $background;
}


ZPKView {
  margin-top: 1;

  #zpk_path {
    width: 50%;
    margin-right: 1;
    border: round #7e7e7e;
  }

  Button {
    width: 15%;
  }
}

"""

    BINDINGS = [
        Binding("ctrl+b", "toggle_sidebar", "选择币种", key_display="B"),
        Binding("ctrl+u", "upload_ui_file", "上传UI文件", key_display="U"),
        Binding("ctrl+d", "get_zpk", "下载", key_display="D"),
        Binding("ctrl+f", "toggle_file_browser", "查看文件", key_display="F"),
        Binding("ctrl+r", "refresh_floder", "刷新", key_display="R"),
        Binding("ctrl+q", "request_quit", "退出", key_display="Q"),
    ]
    folder_list = ["UN60_NEW", "UN60_OLD", "UN60_RUB", "UN60_TOUCH"]
    SCREENS = {"FileBrower": FileBrowser()}
    # MODES = {"FileBrower": FileBrowser()}
    show_sidebar = reactive(False)

    def compose(self) -> ComposeResult:
        yield ScrollableContainer(
            Header(show_clock=True),
            Sidebar(classes="-hidden100"),
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
                    AutoCompleteContainer(
                        id="autocomplete_container"
                    ),
                    Note(
                        id="note"
                    ),
                    Information(
                        
                        id="information"
                    ),
                    Language(
                        id="language"
                    ),
                    Customercode_Input(
                        id="customer_code_input"
                    ),
                    Function_area(
                        id="function_area"
                    ),
                    id="main2_container"
                ),
                id="main_container"
            ),
            id = "container"
        )
        # yield Placeholder(

        # )
        yield Footer(

        )
        
                
    def on_mount(self) -> None:
        """Initialize the app."""
        self.folder_container = self.query_one(FolderContainer)
        self.ui_view = self.query_one(UIView)
        self.note = self.query_one(Note)
        self.information = self.query_one(Information)
        self.sidebar = self.query_one(Sidebar)
        self.function_area = self.query_one(Function_area)
        self.language = self.query_one(Language)
        self.customer_path = None
        self.customer_code = self.query_one(Customercode_Input).get_custoemr_code()
        # self.mount(Footer())

    def on_load(self) -> None:
        pass

    def action_refresh_floder(self):
        """Refresh remote folders."""
        self.folder_container.folder_refresh()
        self.information.refresh_country_code(self.remote_folder)
        self.note.refresh_note()
        # self.mount(Note())

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())    

    def create_readme(self, customer_path: str, latest_file: str) -> None:
        """Create a readme file."""
        if customer_path:
            readme_file_path = f"{customer_path}/README.md"
        else:
            readme_base_path = os.path.join(get_text("local_zpk_path") ,str(self.remote_folder).replace("_", ""))
            readme_file_path = os.path.join(readme_base_path, "README.md")
            readme_file_path = os.path.abspath(readme_file_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(readme_file_path), exist_ok=True)

        with open(readme_file_path, "a+", encoding="utf-8") as f:
            f.write(
                f"""
# 文件名: {latest_file}
- 时间: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))}
- UI文件: {self.ui_file}
- 模式:  {get_mode()}
- 币种 : {", ".join(self.information.get_country_code())}
- 备注 : {self.note.get_note().split("备注:")[-1].replace("\r\n", "\n")}\r\n
""")

    async def action_get_zpk(self):
        """Get ZPK."""
        zpk_path = get_text("local_zpk_path")
        self.note.analyze_note()
        # customer_code = self.note.get_customer_code()
        customer_path = self.customer_path
        if customer_path:
            customer_path = os.path.join(zpk_path, self.customer_path)
            customer_path = os.path.abspath(customer_path)
            print(f"customer_path: {customer_path}")
            if not os.path.exists(customer_path):
                os.makedirs(customer_path)

        currency_list_str = ",".join(self.information.get_country_code())
        select_country(currency_list_str, self.remote_folder)

        if ( get_scheme(self.remote_folder) == "GL18" ):
            print("【INFO】 PACK GL18 GIN")
            image_app_path = os.path.abspath(GL18_get_image_app_path())
            mainboard_path = os.path.abspath(GL18_get_mainboard_app_path())
            boot_path = os.path.abspath(GL18_get_boot_path())
            file_system_path = os.path.abspath(GL18_create_rootfs_image(self.customer_path))
            ui_file_path = os.path.abspath(get_text("local_ui_file_path") + self.ui_file)
            print(f"Paths:\r\n"
                  f"  image_app_path:   {image_app_path}\r\n"
                  f"  mainboard_path:   {mainboard_path}\r\n"
                  f"  boot_path:        {boot_path}\r\n"
                  f"  file_system_path: {file_system_path}\r\n"
                  f"  ui_file_path:     {ui_file_path}")
            PACK_INFO = {
                "img_path":         image_app_path,
                "model":            self.remote_folder,
                "remote_path":      self.remote_folder_path,
                "file_system_path": file_system_path,
                "mainboard_path":   mainboard_path,
                "boot_path":        boot_path,
                "ui_path":          ui_file_path,
                "factory_code":     self.customer_code,
                "customer_path":    customer_path,
            }
            latest_file, file_path = exe_handler.pack_GIN(PACK_INFO)
            if ( latest_file is None or file_path is None ):
                print(f"【Error】 Pack GIN Error")
                exit()
            
            copy_to_clipboard(file_path)
        else:
            await self.push_screen(DownloadScreen())
            latest_file = await self.query_one(DownloadScreen).download(self.remote_folder_path, 
                                                                        self.ui_file, 
                                                                        currency_list_str, 
                                                                        customer_path, 
                                                                        self.customer_code)
        # latest_file = "WLGL20_20230316_1532_1.ZPK"
        
        self.create_readme(customer_path, latest_file)
        self.note.refresh_note()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one(Sidebar)
        print("currency sidebar")
        self.set_focus(None)
        if sidebar.has_class("-hidden100"):
            self.sidebar.query_one(Input).value = " ".join(get_open_country(self.remote_folder)[2:])
            self.sidebar.query_one(Input).focus(True)
            sidebar.remove_class("-hidden100")
        else:
            if sidebar.query("*:focus"):
                self.screen.set_focus(None)
            sidebar.add_class("-hidden100")

    def action_toggle_file_browser(self) -> None:
        """Toggle file browser."""
        self.set_focus(None)
        self.app.push_screen("FileBrower")
        # self.query_one(FileBrowser).refresh_filetree()

    def action_upload_ui_file(self) -> None:
        """Upload ui file."""
        ui_path = get_text("local_ui_file_path")
        print(f"upload ui path = {ui_path},  remote_folder = {self.remote_folder}")
        select_and_upload_file(ui_path, self.remote_folder)
        self.action_refresh_floder()

    def action_toggle_dark(self):
        """Toggle dark mode."""
        self.dark = not self.dark

    @on(FolderContainer.Selected)
    def handle_folder_selected(self, message:FolderContainer.Selected) -> None:
        self.remote_folder = message.selected
        self.remote_folder_path = message.selected_path
        self.query_one(Information).set_remote_folder(message.selected) 
        self.ui_view.update_by_folder(message.selected)
        self.information.refresh_country_code(self.remote_folder)
        self.information.set_mode(get_mode(self.remote_folder))

        self.language.clear_languages()
        self.language.add_languages(get_languages(self.remote_folder))
        

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
            error_msg = select_country(val, self.remote_folder)
            if error_msg:
                self.sidebar.query_one(ErrorMessage).msg = error_msg
            else:
                self.sidebar.query_one(ErrorMessage).msg = [" 【Success】Success!"]
            self.query_one(Information).refresh_country_code(self.remote_folder)
        else:
            self.action_toggle_sidebar()

    @on(Language.LanguageSelected)
    def handle_language_selected(self, message:Language.LanguageSelected) -> None:
        language = message.selected
        # print(language)
        set_language(language)


    @on(Function_area.CurrenciesBtnPressed)
    def handle_currencyBtn_pressed(self, event:Button.Pressed) -> None:
        print("Function_area.CurrencyBtnPressed")
        self.action_toggle_sidebar()


    @on(Function_area.DownloadBtnPressed)
    async def handle_downloadBtn_pressed(self, event:Button.Pressed) -> None:
        await self.action_get_zpk()
        # self.test_note()

    @on(Function_area.CopyCurrencyXMLBtnPressed)
    def handle_copy_currency_xml(self, event:Button.Pressed) -> None:
        origin_xml_path, new_xml_path = get_local_currencyXML_path()
        copy_to_clipboard(new_xml_path)
    
    @on(Function_area.FileBrowserBtnPressed)
    def handle_filebrowser_open(self, event:Button.Pressed) -> None:
        self.action_toggle_file_browser()

    @on(Function_area.uploadBtnPressed)
    def handle_upload_ui(self, event:Button.Pressed) -> None:
        self.action_upload_ui_file()

    @on(AutoCompleteContainer.Submitted)
    def handle_auto_complete_input_submitted(self, event: AutoCompleteContainer.Submitted):
        print(f"AutoCompleteContainer submitted with value: {event.value}")
        self.customer_path = event.value

    @on(Customercode_Input.Customercode_Changed)
    def handle_customercode_changed(self, event:Customercode_Input.Customercode_Changed) -> None:
        self.customer_code = event.value
        print(f"Customercode_Input changed with value: {self.customer_code}")

if __name__ == "__main__":
    try:
        app = GetZPKApp()
        app.run()
    except Exception as e:
        print("Exception:", e)
        input("Press Enter to exit...")
        input("Press Enter to exit...")
