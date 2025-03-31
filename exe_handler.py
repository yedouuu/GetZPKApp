import os
import pyautogui
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import pyperclip 

exe_path = r"D:\\200_WL\\280_Project\\WL_GL18\\04_Software\\1_WLGL18_240411\\GLTooL_V3.0.1.exe"

def locate_perf_test(img_path: str, callback):
  """ 快速图像定位耗时测试 """
  start_time = time.time()
  ret = callback(img_path)
  end_time = time.time()
  print(f"图像定位耗时：{end_time - start_time}秒")

  return ret


def fast_image_locate(img_path, region=None, confidence=0.9):
  """ 加速图像定位 """
  return pyautogui.locateCenterOnScreen(img_path, region=region, confidence=confidence)


def wait_for_window(title, timeout=10):
    """等待窗口出现，设置超时时间"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        windows = pyautogui.getWindowsWithTitle(title)
        if windows:
            return windows[0]
        time.sleep(0.3)
    return None

def click_and_type(position, text, enter=True):
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


def find_with_retry(img_path, region=None, max_retries=3, confidence=0.9):
    """添加重试机制的图像查找"""
    try:
      for _ in range(max_retries):
          result = fast_image_locate(img_path, region, confidence)
          if result:
              return result
          time.sleep(0.1)
      return None
    except Exception as e:
        print(f"【ERROR】图像查找错误：{e}, path:{img_path}")
        input("按任意键退出...")
        exit()

def executer(img_path, file_system_path, mainboard_path, boot_path, ui_path, GIN_name, factory_code="WL"):
    pyautogui.hotkey('ctrl', 'win', 'd')

    pyautogui.alert("即将开始自动化操作，请不要操作鼠标键盘！")
    pyautogui.PAUSE = 0.1  # 减少操作间隔

    # 启动程序
    process = subprocess.Popen(exe_path)
    
    # 等待主窗口出现
    main_window = wait_for_window("GL升级镜像制作工具")
    if not main_window:
        print("程序启动超时！")
        return
    
    time.sleep(0.1)

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
        find_func = partial(find_with_retry, region=locate_region)
        positions = list(executor.map(lambda x: find_func(x[0]), items))

    # 按顺序执行点击和输入操作
    for (_, text), position in zip(items, positions):
        retry_count = 0
        while retry_count < 3:
            if click_and_type(position, text):
                break
            retry_count += 1
            if retry_count == 3:
                print(f"未找到或无法输入 {text}")
                return False
            time.sleep(0.1)

    
    pos = find_with_retry("./assets/build_GIN.png")
    pyautogui.click(pos)

    # 等待完成窗口出现
    info_window = wait_for_window("信息")
    if not info_window:
        print("程序启动超时！")
        return
    
    time.sleep(0.3)

    ok_locate_region = info_window.left, info_window.top, info_window.width, info_window.height
    print(ok_locate_region)
    pos = find_with_retry("./assets/ok_button.png", region=ok_locate_region)
    pyautogui.click(pos)

    pos = find_with_retry("./assets/exit_button.png")
    pyautogui.click(pos)

    pyautogui.hotkey('ctrl', 'win', 'F4')
    return True


def pack_GIN(img_path, model, file_system_path, mainboard_path, boot_path, ui_path, factory_code="WL"):
  GIN_name = f"{factory_code}_\
{model}_\
{mainboard_path.split(".")[0].split('_')[-1]}_\
{img_path.split(".")[0].split('_')[-1]}_\
{file_system_path.split(".")[0].split('_')[-1]}"
  print(GIN_name)

  executer(img_path, file_system_path, mainboard_path, boot_path, ui_path, GIN_name, factory_code="WL")

def main():
  try:
    # 直接执行命令
    return_code = os.system(f'"{exe_path}"')
    if return_code == 0:
      print("执行成功")
    else:
      print(f"执行失败，返回码：{return_code}")
  except Exception as e:
    print(f"错误：{e}")


if __name__ == "__main__":
  img_path = r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\GL18_6140.bin"
  file_system_path = r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\rootfs_20011b.bin"
  mainboard_path = r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\M4_WLGL20_B00_AT8236_4257A.bin"
  boot_path = r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\BOOT.bin"
  ui_path = r"D:\200_WL\280_Project\WL_GL18\04_Software\1_WLGL18_240411\ui_resource_UN60_ENRU.bin"
  
  pack_GIN(img_path, file_system_path, mainboard_path, boot_path, ui_path)