# pyinstaller -F AutoFish_v0.2.py -w
import random
import sys
import threading
import time
import tkinter as tk

import cv2
import numpy as np
import pyautogui
import sounddevice as sd

wow_window = None
control_window:tk.Tk = None
target_image = cv2.imread('var/target_image.png', cv2.IMREAD_GRAYSCALE)  # 读取当前目录的目标浮标图片
duration = 2  # 每次录制 2 秒
similarity_threshold = 0.65  # 设置匹配的阈值
threshold = 1.5  # 音频活动的阈值
app_name = "魔兽世界"
run_flag = True
similarity_entry: tk.Entry = None  # 匹配度输入框
volume_entry: tk.Entry = None  # 音量输入框
app_name_entry: tk.Entry = None  # 窗口名输入框

sampling_rate = 44100  #
blocksize = 2048
keep_running = True

total_count = 0
log_text: tk.Text = None


# 音频回调函数
def audio_callback(indata, frames, time, status):
    global keep_running
    volume = np.linalg.norm(indata)  # 计算音量的L2范数
    if volume > threshold:
        print_log_text(f"音量范数:{round(volume, 2)} \n")
        print_log_text("已上钩,响起水花声,收杆,收杆,收杆\n 执行下一轮钓鱼循环\n")
        pyautogui.rightClick()  # 鼠标右击
        keep_running = False  # 停止音频捕获


# 创建控制窗口的函数
def create_control_window():
    global log_text, similarity_entry, volume_entry, app_name_entry,control_window

    # 创建一个300x400的窗口
    control_window = tk.Tk()
    control_window.geometry("330x620")
    control_window.title("钓鱼控制窗口v0.2")

    # 添加文本框以显示日志
    log_text = tk.Text(control_window, height=15, width=40, wrap='word')
    log_text.pack()
    log_text.pack(expand=True, fill='both')
    log_text.config(bg='black', fg='white')

    # 添加窗口名输入框
    app_name_label = tk.Label(control_window, text="游戏窗口名称(默认:魔兽世界)")
    app_name_label.pack()
    app_name_entry = tk.Entry(control_window)
    app_name_entry.insert(0, str(app_name))
    app_name_entry.pack()

    # 添加匹配度输入框,只能输入0.1-0.9,默认为0.7,并且给similarity_threshold赋值
    similarity_label = tk.Label(control_window, text="匹配度（0.1-0.9）:")
    similarity_label.pack()
    similarity_entry = tk.Entry(control_window)
    similarity_entry.insert(0, str(similarity_threshold))
    similarity_entry.pack()

    # 添加音量范试,只能输入1.3-5.0,默认1.5,并且给threshold赋值
    volume_label = tk.Label(control_window, text="音量阈值（1.3-5.0）:")
    volume_label.pack()
    volume_entry = tk.Entry(control_window)
    volume_entry.insert(0, str(threshold))
    volume_entry.pack()

    # 启动钓鱼逻辑
    start_button = tk.Button(control_window, text="开始钓鱼", command=fishing_thread.start)
    start_button.pack()
    start_button.pack(expand=True, fill='both')

    # 窗口置顶
    control_window.attributes('-topmost', True)
    #
    control_window.protocol("WM_DELETE_WINDOW", lambda: (
        end_program(),
        control_window.destroy(),
        sys.exit(0)
    ))

    # 启动Tkinter主循环
    control_window.mainloop()


# 钓鱼主逻辑
def fishing_logic():
    global wow_window, total_count, keep_running, similarity_threshold, threshold, log_text, app_name
    try:
        app_name = app_name_entry.get()
        active_wow_window()
        time.sleep(1)
        while run_flag:
            if similarity_entry.get():
                similarity_threshold = float(similarity_entry.get())
            if volume_entry.get():
                threshold = float(volume_entry.get())
            print_log_text(f"已设置匹配度:{similarity_threshold}\n音量阈值:{round(threshold, 2)}\n")
            total_count += 1
            print_log_text(f"第{total_count}次钓鱼\n")

            # 按下1键开始钓鱼
            pyautogui.press('1')
            time.sleep(3)
            # 获取窗口截图
            screenshot = pyautogui.screenshot(
                region=(wow_window.left, wow_window.top, wow_window.width, wow_window.height))
            screenshot_np = np.array(screenshot)
            screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

            target_val = 0
            max_loc_val = 0

            for i in range(10):  # 尝试多次匹配
                result = cv2.matchTemplate(screenshot_np, target_image, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                print_log_text(f"---第{i + 1}次匹配度: {round(max_val, 2)}\n")
                if max_val >= similarity_threshold:
                    target_val = max_val
                    max_loc_val = max_loc
                    break
                else:
                    screenshot = pyautogui.screenshot(
                        region=(wow_window.left, wow_window.top, wow_window.width, wow_window.height))
                    screenshot_np = np.array(screenshot)
                    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

            if target_val >= similarity_threshold:
                # 浮标的左上角位置
                target_x, target_y = max_loc_val
                float_center_x = target_x + target_image.shape[1] // 2
                float_center_y = target_y + target_image.shape[0] // 2
                pyautogui.moveTo(float_center_x, float_center_y, random.uniform(0.3, 0.9))
                print_log_text(f"浮标找到，鼠标移动到位置: ({float_center_x}, {float_center_y})\n")
                # 开始捕获音频
                audio_thread = threading.Thread(target=start_audio_capture)
                audio_thread.start()
                keep_running = True  # 重置标志
                # 线程超时处理10s
                audio_thread.join(10)
            else:
                print_log_text("未找到浮标\n")
                time.sleep(1)  # 增加等待时间
    except Exception as e:
        print_log_text(f"{e}\n")
    finally:
        print("程序结束!")
        control_window.destroy(),
        sys.exit(0)


# 用于异步捕获音频的函数
def start_audio_capture():
    with sd.InputStream(callback=audio_callback, channels=2, samplerate=sampling_rate, blocksize=blocksize):
        while keep_running:
            sd.sleep(100)  # 持续捕获音频


# 输出日志
def print_log_text(text: str):
    if run_flag and log_text is not None:
        log_text.insert(tk.END, text)
        log_text.see(tk.END)


# 获取并激活魔兽世界窗口
def active_wow_window():
    global wow_window
    windows = pyautogui.getWindowsWithTitle(app_name)
    if len(windows) > 0:
        wow_window = windows[0]
        wow_window.activate()
    else:
        # 窗口提示
        pyautogui.alert("未找到魔兽世界游戏窗口,请检查游戏是否在运行或者窗口名称是否正确") and sys.exit(0)


def end_program():
    global run_flag
    run_flag = False

    # 或许应该保持配置信息


if __name__ == '__main__':
    active_wow_window()

    # 创建并启动窗口线程
    window_thread = threading.Thread(target=create_control_window)
    window_thread.start()

    # 创建并启动钓鱼逻辑线程
    fishing_thread = threading.Thread(target=fishing_logic)
    # fishing_thread.start()
