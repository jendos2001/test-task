import numpy as np
import whisper
from scipy.signal import resample_poly

from .logger import MyLogger


class ASREngine:
    def __init__(self, model_name: str, logger: MyLogger):
        self.model_name = model_name
        self.logger = logger
        self.model = self._load()

    def _load(self):
        self.logger.info(event="ASR load start", model=self.model_name)
        model = whisper.load_model(self.model_name, device="cpu")
        self.logger.info(event="ASR load done", model=self.model_name)
        return model

    def transcribe_from_pcm(self, pcm_bytes: bytes, sample_rate: int, channels: int, lang: str = "en") -> dict:
        arr = np.frombuffer(pcm_bytes, dtype=np.int16)

        # Пробуем преобразовать в моно, если многоканальная
        if channels > 1:
            try:
                arr = arr.reshape(-1, channels)
                arr = arr.mean(axis=1).astype(np.int16)
            except Exception as e:
                self.logger.error(event="Failed to process multi-channel audio to mono-channel audio")
                raise

        audio = arr.astype(np.float32) / 32768.0

        # Преобразование частоты для модели, в whisper 16000
        if sample_rate != 16000:
            try:
                self.logger.info(event=f"Resampling from {sample_rate}Hz to 16000Hz")
                audio = resample_poly(audio, 16000, sample_rate)
                sample_rate = 16000
            except Exception as e:
                self.logger.error(event=f"Resampling from {sample_rate}Hz to 16000Hz failed")
                raise

        result = self.model.transcribe(audio, language=lang, fp16=False)
        
        if "segments" in result.keys():
            segments = result["segments"]
            out_text = [
                {
                    "start_ms": int(segment["start"] * 1000),
                    "end_ms": int(segment["end"] * 1000),
                    "text": segment["text"].strip(),
                }
                for segment in segments
            ]
            out = {"segments": out_text}
        else:
            out = {"text": result.get("text", "").strip()}
        return out
