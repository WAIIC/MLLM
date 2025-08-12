# utils_vlm_move.py
# 输入指令，多模态大模型识别图像，吸泵吸取并移动物体

from utils_robot import *
from utils_asr import *
from utils_vlm import *
import time

HEIGHT_SAFE = 220          # 搬运安全高度
HEIGHT_START = 85        # 起点高度
HEIGHT_END   = 130         # 终点高度

def vlm_move(PROMPT='', input_way='keyboard'):
    '''
    多模态大模型识别图像，吸泵吸取并移动物体
    input_way：speech语音输入，keyboard键盘输入
    '''


    # 机械臂归零
    print('机械臂归零')
    mc.send_angles([0, 0, 0, 0, 0, 0], 50)
    time.sleep(1)

    print('给出的指令是：', PROMPT)
    top_view_shot(check=False)
    img_path = 'temp/vl_now.jpg'

    n = 1
    while n < 5:
        try:
            print('    尝试第 {} 次访问多模态大模型'.format(n))
            result = QwenVL_api(PROMPT, img_path='temp/vl_now.jpg')
            #result = yi_vision_api(PROMPT, img_path='temp/vl_now.jpg')
            print('    多模态大模型调用成功！')
            print(result)
            break
        except Exception as e:
            print('    返回数据结构错误，再尝试一次', e)
            n += 1

    START_X_CENTER, START_Y_CENTER, END_X_CENTER, END_Y_CENTER = post_processing_viz(result, img_path, check=True)
    print('像素坐标为', START_X_CENTER, START_Y_CENTER, END_X_CENTER, END_Y_CENTER)

    # 起点，机械臂坐标
    START_X_MC, START_Y_MC = eye2hand(START_X_CENTER, START_Y_CENTER)
    # 终点，机械臂坐标
    END_X_MC, END_Y_MC = eye2hand(END_X_CENTER, END_Y_CENTER)

    print('机械臂坐标为',START_X_MC, START_Y_MC,END_X_MC, END_Y_MC)

    pump_move(mc=mc, XY_START=[START_X_MC, START_Y_MC], XY_END=[END_X_MC, END_Y_MC])

    cv2.destroyAllWindows()  # 关闭所有opencv窗口


def vlm_vqa(PROMPT='请数一数图中中几个方块', input_way='keyboard'):
    '''
    多模态大模型视觉问答功能
    input_way：speech语音输入，keyboard键盘输入
    '''
    # 机械臂归零
    mc.send_angles([0, 0, 0, 0, 0, 0], 50)
    time.sleep(3)

    print('给出的指令是：', PROMPT)
    top_view_shot(check=False)
    img_path = 'temp/vl_now.jpg'

    result = QwenVL_api(PROMPT, img_path='temp/vl_now.jpg', vlm_option=1)
    print('    多模态大模型调用成功')

    cv2.destroyAllWindows()  # 关闭所有opencv窗口
    return result