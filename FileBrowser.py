"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import os
from pathlib import Path
from rich.syntax import Syntax
from rich.traceback import Traceback
from pathlib import Path
from typing import Iterable

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Static, Button, Input
from textual.screen import Screen
from textual.reactive import reactive

from CopyFile import copy_to_clipboard

class ZPKView(Static):
    
    path = reactive("")

    def __init__(self, path: str) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Horizontal(
          Static(f"{self.path}", id="zpk_path"),
          Button("复制", variant="primary")  
        )
    
    def set_path(self, path: str) -> None:
        self.path = path
        file_name = path.split("\\")[-1].split(".")
        file_name = f"{file_name[0]}.{file_name[1][:4]}"
        self.query_one("#zpk_path", Static).update(file_name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
      # 调用函数，复制文件
      abs_path = os.path.abspath(self.path)
      copy_to_clipboard([abs_path])

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
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
            yield ZPKView(self.path)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(FilteredDirectoryTree).focus()
        # self.mount(Footer())

    def on_load(self) -> None:
        """Called when the app has loaded."""
        pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Called when the user submits input."""
        self.filter_text = event.value
        self.query_one(FilteredDirectoryTree).remove()
        self.query_one(Container).mount(FilteredDirectoryTree(self.path, self.filter_text, id="tree-view"))
        event.stop()


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
