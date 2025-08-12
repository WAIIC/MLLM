# utils_tts.py
# 语音合成

import os
import appbuilder
from API_KEY import *
import pyaudio
import wave

tts_ab = appbuilder.TTS()

def tts(TEXT='我是多模态六轴机械臂', tts_wav_path = 'temp/tts.wav'):
    '''
    语音合成TTS，生成wav音频文件
    '''
    inp = appbuilder.Message(content={"text": TEXT})
    out = tts_ab.run(inp, model="paddlespeech-tts", audio_type="wav")
    # out = tts_ab.run(inp, audio_type="wav")
    with open(tts_wav_path, "wb") as f:
        f.write(out.content["audio_binary"])
    # print("TTS语音合成，导出wav音频文件至：{}".format(tts_wav_path))

def play_wav(wav_file='asset/welcome.wav'):
    '''
    播放wav音频文件
    '''
    prompt = 'aplay -t wav {} -q'.format(wav_file)
    os.system(prompt)

