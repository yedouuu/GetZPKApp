import os
# import pyautogui
from pywinauto import Application
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import pyperclip 
import shutil
import xml_Utils
from pathlib import Path

# exe_path = r"D:\\200_WL\\280_Project\\WL_GL18\\04_Software\\1_WLGL18_240411\\GLTooL_V3.0.1.exe"

class PyguiautoHandler:
  def locate_perf_test(self, img_path: str, callback):
    """ 快速图像定位耗时测试 """
    start_time = time.time()
    ret = callback(img_path)
    end_time = time.time()
    print(f"图像定位耗时：{end_time - start_time}秒")

    return ret


  def fast_image_locate(self, img_path, region=None, confidence=0.9):
    """ 加速图像定位 """
    return pyautogui.locateCenterOnScreen(img_path, region=region, confidence=confidence)


  def wait_for_window(self, title, timeout=10):
      """等待窗口出现，设置超时时间"""
      start_time = time.time()
      while time.time() - start_time < timeout:
          windows = pyautogui.getWindowsWithTitle(title)
          if windows:
              return windows[0]
          time.sleep(0.3)
      return None

  def click_and_type(self, position, text, enter=True):
      """统一处理点击和输入，使用剪贴板提高输入可靠性"""
      if position:
          pyautogui.click(position)
          # 将文本复制到剪贴板
          pyperclip.copy(text)
          time.sleep(0.02)

          # 使用快捷键粘贴
          pyautogui.hotkey('ctrl', 'v')
          time.sleep(0.05)  # 短暂等待确保粘贴完成
          return True
      return False


  def find_with_retry(
      self,
      img_path: str, 
      region: tuple[int, int, int, int] | None = None,
      max_retries: int = 3,
      confidence: float = 0.9
  ) -> tuple[int, int] | None:
      """
      Repeatedly attempt to locate an image on screen with retry mechanism.
      
      Args:
          img_path: Path to the image file to locate
          region: Optional tuple of (left, top, width, height) to search within
          max_retries: Maximum number of retry attempts
          confidence: Minimum confidence level for image matching (0-1)
      
      Returns:
          Tuple of (x, y) coordinates if found, None otherwise
      """
      if not os.path.isfile(img_path):
          xml_Utils.print_red_text(f"Error: Image file not found: {img_path}")
          return None

      try:
          abs_path = os.path.abspath(img_path)
          for attempt in range(1, max_retries + 1):
              xml_Utils.print_red_text(f"Attempt {attempt}/{max_retries} to locate image: {abs_path}")
              
              result = self.fast_image_locate(abs_path, region, confidence)
              if result:
                  xml_Utils.print_red_text(f"Successfully located image at position: {result}")
                  return result
                  
              if attempt < max_retries:
                  time.sleep(0.1 * attempt)  # Increasing delay between retries
                  
          xml_Utils.print_red_text(f"Failed to locate image after {max_retries} attempts")
          return None
          
      except Exception as e:
          xml_Utils.print_red_text(f"【{type(e)}】Error while searching for image: {str(e)}")
          return None

  def executer(self, img_path, file_system_path, mainboard_path, boot_path, ui_path, GIN_name, factory_code="WL"):
      # pyautogui.hotkey('ctrl', 'win', 'd')

      # pyautogui.alert("即将开始自动化操作，请不要操作鼠标键盘！")
      pyautogui.PAUSE = 0.1  # 减少操作间隔

      # 启动程序
      exe_path = xml_Utils.get_text("local_GLTool_path")
      process = subprocess.Popen(exe_path)
      
      # 等待主窗口出现
      main_window = self.wait_for_window("GL升级镜像制作工具")
      if not main_window:
          xml_Utils.print_red_text("程序启动超时！")
          return
      
      xml_Utils.print_red_text("GL升级镜像制作工具 启动成功")

      time.sleep(0.3)

      locate_region = main_window.left, main_window.top, main_window.width, main_window.height

      # 定义要处理的项目
      items = [
          ("./assets/imageboard.png",     f"{img_path}"),
          ("./assets/file_system.png",    f"{file_system_path}"),
          ("./assets/mainboard.png",      f"{mainboard_path}"),
          ("./assets/mainboard_boot.png", f"{boot_path}"),
          ("./assets/ui_resource.png",    f"{ui_path}"),
          # ("./assets/factory_code.png",   f"{factory_code}"),
          ("./assets/GIN_name.png",       f"{GIN_name}"),
      ]

      # 使用线程池并行处理图像识别
      with ThreadPoolExecutor(max_workers=6) as executor:
          find_func = partial(self.find_with_retry, region=locate_region)
          positions = list(executor.map(lambda x: find_func(x[0]), items))

      # 按顺序执行点击和输入操作
      for (_, text), position in zip(items, positions):
          retry_count = 0
          while retry_count < 3:
              if self.click_and_type(position, text):
                  break
              retry_count += 1
              if retry_count == 3:
                  xml_Utils.print_red_text(f"未找到或无法输入 {text}")
                  return False
              time.sleep(0.1)

      
      pos = self.find_with_retry("./assets/build_GIN.png")
      pyautogui.click(pos)

      # 等待完成窗口出现
      info_window = self.wait_for_window("信息")
      if not info_window:
          xml_Utils.print_red_text("程序启动超时！")
          return
      
      time.sleep(0.3)

      ok_locate_region = info_window.left, info_window.top, info_window.width, info_window.height
      print(ok_locate_region)
      pos = self.find_with_retry("./assets/ok_button.png", region=ok_locate_region)
      pyautogui.click(pos)

      pos = self.find_with_retry("./assets/exit_button.png")
      pyautogui.click(pos)

      # pyautogui.hotkey('ctrl', 'win', 'F4')
      return True

