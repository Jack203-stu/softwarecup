"""语音识别 + 语音合成"""
import os
os.environ["NO_PROXY"] = "*"
os.environ["MODELSCOPE_DISABLE_SSL"] = "1"
from funasr import AutoModel
import subprocess, os

class ASRService:
    def __init__(self):
        print("⏳ 加载 ASR...")
        # 强制 CPU，修复 CUDA 错误
        self.model = AutoModel(
            model="iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            device="cpu",  # 强制CPU
            disable_update=True
        )
        print("✅ ASR 就绪")
    
    def transcribe(self, audio_path):
        try:
            result = self.model.generate(input=audio_path)
            if result and len(result) > 0:
                return result[0].get('text', '')
            return ""
        except:
            return ""

class TTSService:
    def __init__(self):
        self.voice = "zh-CN-XiaoxiaoNeural"
        print("✅ Edge TTS 就绪 (Xiaoxiao)")
    
    def synthesize(self, text, output_path="output.wav"):
        try:
            subprocess.run([
                'edge-tts',
                '--voice', self.voice,
                '--text', text,
                '--write-media', output_path
            ], capture_output=True)
        except:
            pass