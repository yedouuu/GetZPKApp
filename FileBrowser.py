"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import os
import asyncio
from pathlib import Path
from rich.syntax import Syntax
from rich.traceback import Traceback
from pathlib import Path
from typing import Iterable

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, ScrollableContainer
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Static, Button, Input
from textual.screen import Screen
from textual.reactive import reactive
from textual.binding import Binding

from CopyFile import copy_to_clipboard, open_file_path

class ZPKView(Static):
    
    path = reactive("")
    folder_path = reactive("./")

    def __init__(self, path: str) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Horizontal(
          Static(f"{self.path}", id="zpk_path"),
          Button("复制", id="copy", variant="primary"), 
          Button("打开", id="open", variant="primary")
        )
    
    def set_path(self, path: str) -> None:
        self.set_folder_path(path)
        self.path = path
        file_name = path.split("\\")[-1].split(".")
        file_name = f"{file_name[0]}.{file_name[1][:4]}"
        self.query_one("#zpk_path", Static).update(file_name)

    def set_folder_path(self, path: str) -> None:
        if path.endswith(".ZPK"):
            path = path.rsplit("\\", 1)[0]
        self.path = path
        self.query_one("#zpk_path", Static).update(path)
        self.folder_path = path

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy":
            abs_path = os.path.abspath(self.path)
            print(abs_path)
            copy_to_clipboard(abs_path)
        elif event.button.id == "open":
            abs_path = os.path.abspath(self.folder_path)
            print(abs_path)
            open_file_path(abs_path)

class FilteredDirectoryTree(DirectoryTree):

    def __init__ (self, path: str, keywords: str, *args, **kwargs) -> None:
        super().__init__(path, *args, **kwargs)
        self.keywords = keywords

    # def watch_keywords(self, keywords: str) -> None:
    #     """Called when keywords is modified."""
    #     self.query_one(DirectoryTree).path = self.path

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        path_list = []
        for path in paths:
            if path.is_dir() and self.keywords not in path.name:
                continue
            else:
                path_list.append(path)

        return path_list

class FileBrowserFooter(Footer):
    pass

class FileBrowser(Screen):
    """Textual code browser app."""

    CSS = """
Screen {
    background: $surface-darken-1;
    &:inline {
        height: 50vh;
    }
}

#tree-view {
    display: none;
    scrollbar-gutter: stable;
    overflow: auto;
    width: auto;
    height: 100%;
    dock: left;
}

FileBrowser.-show-tree #tree-view {
    display: block;
    max-width: 50%;
}

#file_filter_input {
    margin-top: 1;
}

#code-view {
    min-width: 100%;
    height:70%;
    border: round #7e7e7e;
}
#code {
    width: auto;
}
"""
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
        Binding("ctrl+b", "toggle_sidebar", "选择币种", key_display="B", show=False),
        Binding("ctrl+d", "get_zpk", "下载", key_display="D", show=False),
        Binding("ctrl+u", "upload_ui_file", "上传UI文件", key_display="U", show=False),
        Binding("ctrl+f", "toggle_file_browser", "查看文件", key_display="F", show=False),
        Binding("ctrl+r", "refresh_floder", "刷新", key_display="R", show=False),
        Binding("ctrl+q", "request_quit", "退出", key_display="Q", show=False),
    ]

    show_tree = var(True)
    filter_text = var("")
    path = "./ZPK/"

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        
        yield Header()
        with Container():
            yield Input(id="file_filter_input")
            yield FilteredDirectoryTree(self.path, self.filter_text, id="tree-view")
            with ScrollableContainer(id="code-view"):
                yield Static(id="code", expand=True)
            yield ZPKView(self.path)
        yield FileBrowserFooter()

    def on_mount(self) -> None:
        self.query_one(FilteredDirectoryTree).focus()
        self.refresh_filetree()

    def on_load(self) -> None:
        """Called when the app has loaded."""
        pass

    def refresh_filetree(self) -> None:
        self.query_one("#file_filter_input", Input).value = ""
        # self.on_input_submitted(input.Submitted(value=""))

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
        await asyncio.sleep(0.3)  # 非阻塞延时1秒
        # 执行需要延时后处理的任务
        self.query_one(FilteredDirectoryTree).remove()
        self.query_one(Container).mount(FilteredDirectoryTree(self.path, value, id="tree-view"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when the user presses enter in the input."""
        self.filter_text = event.value
        self.query_one(FilteredDirectoryTree).remove()
        self.query_one(Container).mount(FilteredDirectoryTree(self.path, self.filter_text, id="tree-view"))


    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected):
        path = str(event.path)
        zpk_view = self.query_one(ZPKView)
        print("fodler selected path", path)
        zpk_view.set_folder_path(path)

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#code", Static)
        zpk_view = self.query_one(ZPKView)
        syntax = " "
        try:
            path = str(event.path)
            if ".ZPK" in path:
                # code_view.update(path)
                zpk_view.set_path(path)
            else:
              zpk_view.set_folder_path(path)
              syntax = Syntax.from_path(
                  str(event.path),
                  line_numbers=True,
                  word_wrap=False,
                  indent_guides=True,
                  theme="github-dark",
              )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            if syntax != " ":
              code_view.update(syntax)  
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)

    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree

    def action_quit(self) -> None:
        """Called in response to key binding."""
        self.app.pop_screen()


if __name__ == "__main__":
    FileBrowser().run()
