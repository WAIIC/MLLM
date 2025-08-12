# utils_vlm.py
# 多模态大模型、可视化

print('导入视觉大模型模块')

import time
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import openai
import base64
import json
# 中文字体路径（请确保存在）
font = ImageFont.truetype('asset/SimHei.ttf', 26)

from API_KEY import *          # YI_KEY / Qwen_KEY
from utils_tts import *        # tts / play_wav

OUTPUT_VLM = ''

# ---------- 系统提示 ----------
SYSTEM_PROMPT_CATCH = '''
我即将说一句给机械臂的指令，你帮我从这句话中提取出起始物体和终止物体，并从这张图中分别找到这两个物体左上角和右下角的像素坐标，输出json数据结构。
示例：
{
 "start":"红色方块",
 "start_xyxy":[[102,505],[324,860]],
 "end":"房子简笔画",
 "end_xyxy":[[300,150],[476,310]]
}
只回复json本身即可，不要回复其它内容
我现在的指令是：
'''
SYSTEM_PROMPT_CATCHTOME = '''
我即将说一句给机械臂的指令，你帮我从这句话中提取出起始物体，并从这张图中找到起始物体左上角和右下角的像素坐标，输出json数据结构。
例如，如果我的指令是：请把红色方块拿给我。
你输出这样的格式：
{
 "start":"红色方块",
 "start_xyxy":[[102,505],[324,860]]
}
只回复json本身即可，不要回复其它内容

我现在的指令是：
'''
SYSTEM_PROMPT_VQA = '''
告诉我图片中每个物体的名称、类别和作用。每个物体用一句话描述。
示例：
连花清瘟胶囊，药品，治疗感冒。
盘子，生活物品，盛放东西。
氯雷他定片，药品，治疗抗过敏。
我现在的指令是：
'''

# ---------- Yi-Vision ----------
def yi_vision_api(prompt='帮我把红色方块放在钢笔上', img_path='temp/vl_now.jpg', vlm_option=0):
    if vlm_option == 0:
        system = SYSTEM_PROMPT_CATCH
    else:
        system = SYSTEM_PROMPT_VQA

    client = openai.OpenAI(api_key=YI_KEY, base_url="https://api.lingyiwanwu.com/v1")

    with open(img_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()

    res = client.chat.completions.create(
        model="yi-vision-v2",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system + prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }
        ]
    )

    result = res.choices[0].message.content.strip()
    if vlm_option == 0:
        return eval(result)
    else:
        print(result)
        tts(result)
        play_wav('temp/tts.wav')
        return result


# ---------- Qwen-VL ----------
def QwenVL_api(prompt='帮我把红色方块放在钢笔上',
               img_path='temp/vl_now.jpg',
               vlm_option=0,
               max_retry=4):
    """
    调用 Qwen-VL 并安全解析 JSON
    return: dict，如 {"start":"...","start_xyxy":[...], ...}
    """

    if vlm_option==0:
        system=SYSTEM_PROMPT_CATCH
    if vlm_option==1:
        system=SYSTEM_PROMPT_VQA
    if vlm_option==2:
        system=SYSTEM_PROMPT_CATCHTOME

    client = openai.OpenAI(
        api_key="sk-39e6900000000000003b42a520",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    with open(img_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()

    for attempt in range(1, max_retry + 1):
        try:
            res = client.chat.completions.create(
                model="qwen-vl-max",   # 可改 qwen-vl-max 等
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url",
                             "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                            {"type": "text",
                             "text": system + prompt}
                        ]
                    }
                ]
            )
            raw = res.choices[0].message.content.strip()

            # 去掉可能的 Markdown 代码块标记
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            result = json.loads(raw.strip())

            # 如果是纯问答模式，直接朗读
            if vlm_option != 0:
                print(result)
                tts(str(result))
                play_wav('temp/tts.wav')

            return result

        except Exception as e:
            print(f"[QwenVL_api] 第 {attempt} 次解析失败: {e}")
            print("原始返回内容 >>>\n", raw, "\n<<<")
            if attempt == max_retry:
                # 超过重试次数，给出一个空字典，避免外部崩溃
                return {"start": "", "start_xyxy": [[0, 0], [0, 0]],
                        "end": "",   "end_xyxy":   [[0, 0], [0, 0]]}

# ---------- 可视化 ----------
def post_processing_viz(result, img_path, check=False):
    """
    将 VLM 返回的 JSON 转为中心坐标并可视化
    返回：START_X_CENTER, START_Y_CENTER, END_X_CENTER, END_Y_CENTER
    """
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    factor = 999  # 缩放因子（与旧版保持一致）

    def scale(xy):
        return xy

    # 起点
    start_name = result['start']
    sx_min, sy_min, sx_max, sy_max = scale(result['start_xyxy'][0] + result['start_xyxy'][1])
    sx_c = (sx_min + sx_max) // 2
    sy_c = (sy_min + sy_max) // 2

    # 终点
    end_name = result['end']
    ex_min, ey_min, ex_max, ey_max = scale(result['end_xyxy'][0] + result['end_xyxy'][1])
    ex_c = (ex_min + ex_max) // 2
    ey_c = (ey_min + ey_max) // 2

    # 画框
    cv2.rectangle(img, (sx_min, sy_min), (sx_max, sy_max), (0, 0, 255), 3)
    cv2.circle(img, (sx_c, sy_c), 6, (0, 0, 255), -1)
    cv2.rectangle(img, (ex_min, ey_min), (ex_max, ey_max), (255, 0, 0), 3)
    cv2.circle(img, (ex_c, ey_c), 6, (255, 0, 0), -1)

    # 写字
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil)
    draw.text((sx_min, sy_min - 32), start_name, font=font, fill=(255, 0, 0))
    draw.text((ex_min, ey_min - 32), end_name, font=font, fill=(0, 0, 255))
    img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    # 保存
    os.makedirs('temp', exist_ok=True)
    os.makedirs('visualizations', exist_ok=True)
    cv2.imwrite('temp/vl_now_viz.jpg', img)
    cv2.imwrite(f'visualizations/{time.strftime("%Y%m%d%H%M")}.jpg', img)

    cv2.imshow('zihao_vlm', img)


    return sx_c, sy_c, ex_c, ey_c