class PywinautoHandler:
    def __init__(self):
        self.app = None
        self.main_window = None
        self.active_window = None

    def _click_button(self, label_text):
        """通过标签文本定位并点击按钮"""
        try:
            label_button = f"{label_text}Button"
            button = self.active_window[label_button]
            print(f"点击按钮: {label_text} : {button}")
            button.click()
        except KeyError:
            raise Exception(f"未找到标签为 '{label_text}' 的按钮")
        except Exception as e:
            raise Exception(f"点击按钮 '{label_text}' 时发生错误: {str(e)}")

    def _find_edit_by_label(self, label_text):
        """
        通过标签文本定位对应的输入框
        Args:
            label_text: 标签文本
        Returns:
            输入框控件对象
        Raises:
            KeyError: 未找到对应标签的输入框
            Exception: 其他异常
        """
        try:
            label_edit = f"{label_text}Edit"
            edit_control = self.active_window[label_edit]
            if not edit_control.exists():
                raise KeyError(f"输入框不存在: {label_edit}")
            return edit_control
        except KeyError as e:
            raise KeyError(f"未找到标签为 '{label_text}' 的输入框") from e
        except Exception as e:
            raise Exception(f"定位输入框时发生错误: {str(e)}") from e

    def _fill_field(self, label, value):
        """通用字段填写方法"""
        start_time = time.time()
        
        # 定位目标输入框
        edit_control = self._find_edit_by_label(label)
        
        # edit_control.set_focus()
        edit_control.set_text(value)
        
        # 验证输入结果
        if edit_control.window_text() != value:
            raise Exception(f"输入验证失败: [{label}] 期望值[{value}] 实际值[{edit_control.window_text()}]")
            
        print(f"成功填写 [{label}] 耗时: {time.time()-start_time:.2f}s")

    def _background_startup(self, exe_path):
        """后台启动应用程序"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(exe_path, startupinfo=startupinfo)
            return process
        except Exception as e:
            raise Exception(f"启动应用程序失败: {str(e)}")

    def executer(self, img_path, file_system_path, mainboard_path, boot_path, ui_path, GIN_name, factory_code="WL"):
        exe_path = xml_Utils.get_text("local_GLTool_path")
        title = os.path.basename(exe_path)
        version = title.split('_')[1].split('.exe')[0]
        full_title = f"GL升级镜像制作工具{version}"

        # 启动应用程序
        # process = self._background_startup(exe_path)
        # self.app = Application(backend="win32").connect(process=process.pid)
        self.app = Application(backend="win32").start(exe_path)
        self.main_window = self.app.window(title=full_title)
        self.active_window = self.main_window
        
        print("window open, title:", full_title)
        # self.main_window.print_control_identifiers()
    
        try:
            # 定义要处理的项目
            # uia_items = [
            #     ("1000",    f"{img_path}"),
            #     ("1001",    f"{file_system_path}"),
            #     ("1002",    f"{mainboard_path}"),
            #     # ("1018",    f"{boot_path}"),
            #     ("1018",    f"{ui_path}"),
            #     ("1003",    f"{factory_code}"),
            #     ("1013",    f"{GIN_name}"),
            # ]

            win32_items = [
                ("图像板程序镜像",    f"{img_path}"),
                ("文件系统镜像",    f"{file_system_path}"),
                ("主控板固件镜像",    f"{mainboard_path}"),
                # ("1018",    f"{boot_path}"),
                ("图像资源镜像",    f"{ui_path}"),
                ("厂家编号",    f"{factory_code}"),
                ("镜像名",    f"{GIN_name}"),
            ]

            # 使用线程池并行处理,填写各个路径字段
            with ThreadPoolExecutor(max_workers=6) as executor:
                find_func = partial(self._fill_field)
                list(executor.map(lambda x: find_func(x[0], x[1]), win32_items))
            
            # 点击制作镜像按钮
            self._click_button("制作镜像")
            time.sleep(0.3)

            self.active_window = self.app.window(title="信息")
            self._click_button("确定")
            time.sleep(0.3)

            self.active_window = self.main_window
            self._click_button("退出")
            # self.main_window.child_window(auto_id="1011", control_type="Button").click()
            
        except Exception as e:
            print(f"操作失败: {str(e)}")
            raise

    def _fill_path(self, auto_id, value):
        """通用方法：通过auto_id定位输入框并填写值"""
        print(f"正在填写 [auto_id={auto_id}] -> {value}")
        edit_control = self.main_window.child_window(
            auto_id=auto_id, 
            control_type="Edit"
        )
        if not edit_control.exists():
            raise Exception(f"未找到auto_id={auto_id}的输入框")
            
        edit_control.set_text(value)
        print(f"已填写 [auto_id={auto_id}] -> {value}")

    def _click_browse_button(self, related_auto_id):
        """点击与输入框关联的浏览按钮（可选）"""
        # 根据浏览按钮的auto_id规律实现（示例：输入框auto_id=1000对应浏览按钮auto_id=1004）
        browse_btn = self.main_window.child_window(
            auto_id=str(int(related_auto_id)+4),  # 根据实际规律调整
            control_type="Button"
        )
        browse_btn.click()
      

def pack_GIN(PACK_INFO):
#   GIN_name = f"{factory_code}_\
# {model}_\
# {mainboard_path.split(".")[0].split('_')[-1]}_\
# {img_path.split(".")[0].split('_')[-1]}_\
# {file_system_path.split(".")[0].split('_')[-1]}"
  img_path         = PACK_INFO["img_path"]
  model            = PACK_INFO["model"]
  remote_path      = PACK_INFO["remote_path"]
  file_system_path = PACK_INFO["file_system_path"]
  mainboard_path   = PACK_INFO["mainboard_path"]
  boot_path        = PACK_INFO["boot_path"]
  ui_path          = PACK_INFO["ui_path"]
  factory_code     = PACK_INFO["factory_code"]
  customer_path    = PACK_INFO["customer_path"]

  GIN_name = xml_Utils.generate_new_name(remote_path, customer_path, factory_code)
  print(GIN_name)

  handler = PywinautoHandler()
  handler.executer(
      img_path=img_path,
      file_system_path=file_system_path, 
      mainboard_path=mainboard_path,
      boot_path=boot_path,
      ui_path=ui_path,
      GIN_name=GIN_name,
      factory_code=factory_code
  )
  
  GIN_path = os.path.join(os.path.abspath("./"), GIN_name + "_GLImage.GIN")
  if not os.path.exists(GIN_path):
    print(f"【Error】Source GIN file not found: {GIN_path}")
    return None, None
  
  dst_dir = os.path.abspath(xml_Utils.get_text("local_zpk_path"))
  dst_dir = os.path.join(dst_dir, customer_path if customer_path else model.replace("_", ""))
  dst_path = copy_gin_file(GIN_path, dst_dir)
        
  # 删除源文件
  os.remove(GIN_path)
  return os.path.basename(dst_path), dst_path


def copy_gin_file(src_file, dst_dir):
  """Copy GIN file to target directory with error handling"""
  try:
    # Ensure source file exists
    if not os.path.exists(src_file):
      print(f"【Error】Source file not found: {src_file}")
      return False
        
    # Create destination directory if it doesn't exist
    Path(dst_dir).mkdir(parents=True, exist_ok=True)
    
    # Construct destination path
    dst_file = os.path.join(dst_dir, os.path.basename(src_file))
    
    # Copy file with metadata
    print(f"【Info】Copying file:\nFrom: {src_file}\nTo: {dst_file}")
    dst_path = shutil.copy2(src_file, dst_file)
    
    # Verify copy was successful
    if os.path.exists(dst_file):
      print(f"【Success】File copied successfully")
      return dst_path
    else:
      print(f"【Error】Copy verification failed")
      return False
          
  except Exception as e:
    print(f"【Error】Failed to copy file: {str(e)}")
    return False

if __name__ == "__main__":
  PACK_INFO = {
    "img_path":         r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\GL18_6140.bin",
    "model":            "UN60D",
    "remote_path":      r"./1_WLGL18_240411/UN60D_ENRU/",  # This wasn't provided in original data
    "file_system_path": r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\rootfs_20011b.bin",
    "mainboard_path":   r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\M4_WLGL20_B00_AT8236_4257A.bin",
    "boot_path":        r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\BOOT.bin",
    "ui_path":          r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\ui_resource_UN60_ENRU.bin",
    "factory_code":     "WL",  # Using default from executer() function
    "customer_path":    "",    # This wasn't provided in original data
  }

  pack_GIN(PACK_INFO)
  # copy_gin_file()