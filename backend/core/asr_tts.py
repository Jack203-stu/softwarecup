"""语音识别 + 语音合成（稳定版）"""
from funasr import AutoModel
import subprocess, os

class ASRService:
    def __init__(self):
        print("[*] Loading ASR...")
        self.model = AutoModel(
            model="iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            device="cpu", disable_update=True
        )
        print("[OK] ASR ready")
    
    def transcribe(self, audio_path):
        try:
            result = self.model.generate(input=audio_path)
            return result[0].get('text', '') if result else ""
        except:
            return ""

class TTSService:
    def __init__(self):
        self.voice = "zh-CN-XiaoxiaoNeural"
        self.cache = {}
        print("[OK] Edge TTS ready (Xiaoxiao)")
    
    def synthesize(self, text, output_path="output.wav", voice=None):
        actual_voice = voice or self.voice
        cache_key = f"{text}_{actual_voice}"
        
        if cache_key in self.cache:
            cached_path = self.cache[cache_key]
            if os.path.exists(cached_path):
                import shutil
                shutil.copy2(cached_path, output_path)
                return output_path
        
        if not os.path.isabs(output_path):
            output_path = os.path.join(os.getcwd(), output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            subprocess.run([
                'edge-tts',
                '--voice', actual_voice,
                '--text', text,
                '--write-media', output_path
            ], check=True, capture_output=True)
            
            self.cache[cache_key] = output_path
            
        except Exception as e:
            print(f"⚠️ Edge TTS 失败: {e}")
            import wave, struct
            with wave.open(output_path, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(struct.pack('<h', 0) * 16000)
        
        return output_path
