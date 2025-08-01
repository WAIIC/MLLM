# utils_robot.py
# 启动并连接机械臂，导入各种工具包

print('导入机械臂连接模块')

from pymycobot import MyCobot280
from pymycobot import PI_PORT, PI_BAUD
import cv2
import numpy as np
import time
from utils_pump import *

# 连接机械臂
mc = MyCobot280(PI_PORT, PI_BAUD)
# 设置运动模式为队列模式(0)
mc.set_fresh_mode(0)

def back_zero():
    '''
    机械臂归零
    '''
    print('机械臂归零')
    mc.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(3)


def relax_arms():
    print('放松机械臂关节')
    mc.release_all_servos()


def head_shake():
    # 左右摆头
    mc.send_angles([0.87, (-50.44), 47.28, 0.35, (-0.43), (-0.26)], 70)
    time.sleep(1)
    for count in range(2):
        mc.send_angle(5, 30, 80)
        time.sleep(0.5)
        mc.send_angle(5, -30, 80)
        time.sleep(0.5)
    mc.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(2)


def head_dance():
    # 跳舞
    mc.send_angles([0.87, (-50.44), 47.28, 0.35, (-0.43), (-0.26)], 70)
    time.sleep(1)
    for count in range(1):
        mc.send_angles([(-0.17), (-94.3), 118.91, (-39.9), 59.32, (-0.52)], 80)
        time.sleep(1.2)
        mc.send_angles([67.85, (-3.42), (-116.98), 106.52, 23.11, (-0.52)], 80)
        time.sleep(1.7)
        mc.send_angles([(-38.14), (-115.04), 116.63, 69.69, 3.25, (-11.6)], 80)
        time.sleep(1.7)
        mc.send_angles([2.72, (-26.19), 140.27, (-110.74), (-6.15), (-11.25)], 80)
        time.sleep(1)
        mc.send_angles([0, 0, 0, 0, 0, 0], 80)


def head_nod():
    # 点头
    mc.send_angles([0.87, (-50.44), 47.28, 0.35, (-0.43), (-0.26)], 70)
    for count in range(2):
        mc.send_angle(4, 13, 70)
        time.sleep(0.5)
        mc.send_angle(4, -20, 70)
        time.sleep(1)
        mc.send_angle(4, 13, 70)
        time.sleep(0.5)
    mc.send_angles([0.87, (-50.44), 47.28, 0.35, (-0.43), (-0.26)], 70)


def move_to_coords(X=150, Y=-130, HEIGHT_SAFE=230):
    print('移动至指定坐标：X {} Y {}'.format(X, Y))
    mc.send_coords([X, Y, HEIGHT_SAFE, 0, 180, 90], 20, 0)
    time.sleep(4)


def single_joint_move(joint_index, angle):
    print('关节 {} 旋转至 {} 度'.format(joint_index, angle))
    mc.send_angle(joint_index, angle, 40)
    time.sleep(2)


def move_to_top_view():
    print('移动至俯视姿态')
    mc.send_angles([39.19, -4.39, -69.43, -10.63, 1.75, 80.77], 10)
    time.sleep(3)


def top_view_shot(check=False):
    '''
    拍摄一张图片并保存
    check：是否需要人工看屏幕确认拍照成功，再在键盘上按q键确认继续
    '''
    print('    移动至俯视姿态')
    move_to_top_view()
    time.sleep(1.5)
    # 获取摄像头，传入0表示获取系统默认摄像头
    cap = cv2.VideoCapture(20)
    # 打开cap
    cap.open(20)
    time.sleep(1)
    success, img_bgr = cap.read()

    # 保存图像
    print('    保存至temp/vl_now.jpg')
    cv2.imwrite('temp/vl_now.jpg', img_bgr)

    # 屏幕上展示图像
    cv2.destroyAllWindows()  # 关闭所有opencv窗口
    cv2.imshow('waiic_vlm', img_bgr)

    # 关闭摄像头
    cap.release()


