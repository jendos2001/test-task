import asyncio

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings
from .logger import MyLogger
from .engine import ASREngine


settings = Settings()
logger = MyLogger(settings.LOG_DIR, settings.LOG_FILE_INFO, settings.LOG_FILE_ERROR, settings.LOG_LEVEL)
asr_engine = ASREngine(settings.ASR_MODEL_NAME, logger)

app = FastAPI(title="asr-service", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/api/stt/bytes")
async def stt_bytes(
    request: Request,
    sample_rate: int = Query(..., description="Sample rate"),
    channels: int = Query(..., description="Channels"),
    lang: str = Query("en", description="Language (optional)"),
):
    try:
        body = await asyncio.wait_for(request.body(), timeout=settings.REQUEST_TIMEOUT)
    except asyncio.TimeoutError:
        logger.error(event="Request body read timeout")
        raise HTTPException(status_code=408, detail="Request body read timeout")

    if not body:
        logger.error(event="Request empty body")
        raise HTTPException(status_code=400, detail="Empty body")


    bytes_per_sample = 2
    total_samples = len(body) / (bytes_per_sample * max(1, channels))
    duration_s = total_samples / sample_rate
    if duration_s > settings.MAX_DUARTION:
        logger.error(event=f"Audio too long: {duration_s}s > {settings.MAX_DUARTION}s")
        raise HTTPException(status_code=413, detail=f"Audio too long: {duration_s:.2f}s > {settings.MAX_DUARTION}s")

    try:
        loop = asyncio.get_event_loop()
        coro = loop.run_in_executor(None, asr_engine.transcribe_from_pcm, body, sample_rate, channels, lang)
        res = await asyncio.wait_for(coro, timeout=settings.REQUEST_TIMEOUT)
    except asyncio.TimeoutError:
        logger.error(event="Transcription timeout")
        raise HTTPException(status_code=504, detail="Transcription timeout")
    except ValueError as e:
        logger.error(event="Invalid audio data")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(event="Internal server error")
        raise HTTPException(status_code=500, detail="Internal server error")


    return JSONResponse(content=res)


if __name__ == "__main__":
    import uvicorn

    logger.info(event="ASR server start", host=settings.HOST, port=settings.ASR_PORT)
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.ASR_PORT, log_level="info")
