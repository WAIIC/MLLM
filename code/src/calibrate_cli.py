# calibrate_cli.py
import sys
from utils_robot import robot, handeye

def main() -> None:
    print("=== MyCobot 手眼标定 CLI ===")
    n = int(input("请输入标定点数: "))#建议是4个
    px_list, wl_list = [], []
    for i in range(n):
        px = tuple(map(int,   input(f"第{i+1}点 像素坐标 x y: ").split()))
        wl = tuple(map(float, input(f"第{i+1}点 机械臂坐标 x y: ").split()))
        px_list.append(px)
        wl_list.append(wl)
    handeye.calibrate(px_list, wl_list, max_error=2.0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)