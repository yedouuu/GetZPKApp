from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Button
from textual.message import Message
from textual.containers import Vertical, ScrollableContainer 
from textual.reactive import reactive
from textual import on
import os

class AutoCompleteInput(Input):
    suggestions = reactive([])
    all_suggestions = reactive([])
    selected_index = reactive(0)
    submitted = reactive(False)

    def on_mount(self):
        self.styles.border = ("round", "gray")
        self.styles.background = "#1e1e1e"
        self.styles.color = "white"
        self.styles.border_radius = 2

        self.suggestions_box = Static("")
        self.suggestions_box.styles.border = ("round", "gray")
        self.suggestions_box.styles.background = "black"
        self.suggestions_box.styles.color = "white"
        self.suggestions_box.styles.padding = (0, 1)
        self.suggestions_box.styles.display = "none"
        # self.suggestions_box.styles.column_span = 16
        # self.suggestions_box.styles.row_span = 2
        # self.suggestions_box.styles.layers = "above"
        #self.suggestions_box.styles.margin = (3, 0, 0, 0)

        self.parent.mount(self.suggestions_box)
        self.all_suggestions = self.list_all_dirs("./ZPK/")

    @on(Input.Changed)
    def handle_input_changed(self, event: Input.Changed) -> None:
        
        """ 如果是自动补全提交导致的更新，则不处理 """
        if self.submitted:
            self.submitted = False
            return

        self.suggestions = self.get_suggestions(event.value)
        required_height = len(self.suggestions) + 4
        current_height = self.parent.size.height
        print("AutoComplete height = ", self.parent.size.height)
        print("AutoComplete required_height = ", required_height)
        if self.suggestions:
            if current_height < required_height:
                new_row_span = (required_height / 3) if (required_height % 3) == 0 else (required_height / 3) + 1
                new_row_span = 8 if new_row_span > 8 else new_row_span
                self.parent.styles.row_span = new_row_span
                print("Update AutoComplete row_span = ", self.parent.styles.row_span)
            else:
                new_row_span = (required_height / 3) if (required_height % 3) == 0 else (required_height / 3) + 1
                new_row_span = 8 if new_row_span > 8 else new_row_span
                self.parent.styles.row_span = new_row_span
                print("Update AutoComplete row_span = ", self.parent.styles.row_span)
        else:
            self.parent.styles.row_span = 1
        self.selected_index = 0
        self.update_suggestions_display()
        self.submitted = False

    def on_key(self, event):
        #await super().on_key(event)
        if event.key in ("down", "up", "tab", "enter"):
            if event.key == "down" and self.suggestions:
                # Move selection down
                self.selected_index = (self.selected_index + 1) % len(self.suggestions)
            elif event.key == "up" and self.suggestions:
                # Move selection up
                self.selected_index = (self.selected_index - 1) % len(self.suggestions)
            elif event.key == "tab" and self.suggestions:
                event.stop()
                self.value = self.suggestions[self.selected_index]
                self.cursor_position = len(self.value)
                self.suggestions = []
                self.parent.styles.row_span = 1
                self.submitted = True
                self.post_message(self.Submitted(self, self.value))
            elif event.key == "enter" and self.suggestions:
                self.value = self.suggestions[self.selected_index]
                self.cursor_position = len(self.value)
                self.suggestions = []
                self.parent.styles.row_span = 1
                self.submitted = True
                #self.post_message(self.Submitted(self.value))

            print(self.suggestions_box)
            self.update_suggestions_display()


    def update_suggestions_display(self):
        if self.suggestions:
            suggestions_text = "\n".join(
                f"\033[1;32m> {s}\033[0m" if i == self.selected_index else f"{s}"
                for i, s in enumerate(self.suggestions)
            )
            # suggestions_text = "\n".join(self.suggestions)
            self.suggestions_box.update(suggestions_text)
            self.suggestions_box.styles.display = "block"
        else:
            self.suggestions_box.styles.display = "none"

    def list_all_dirs(self, path):
        directories = []
        # 使用 os.walk() 遍历路径中的所有目录和文件
        for root, dirs, _ in os.walk(path):
            # 将当前目录下的所有子目录添加到列表中
            for dir_name in dirs:
                #print(f"dir_name = {dir_name}\n\r root = {root}")
                directories.append(os.path.join(root, dir_name))
        return [dir.replace(path, "") for dir in directories]
    
    def get_suggestions(self, text):
        if text:
            return [s for s in self.all_suggestions if text.lower() in s.lower()]
        else:
            return []

class AutoCompleteContainer(ScrollableContainer):
    def compose(self) -> ComposeResult:
        yield AutoCompleteInput(placeholder="请输入要保存的文件夹...")

    class Submitted(Message):
        def __init__(self, value) -> None:
            self.value = value
            super().__init__()

    @on(AutoCompleteInput.Submitted)
    async def handle_auto_complete_input_submitted(self, event: AutoCompleteInput.Submitted):
        print(f"AutoCompleteInput submitted with value: {event.value}")
        self.refresh()  # 确保界面刷新以反映最新状态
        self.post_message(self.Submitted(event.value))
        


class AutoCompleteApp(App):

    def compose(self) -> ComposeResult:
        yield Vertical(
            AutoCompleteContainer(),
        )

if __name__ == "__main__":
    app = AutoCompleteApp()
    app.run()