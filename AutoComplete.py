from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Button
from textual.message import Message
from textual.containers import Vertical, ScrollableContainer, Container
from textual.validation import Validator, ValidationResult
from textual.reactive import reactive
from textual import on
import re
import os

class AutoCompleteInput(Input):
    suggestions = reactive([])
    error_msg = reactive([])
    all_suggestions = reactive([])
    selected_index = reactive(0)
    submitted = reactive(False)

    def on_mount(self):
        # self.styles.border = ("round", "gray")
        # self.styles.background = "#1e1e1e"
        # self.styles.color = "white"
        # self.styles.margin = (1, 0, 0, 0)
        # self.styles.border_radius = 2

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
        self.error_box = Static("")
        self.error_box.styles.border = ("round", "#d0506d")
        self.error_box.styles.background = "#d0506d"
        self.error_box.styles.color = "white"
        self.error_box.styles.padding = (0, 1)
        self.error_box.styles.display = "none"

        self.parent.mount(self.error_box)
        self.parent.mount(self.suggestions_box)
        self.all_suggestions = self.list_all_dirs("./ZPK/")

    @on(Input.Changed)
    def handle_input_changed(self, event: Input.Changed) -> None:
        
        """ 如果是自动补全提交导致的更新，则不处理 """
        if self.submitted:
            self.submitted = False
            return

        # 有输入才有validation_result对象，防止直接回车 和Tab时出现错误
        if event.validation_result:
            if not event.validation_result.is_valid:
                print("【ERROR】", event.validation_result.failure_descriptions)
                if not self.error_msg:
                    self.parent.styles.row_span += 2
                self.error_msg = event.validation_result.failure_descriptions
                self.update_error_display()
                self.post_message(self.Submitted(self, ""))      # 清空已提交的信息
                return
            else:
                if self.error_msg:
                    self.parent.styles.row_span -= 2 if self.parent.styles.row_span > 3 else 0
                    self.error_msg = []
                self.update_error_display()

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

        self.post_message(self.Submitted(self, self.value))
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
            elif event.key == "tab":
                # 如果有选中建议项，则进行提交
                # 若已经确认提交过，则重新展示所有建议项
                event.stop()
                if self.suggestions and self.submitted == False:
                    self.value = self.suggestions[self.selected_index]
                    self.cursor_position = len(self.value)
                    self.suggestions = []
                    self.parent.styles.row_span = 1
                    self.submitted = True
                    self.post_message(self.Submitted(self, self.value))
                else:
                    self.submitted = False
                    
                    if self.value == "":
                        self.suggestions = self.all_suggestions
                    
                    self.handle_input_changed(Input.Changed(self, self.value))

                
            elif event.key == "enter" and self.suggestions:
                # self.value = self.suggestions[self.selected_index]
                # self.cursor_position = len(self.value)
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

    def update_error_display(self):
        if self.error_msg:
            error_text = "\n".join(self.error_msg)
            self.error_box.update(error_text)
            self.error_box.styles.display = "block"
        else:
            self.error_box.styles.display = "none"

    def list_all_dirs(self, path):
        directories = []
        # 使用 os.walk() 遍历路径中的所有目录和文件
        for root, dirs, _ in os.walk(path):
            # 将当前目录下的所有子目录添加到列表中
            for dir_name in dirs:
                #print(f"dir_name = {dir_name}\n\r root = {root}")
                directories.append(os.path.join(root, dir_name))
        return [dir.replace(path, "") for dir in directories]
    
    def update_dirs(self):
        self.all_suggestions = self.list_all_dirs("./ZPK/")

    def get_suggestions(self, text):
        if text:
            return [s for s in self.all_suggestions if text.lower() in s.lower()]
        else:
            return []

class ValidFolderName(Validator):

    def is_valid_folder_name(self, folder_name: str) -> bool:
        # 正则表达式，确保文件夹名称不包含非法字符，并且不以.或空格结尾
        pattern = re.compile(r'^(?!^(con|prn|aux|nul|com[0-9]|lpt[0-9])(\..*)?$)(^[^<>:"/\\|?*\x00-\x1F]+$)', re.UNICODE)
        return bool(re.match(pattern, folder_name))
    

    def validate(self, value: str) -> ValidationResult:
        """Check whether the folder name is valid."""
        # invalid_chars = '<>:"/\\|?*'
        # windows_reserved_name = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "COM0", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9", "LP0"]

        if value == "":
            return self.success()

        value = value.replace("/", "\\").strip("\\")
        parts = value.split("\\")
        print(f"【DEBUG】folder path parts = {parts}")
        for part in parts:
            if not self.is_valid_folder_name(part):
                return self.failure(f"Folder name '{part}' is not valid .\r\n文件名'{part}'无效。")
        return self.success()

        # 检验文件路径是否合法
        # regex = "[a-z]|[A-Z]:(\\[^\\/&?\n]+)\\?"
        # if not re.match(regex, value):
        #     return self.failure(f"Folder name is not valid.\r\n文件名无效。")

        # 这是检验单个文件名是否合法的代码
        # if any(char in value for char in invalid_chars):
        #     return self.failure(f"Folder names cannot contain {invalid_chars}\r\n文件名不能包含 {invalid_chars}")
        
        # Checking if name is a reserved name in Windows
        # if value.upper() in windows_reserved_name:
        #     return self.failure(f"Folder name cannot be '{windows_reserved_name}'")

        # return self.success()

class AutoCompleteContainer(ScrollableContainer):

    def compose(self) -> ComposeResult:
        yield AutoCompleteInput(
            id="auto-complete-input", 
            classes="grey_input",
            placeholder="请输入要保存的文件夹...",
            validators=[
                ValidFolderName()
            ],
        )

    def on_mount(self):
        self.auto_complete_input = self.query_one(AutoCompleteInput)

    class Submitted(Message):
        def __init__(self, value) -> None:
            self.value = value
            super().__init__()

    @on(AutoCompleteInput.Submitted)
    async def handle_auto_complete_input_submitted(self, event: AutoCompleteInput.Submitted):
        print(f"AutoCompleteInput submitted with value: {event.value}")
        self.refresh()  # 确保界面刷新以反映最新状态
        self.post_message(self.Submitted(event.value))

    def auto_complete_update_dirs(self):
        self.auto_complete_input.update_dirs()


class AutoCompleteApp(App):

    def compose(self) -> ComposeResult:
        yield Vertical(
            AutoCompleteContainer(),
        )

if __name__ == "__main__":
    app = AutoCompleteApp()
    app.run()