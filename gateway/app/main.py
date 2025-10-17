import json
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import StreamingResponse

from .config import Settings
from .logger import MyLogger
from .engine import call_asr, tts_stream_from_text


settings = Settings()
logger = MyLogger(
    settings.LOG_DIR,
    settings.LOG_FILE_INFO,
    settings.LOG_FILE_ERROR,
    settings.LOG_LEVEL,
)
app = FastAPI()


@app.websocket("/ws/tts")
async def ws_tts_proxy(ws: WebSocket):
    await ws.accept()
    logger.info(event="WS connection accepted")
    try:
        while True:
            data = await ws.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                logger.error(event="Invalid JSON")
                await ws.send_json({"Error": "Invalid JSON"})
                continue

            if "text" in payload.keys():
                texts = {"text": payload["text"]}
            elif "segments" in payload.keys() and isinstance(payload["segments"], list):
                texts = payload["segments"]
            else:
                logger.error(event="Wrong data format")
                await ws.send_json({"Error": "Wrong data format"})
                continue

            for text in texts:
                try:
                    async for chunk in tts_stream_from_text(
                        logger, settings.TTS_WS_URL, text, settings.REQUEST_TIMEOUT
                    ):
                        await ws.send_bytes(chunk)
                except Exception:
                    logger.error(event="TTS stream error")
                    await ws.send_json({"Error": "TTS stream error"})

    except WebSocketDisconnect:
        logger.error(event="Client websocket disconnected")
    except Exception as e:
        logger.error(event=f"WS error: {e}")
        try:
            await ws.close(code=1011)
        except Exception:
            pass


@app.post("/api/echo-bytes")
async def echo_bytes(request: Request):
    raw = await request.body()
    q = request.query_params
    try:
        sr = int(q.get("sr", 16000))
        ch = int(q.get("ch", 1))
        fmt = "pcm16"
    except Exception:
        logger.error(event="sr,ch required in query")
        raise HTTPException(status_code=400, detail="sr,ch required in query")

    if not raw:
        logger.error(event="Empty audio")
        raise HTTPException(status_code=400, detail="Empty audio")

    try:
        asr_resp = await call_asr(
            logger,
            f"http://asr:{settings.ASR_PORT}",
            raw,
            sr,
            ch,
            fmt,
            settings.REQUEST_TIMEOUT,
        )
    except Exception as e:
        logger.error(event=f"ASR error: {e}")
        raise HTTPException(status_code=502, detail="ASR error")

    has_segments = False
    segments = []

    if (
        "segments" in asr_resp
        and isinstance(asr_resp["segments"], list)
        and len(asr_resp["segments"]) > 0
    ):
        segments = asr_resp["segments"]
        has_segments = True
    elif "text" in asr_resp and asr_resp.get("text"):
        segments = [{"text": asr_resp["text"]}]
    else:
        logger.error(event="No transcription")
        raise HTTPException(status_code=204, detail="No transcription")

    async def streamer():
        try:
            for segment in segments:
                if not has_segments:
                    result = {"text": segment.get("text")}
                else:
                    result = segment
                if not result.get("text"):
                    continue
                async for chunk in tts_stream_from_text(
                    logger, settings.TTS_WS_URL, result, settings.REQUEST_TIMEOUT
                ):
                    yield chunk
        except asyncio.CancelledError:
            logger.info(event="Client disconnected during streaming")
            return
        except Exception as e:
            logger.error(event=f"TTS streaming error: {e}")
            return

    return StreamingResponse(streamer(), media_type="audio/L16")
