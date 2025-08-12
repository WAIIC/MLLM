# agent_go.py
# 「灵晰」多模态AI机械臂——以智能理解重写生产规则，你的全感知智能协作桌面助手。

print('\n视觉感知 · 语义理解 · 精准执行——多模态AI重塑机械臂新定义')
print('中科（梁溪）人工智能创新中心 2025-7-22 \n')

# 导入常用函数
from utils_asr import *             # 录音+语音识别
from utils_robot import *           # 连接机械臂
from utils_llm import *             # 大语言模型API
from utils_led import *             # 控制LED灯颜色
from utils_camera import *          # 摄像头
from utils_robot import *           # 机械臂运动
from utils_pump import *            # GPIO、吸泵
from utils_vlm_move import *        # 多模态大模型识别图像，吸泵吸取并移动物体
from utils_drag_teaching import *   # 拖动示教
from utils_agent import *           # 智能体Agent编排
from utils_tts import *             # 语音合成模块

# print('播放欢迎词')
pump_off()
# back_zero()
#play_wav('asset/welcome.wav')

message=[]
message.append({"role":"system","content":AGENT_SYS_PROMPT})
def agent_play():
    '''
    主函数，语音控制机械臂智能体编排动作
    '''
    # 归零
    back_zero()

    start_record_ok = input('是否开启录音，输入数字录音指定时长，按k打字输入，按c输入默认指令\n')
    if str.isnumeric(start_record_ok):
        DURATION = int(start_record_ok)
        record(DURATION=DURATION)   # 录音
        order = speech_recognition() # 语音识别
    elif start_record_ok == 'k':
        order = input('请输入指令')
    elif start_record_ok == 'c':
        order = '先归零，再摇头'
    else:
        print('无指令，退出')
        # exit()
        raise NameError('无指令，退出')

    message.append({"role": "user", "content": order})
    agent_plan_output = eval(agent_plan(message))
    
    print('编排动作如下\n', agent_plan_output)
    plan_ok = 'c'
    if plan_ok == 'c':
        response = agent_plan_output['response']
        print('开始语音合成')
        tts(response)                     # 语音合成，导出wav音频文件
        play_wav('temp/tts.wav')          # 播放语音合成音频文件
        output_other=''
        for each in agent_plan_output['function']: # 运行智能体规划编排的每个函数
            print('开始执行动作', each)
            ret=eval(each)
            if ret!=None:
                output_other=ret
    elif plan_ok =='q':
        # exit()
        raise NameError('按q退出')
    agent_plan_output['response']+='.'+ output_other
    message.append({"role":"assistant","content":str(agent_plan_output)})

# agent_play()
if __name__ == '__main__':
    while True:
        agent_play()

