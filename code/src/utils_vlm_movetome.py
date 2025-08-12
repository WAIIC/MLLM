

from utils_robot import *
from utils_asr import *
from utils_vlm import *
import time
import numpy as np
import base64
import json
HEIGHT_SAFE = 250          # 搬运安全高度
HEIGHT_START = 95        # 起点高度
HEIGHT_END   = 250         # 终点高度

def vlm_movetome(PROMPT='我把绿色方块拿给我', input_way='keyboard'):
    '''
    多模态识别图像，吸泵吸取并移动物体
    input_way：speech语音输入，keyboard键盘输入
    '''

    # 机械臂归零
    print('机械臂归零')
    mc.send_angles([0, 0, 0, 0, 0, 0], 50)
    time.sleep(1)
    top_view_shot(check=False)

    img_path = 'temp/vl_now.jpg'

    n = 1
    while n < 5:
        try:
            print('    尝试第 {} 次访问多模态大模型'.format(n))
            result = QwenVL_api(PROMPT, img_path='temp/vl_now.jpg', vlm_option=2)
            #result = yi_vision_api(PROMPT, img_path='temp/vl_now.jpg')
            print('    多模态大模型调用成功')
            print(result)
            break
        except Exception as e:
            print('    返回数据结构错误，再尝试一次', e)
            n += 1

    def scale(xy):
        return xy
    start_name = result['start']
    sx_min, sy_min, sx_max, sy_max = scale(result['start_xyxy'][0] + result['start_xyxy'][1])
    sx_c = (sx_min + sx_max) // 2
    sy_c = (sy_min + sy_max) // 2
    START_X_CENTER = sx_c
    START_Y_CENTER = sy_c
    # 起点，机械臂坐标
    START_X_MC, START_Y_MC = eye2hand(START_X_CENTER, START_Y_CENTER)

    ## 吸泵吸取移动物体
    pump_movetome(mc=mc, XY_START=[START_X_MC, START_Y_MC],HEIGHT_START = 95 , XY_END=[250, 50], HEIGHT_END=250, HEIGHT_SAFE=250)

    print('任务完成')
    cv2.destroyAllWindows()  # 关闭所有opencv窗口