def eye2hand(X_im=160, Y_im=120):
    '''
    输入目标点在图像中的像素坐标，转换为机械臂坐标
    '''

    # 整理两个标定点的坐标
    cali_1_im = [138,339]  # 左下角，第一个标定点的像素坐标，要手动填！
    cali_1_mc = [135.5,20.6]  # 左下角，第一个标定点的机械臂坐标，要手动填！
    cali_2_im = [369,72]  # 右上角，第二个标定点的像素坐标   `
    cali_2_mc = [231.7,167.2]  # 右上角，第二个标定点的机械臂坐标，要手动填！

    X_cali_im = [cali_1_im[0], cali_2_im[0]]  # 像素坐标
    X_cali_mc = [cali_1_mc[0], cali_2_mc[0]]  # 机械臂坐标
    Y_cali_im = [cali_2_im[1], cali_1_im[1]]  # 像素坐标，先小后大
    Y_cali_mc = [cali_2_mc[1], cali_1_mc[1]]  # 机械臂坐标，先大后小

    # X差值
    X_mc = int(np.interp(X_im, X_cali_im, X_cali_mc))

    # Y差值
    Y_mc = int(np.interp(Y_im, Y_cali_im, Y_cali_mc))

    return X_mc, Y_mc


def pump_move(mc,
              XY_START=[230, -50],
              HEIGHT_START=90,
              XY_END=[100, 220],
              HEIGHT_END=120,
              HEIGHT_SAFE=220):
    ...
    '''
    用吸泵，将物体从起点吸取移动至终点

    mc：机械臂实例
    XY_START：起点机械臂坐标
    HEIGHT_START：起点高度，方块用90，药盒子用70
    XY_END：终点机械臂坐标
    HEIGHT_END：终点高度
    HEIGHT_SAFE：搬运途中安全高度
    '''
    # 设置运动模式为队列模式(0)
    mc.set_fresh_mode(0)

    # 吸泵移动至物体上方
    print('    吸泵移动至物体上方')
    mc.send_coords([XY_START[0], XY_START[1], HEIGHT_SAFE, 0, 180, 90], 20, 0)
    time.sleep(4)

    # 开启吸泵
    pump_on()

    # 吸泵向下吸取物体
    print('    吸泵向下吸取物体')
    #mc.send_coords([XY_START[0], XY_START[1], HEIGHT_START, 0, 180, 90], 15, 0)
    mc.send_coords([XY_START[0], XY_START[1], 85, 0, 180, 90], 15, 0)
    time.sleep(3)

    # 升起物体
    print('    升起物体')
    mc.send_coords([XY_START[0], XY_START[1], HEIGHT_SAFE, 0, 180, 90], 20, 0)
    time.sleep(4)

    # 搬运物体至目标上方
    print('    搬运物体至目标上方')
    mc.send_coords([XY_END[0], XY_END[1], HEIGHT_SAFE, 0, 180, 90], 20, 0)
    time.sleep(3.5)

    # 向下放下物体
    print('    向下放下物体')
    mc.send_coords([XY_END[0], XY_END[1], HEIGHT_END, 0, 180, 90], 20, 0)
    time.sleep(3)

    # 关闭吸泵
    pump_off()

    # 机械臂归零
    print('    机械臂归零')
    mc.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(1)
def pump_movetome(mc,
              XY_START=[230, -50],
              HEIGHT_START=90,
              XY_END=[100, 220],
              HEIGHT_END=250,
              HEIGHT_SAFE=250):
    ...

    # 设置运动模式为队列模式(0)
    mc.set_fresh_mode(0)

    # 吸泵移动至物体上方
    print('    吸泵移动至物体上方')
    mc.send_coords([XY_START[0], XY_START[1], HEIGHT_SAFE, 0, 180, 90], 20, 0)
    time.sleep(4)

    # 开启吸泵
    pump_on()

    # 吸泵向下吸取物体

    print('    吸泵向下吸取物体')
    mc.send_coords([XY_START[0], XY_START[1], 75, 0, 180, 90], 15, 0)
    time.sleep(2)

    # 升起物体
    print('    升起物体')
    mc.send_coords([XY_START[0], XY_START[1], HEIGHT_SAFE, 0, 180, 90], 20, 0)
    time.sleep(3)

    # 搬运物体
    print('    搬运物体')
    mc.send_coords([146, -51, HEIGHT_SAFE, -90, 50, -80], 30, 0)
    time.sleep(3)
    mc.send_coords([-45, -150, HEIGHT_SAFE+50, -90, 61, -170], 30, 0)
    time.sleep(2)
    mc.send_coords([-200, -5, HEIGHT_SAFE, -130, 50, 60], 30, 0)
    time.sleep(7)
    # 关闭吸泵
    pump_off()

    # 机械臂归零
    print('    机械臂归零')
    mc.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(1)
