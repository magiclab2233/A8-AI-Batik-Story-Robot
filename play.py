from vosk import Model, KaldiRecognizer
import pyaudio
import sounddevice as sd
import numpy as np
import wave

import numpy as np  # 新增numpy处理音频
import subprocess
import os,sys
# 浏览器进程全局变量
browser_process = None

def start_browser():
    """启动Chromium浏览器"""
    global browser_process
    if browser_process is None or browser_process.poll() is not None:
        command = [
            "chromium-browser",
            "--use-fake-ui-for-media-stream",
            "index.html"
        ]
        env = os.environ.copy()
        env["DISPLAY"] = ":0"
        
        try:
            browser_process = subprocess.Popen(
                command,
                env=env,
                stdout=subprocess.DEVNULL,  # 禁止输出
                stderr=subprocess.DEVNULL
            )
            print("浏览器已启动")
        except Exception as e:
            print(f"启动浏览器失败: {e}")

def stop_browser():
    """关闭Chromium浏览器"""
    global browser_process
    if browser_process and browser_process.poll() is None:
        try:
            browser_process.terminate()  # 温和终止
            browser_process.wait(timeout=5)  # 等待进程结束
            print("浏览器已关闭")
        except subprocess.TimeoutExpired:
            browser_process.kill()  # 强制终止
            print("浏览器被强制终止")
        browser_process = None

def stereo_to_mono(data):
    """将双通道音频数据转为单通道（均值混合）"""
    audio_data = np.frombuffer(data, dtype=np.int16)
    # 分离左右声道并取平均
    mono = np.mean([audio_data[::2], audio_data[1::2]], axis=0)
    return mono.astype(np.int16).tobytes()  # 确保输出为int16格式

def play_audio():
    # 打开 WAV 文件
    filename = "notify.wav"
    wav_file = wave.open(filename, 'rb')

    # 读取音频数据
    num_channels = wav_file.getnchannels()
    sample_rate = wav_file.getframerate()
    num_frames = wav_file.getnframes()
    audio_data = wav_file.readframes(num_frames)

    # 将字节数据转换为 NumPy 数组
    audio_data_np = np.frombuffer(audio_data, dtype=np.int16)

    # 播放音频
    sd.play(audio_data_np, samplerate=sample_rate)
    sd.wait()  # 等待播放完成

def monitor():
    sys.stdout.flush()
    """在webrtc 不运行时监听音频输入，捕获唤醒词"""
    # 初始化模型
    model = Model("/home/pi/5o-1/model/vosk-model-small-cn-0.22")
    recognizer = KaldiRecognizer(model, 16000)
    print("start monitor audio")
    sys.stdout.flush()
    # 配置音频输入（保持双通道输入）
    mic = pyaudio.PyAudio()
    stream = mic.open(
        format=pyaudio.paInt16,
        channels=2,          # 硬件输入为双通道（如麦克风）
        rate=16000,
        input=True,
        frames_per_buffer=1024
    )
    
    while True:
        try:
            # 读取双通道数据
            raw_data = stream.read(1024)
            global browser_process
            if browser_process:
                continue
            # 转换单通道
            mono_data = stereo_to_mono(raw_data)
            # 使用单通道数据识别
            if recognizer.AcceptWaveform(mono_data):
                text = recognizer.Result().replace(' ','')
                print(text)
                sys.stdout.flush()
                if "老师" in text:  # 替换为你的唤醒词
                    print("唤醒词检测到!")
                    sys.stdout.flush()
                    start_browser()
        except Exception as e:
            print("error: ", e)
            break

    # 释放资源
    stream.stop_stream()
    stream.close()
    mic.terminate()
    return


        
