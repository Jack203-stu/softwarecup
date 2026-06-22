"""语音识别 + 语音合成（量化加速 + 可选 SenseVoice）"""
import hashlib
import os
import shutil
import subprocess

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'tts_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

_ASR_MODEL_PRESETS = {
    "paraformer-large": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    "paraformer": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
}

def _build_asr():
    from funasr import AutoModel
    model_preset = os.getenv("ASR_MODEL", "paraformer-large")
    model_name = _ASR_MODEL_PRESETS.get(model_preset, _ASR_MODEL_PRESETS["paraformer-large"])
    extra = {"quantize": True}
    try:
        import onnxruntime  # noqa: F401
        extra["backend"] = "onnxruntime"
        print("[*] ASR backend=onnxruntime quantize=on")
    except ImportError:
        print("[*] ASR backend=torch quantize=on (pip install onnxruntime for faster decode)")
    print(f"[*] Loading ASR model={model_preset} ({model_name})...")
    return AutoModel(model=model_name, device="cpu", disable_update=True, **extra)


class ASRService:
    def __init__(self):
        self.model = _build_asr()
        self._mode = os.getenv("ASR_MODEL", "paraformer")
        print(f"[OK] ASR ready (mode={self._mode})")

    def transcribe(self, audio_path):
        try:
            if self._mode == "sensevoice":
                res = self.model.generate(input=audio_path, language="zh", use_itn=True)
            else:
                res = self.model.generate(input=audio_path)
            return res[0].get('text', '') if res else ""
        except Exception as e:
            print(f"[ASR] transcribe err: {e}")
            return ""


class TTSService:
    def __init__(self):
        self.voice = "zh-CN-XiaoxiaoNeural"
        self._mem_cache = {}
        print("[OK] Edge TTS ready (Xiaoxiao, cache dir: " + CACHE_DIR + ")")

    def _cache_path(self, text, voice):
        h = hashlib.md5(f"{voice}|{text}".encode("utf-8")).hexdigest()
        return os.path.join(CACHE_DIR, f"{h}.wav")

    def synthesize(self, text, output_path="output.wav", voice=None):
        actual_voice = voice or self.voice
        cache_file = self._cache_path(text, actual_voice)

        if os.path.exists(cache_file):
            if not os.path.isabs(output_path):
                output_path = os.path.join(os.getcwd(), output_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            shutil.copy2(cache_file, output_path)
            self._mem_cache[f"{text}_{actual_voice}"] = cache_file
            return output_path

        if f"{text}_{actual_voice}" in self._mem_cache:
            cached_path = self._mem_cache[f"{text}_{actual_voice}"]
            if os.path.exists(cached_path):
                if not os.path.isabs(output_path):
                    output_path = os.path.join(os.getcwd(), output_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
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
                '--write-media', cache_file,
            ], check=True, capture_output=True, timeout=20)

            shutil.copy2(cache_file, output_path)
            self._mem_cache[f"{text}_{actual_voice}"] = cache_file

        except Exception as e:
            print(f"TTS fail, fallback silence: {e}")
            import wave, struct
            with wave.open(output_path, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(struct.pack('<h', 0) * 32000)

        return output_path
