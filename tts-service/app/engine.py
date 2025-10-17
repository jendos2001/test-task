import asyncio
import numpy as np

from TTS.api import TTS

from .logger import MyLogger


class TTSEngine:
    def __init__(
        self, model_name: str, logger: MyLogger, sample_rate: int, chunk_ms: int
    ):
        self.model_name = model_name
        self.logger = logger
        self.chunk_ms = chunk_ms
        self.sample_rate = sample_rate
        self._tts = self._load()

    def _load(self):
        self.logger.info(event="TTS load start", model=self.model_name)
        model = TTS(self.model_name, gpu=False)
        self.logger.info(event="TTS load done", model=self.model_name)
        return model

    async def synthesize_sentences(self, text: str, timeout: int):
        sentences = [s.strip() for s in text.strip().split(".") if s.strip()]
        chunk_samples = int(self.sample_rate * (self.chunk_ms / 1000.0))

        for index, sentence in enumerate(sentences):
            try:
                coroutine = asyncio.to_thread(self._tts.tts, text=sentence)
                raw_audio = await asyncio.wait_for(coroutine, timeout=timeout)
                arr = np.asarray(raw_audio)
                arr = np.clip(arr, -1.0, 1.0)  # Убираем шумы
                values = (arr * (2**15 - 1)).astype(np.int16)
                total = len(values)
                pos = 0

                while pos < total:
                    end = pos + chunk_samples
                    chunk = values[pos:end]
                    if len(chunk) > 0:
                        yield chunk.tobytes()
                    pos = end

            except asyncio.TimeoutError:
                self.logger.error(
                    event="TTS generation timeout",
                    sentence_index=index,
                    sentence=sentence,
                )
            except Exception as exception:
                self.logger.error(
                    event="TTS generation error",
                    sentence_inedx=index,
                    error=str(exception),
                )
