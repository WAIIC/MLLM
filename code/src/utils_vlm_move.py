# utils_vlm_move.py
# 同济子豪兄 2025-7-15
# 输入指令，多模态大模型识别图像，吸泵吸取并移动物体

from utils_robot import *
from utils_asr import *
from utils_vlm import *
import time

HEIGHT_SAFE = 220          # 搬运安全高度
HEIGHT_START = 85        # 起点高度
HEIGHT_END   = 130         # 终点高度

def vlm_move(PROMPT='帮我把绿色方块放在小猪佩奇上', input_way='keyboard'):
    '''
    多模态大模型识别图像，吸泵吸取并移动物体
    input_way：speech语音输入，keyboard键盘输入
    '''
    print('多模态大模型识别图像，吸泵吸取并移动物体')

    # 机械臂归零
    print('机械臂归零')
    mc.send_angles([0, 0, 0, 0, 0, 0], 50)
    time.sleep(1)

    ## 第一步：完成手眼标定
    print('第一步：完成手眼标定')

    ## 第二步：发出指令
    print('第二步，给出的指令是：', PROMPT)

    ## 第三步：拍摄俯视图
    print('第三步：拍摄俯视图')
    top_view_shot(check=False)

    ## 第四步：将图片输入给多模态视觉大模型
    print('第四步：将图片输入给多模态视觉大模型')
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
            print('    多模态大模型返回数据结构错误，再尝试一次', e)
            n += 1

    ## 第五步：视觉大模型输出结果后处理和可视化
    print('第五步：视觉大模型输出结果后处理和可视化')
    START_X_CENTER, START_Y_CENTER, END_X_CENTER, END_Y_CENTER = post_processing_viz(result, img_path, check=True)
    print('像素坐标为', START_X_CENTER, START_Y_CENTER, END_X_CENTER, END_Y_CENTER)
    ## 第六步：手眼标定转换为机械臂坐标
    print('第六步：手眼标定，将像素坐标转换为机械臂坐标')
    # 起点，机械臂坐标
    START_X_MC, START_Y_MC = eye2hand(START_X_CENTER, START_Y_CENTER)
    # 终点，机械臂坐标
    END_X_MC, END_Y_MC = eye2hand(END_X_CENTER, END_Y_CENTER)
    print('机械臂坐标为',START_X_MC, START_Y_MC,END_X_MC, END_Y_MC)

    ## 第七步：吸泵吸取移动物体
    print('第七步：吸泵吸取移动物体')
    pump_move(mc=mc, XY_START=[START_X_MC, START_Y_MC], XY_END=[END_X_MC, END_Y_MC])

    ## 第八步：收尾
    print('第八步：任务完成')
    cv2.destroyAllWindows()  # 关闭所有opencv窗口


def vlm_vqa(PROMPT='请数一数图中中几个方块', input_way='keyboard'):
    '''
    多模态大模型视觉问答功能
    input_way：speech语音输入，keyboard键盘输入
    '''
    # 机械臂归零
    print('机械臂归零')
    mc.send_angles([0, 0, 0, 0, 0, 0], 50)
    time.sleep(3)

    print('第二步，给出的指令是：', PROMPT)
    top_view_shot(check=False)
    img_path = 'temp/vl_now.jpg'

    result = QwenVL_api(PROMPT, img_path='temp/vl_now.jpg', vlm_option=1)
    print('    多模态大模型调用成功！')

    cv2.destroyAllWindows()  # 关闭所有opencv窗口
    return result