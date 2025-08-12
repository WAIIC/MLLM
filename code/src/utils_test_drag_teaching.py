# drag_teach.py
# 按键说明见菜单

import os
import sys
import time
import json
import threading
import termios
import tty

from pymycobot import MyCobot280
from pymycobot import PI_PORT, PI_BAUD

# ---------------- 连接机械臂 ----------------
mc = MyCobot280(PI_PORT, PI_BAUD, debug=False)

# ---------------- 终端原始模式 ----------------
class _Raw(object):
    def __init__(self, stream):
        self.stream = stream
        self.fd = self.stream.fileno()
    def __enter__(self):
        self.original = termios.tcgetattr(self.stream)
        tty.setcbreak(self.stream)
    def __exit__(self, *args):
        termios.tcsetattr(self.stream, termios.TCSANOW, self.original)

# ---------------- 主逻辑 ----------------
class DragTeacher:
    def __init__(self):
        self.recording = False
        self.playing = False
        self.record = []
        self.t_record = None
        self.t_play = None

    def _recorder(self):
        while self.recording:
            enc = mc.get_encoders()
            if enc:
                self.record.append(enc)
            time.sleep(0.1)

    def start_record(self):
        self.record.clear()
        self.recording = True
        mc.set_fresh_mode(0)
        self.t_record = threading.Thread(target=self._recorder, daemon=True)
        self.t_record.start()
        print("\n>>> 开始录制，按 c 结束录制")

    def stop_record(self):
        if self.recording:
            self.recording = False
            self.t_record.join()
            print(">>> 录制结束")

    def play_once(self):
        if not self.record:
            print(">>> 无录制数据")
            return
        print(">>> 回放一次")
        for enc in self.record:
            mc.set_encoders(enc, 80)
            time.sleep(0.1)
        print(">>> 回放结束")

    def _looper(self):
        idx = 0
        n = len(self.record)
        while self.playing:
            mc.set_encoders(self.record[idx % n], 80)
            idx += 1
            time.sleep(0.1)

    def start_loop(self):
        if not self.record:
            print(">>> 无录制数据")
            return
        self.playing = True
        self.t_play = threading.Thread(target=self._looper, daemon=True)
        self.t_play.start()
        print(">>> 开始循环回放，按 P 停止")

    def stop_loop(self):
        if self.playing:
            self.playing = False
            self.t_play.join()
            print(">>> 停止循环回放")

    # ---------- 本地文件 ----------
    def save(self):
        if not self.record:
            print(">>> 无数据可保存")
            return
        os.makedirs("temp", exist_ok=True)
        with open("temp/record.txt", "w") as f:
            json.dump(self.record, f, indent=2)
        print(">>> 已保存 temp/record.txt")

    def load(self):
        try:
            with open("temp/record.txt") as f:
                self.record = json.load(f)
            print(">>> 已加载轨迹")
        except Exception as e:
            print(">>> 加载失败", e)

    # ---------- 菜单 ----------
    def menu(self):
        print("""
拖拽示教 独立版
r : 开始录制
c : 停止录制
p : 回放一次
P : 循环/停止循环
s : 保存轨迹
l : 加载轨迹
f : 放松机械臂
q : 退出
----------------""")

    def run(self):
        self.menu()
        while True:
            with _Raw(sys.stdin):
                key = sys.stdin.read(1).lower()
            if key == "q":
                break
            elif key == "r":
                self.start_record()
            elif key == "c":
                self.stop_record()
            elif key == "p":
                self.play_once()
            elif key == "p" and self.playing:  # 实际由 stop_loop 处理
                self.stop_loop()
            elif key == "p":                   # 循环切换
                if not self.playing:
                    self.start_loop()
                else:
                    self.stop_loop()
            elif key == "s":
                self.save()
            elif key == "l":
                self.load()
            elif key == "f":
                mc.release_all_servos()
                print(">>> 机械臂已放松")
            else:
                self.menu()

# ---------------- 主入口 ----------------
if __name__ == "__main__":
    print("机械臂归零 ...")
    mc.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(3)

    DragTeacher().run()

    print("机械臂归零 ...")
    mc.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(2)
    print("已退出")
