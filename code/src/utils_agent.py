# utils_agent.py
# Agent智能体相关函数参考

from utils_llm import *

AGENT_SYS_PROMPT = '''

'''

def agent_plan(PROMPT='先回到原点，再把LED灯改为墨绿色，然后把绿色方块放在篮球上'):
    print('Agent智能体编排动作')
    agent_plan = llm_yi(PROMPT)
    return agent_plan
