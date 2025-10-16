import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .logger import MyLogger
from .engine import TTSEngine

settings = Settings()
logger = MyLogger(settings.LOG_DIR, settings.LOG_FILE_INFO, settings.LOG_FILE_ERROR, settings.LOG_LEVEL)
tts_engine = TTSEngine(settings.TTS_MODEL_NAME, logger, settings.SAMPLE_RATE, settings.CHUNK_MS)


app = FastAPI(title="tts-service", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.websocket(settings.WS_PATH)
async def websocket_tts(ws: WebSocket):
    await ws.accept()
    logger.info(event="WebSocket connected", path=settings.WS_PATH)
    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=settings.RECIEVE_TIMEOUT)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await ws.send_text(json.dumps({"error": "Invalid data"}))
            logger.error(event="Invalid data")
            await ws.close(code=1003) # Unsupported Data
            logger.info(event="WebSocket closed", path=settings.WS_PATH)
            return

        text = payload.get("text")
        if not text or not text.strip():
            await ws.send_text(json.dumps({"error": "empty text"}))
            logger.error(event="Empty input text")
            await ws.close(code=1003)
            logger.info(event="WebSocket closed", path=settings.WS_PATH)
            return

        try:
            async for chunk in tts_engine.synthesize_sentences(text, settings.GENERATION_TIMEOUT):
                await ws.send_bytes(chunk)
            await ws.send_text(json.dumps({"type": "end"})) # Завершаем стрим
            logger.info(event="Stream complete")
        except asyncio.TimeoutError:
            await ws.send_text(json.dumps({"error": "Generation timeout"}))
            logger.error(event="Generation timeout")
            await ws.close(code=1011)
            logger.info(event="WebSocket closed", path=settings.WS_PATH)

        except Exception as exception:
            await ws.send_text(json.dumps({"error": "Generation error"}))
            logger.error(event="Generation error", error=str(exception))
            await ws.close(code=1011)
            logger.info(event="WebSocket closed", path=settings.WS_PATH)

    except WebSocketDisconnect:
        logger.info(event="Client disconnect")
    except asyncio.TimeoutError:
        await ws.send_text(json.dumps({"error": "Server timeout"}))
        logger.error(event="Server timeout")
        await ws.close(code=1011)
        logger.info(event="WebSocket closed", path=settings.WS_PATH)
    except Exception as exception:
        logger.error(event="WebSocket exception", error=str(exception))
        await ws.close(code=1011)
        logger.info(event="WebSocket closed", path=settings.WS_PATH)


if __name__ == "__main__":
    import uvicorn

    logger.info(event="TTS server start", host=settings.HOST, port=settings.TTS_PORT, ws_path=settings.WS_PATH)
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.TTS_PORT, log_level="info")
