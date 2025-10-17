import asyncio
import aiohttp
import json
from .logger import MyLogger


async def call_asr(logger: MyLogger, asr_url: str, audio_bytes: bytes, sr: int, ch: int, fmt: str, timeout: int):
    url = f"{asr_url.rstrip('/')}/api/stt/bytes"
    params = {
        "sr": sr,
        "ch": ch,
        "fmt": fmt,
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as sess:
            async with sess.post(url, params=params, data=audio_bytes, 
                                 headers={"Content-Type": "application/octet-stream"}) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(event=f"Status {resp.status} {text}")
                    raise aiohttp.ClientResponseError(
                        resp.request_info, resp.history, status=resp.status, message=text
                    )
                return await resp.json()
    except asyncio.TimeoutError:
        logger.error(event="ASR request timeout")
        raise

async def tts_stream_from_text(logger: MyLogger, tts_ws_url:str, text: dict, timeout: int):
    url = tts_ws_url
    logger.info(event=f"Connecting to TTS {url} for text: {text}")
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None)) as sess:
            async with sess.ws_connect(url, timeout=timeout) as ws:
                await ws.send_json(text)

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        yield msg.data

                    elif msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            payload = json.loads(msg.data)
                            evt = payload.get("type")
                            if evt == "end":
                                logger.info(event=f"TTS end signal received")
                                break
                        except Exception:
                            logger.info(event=f"TTS text error")

                    elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                        logger.info(event=f"TTS WS closed or error ({msg.type})")
                        break

                await ws.close()

    except asyncio.TimeoutError:
        logger.error(event="TTS websocket timeout")
    except Exception:
        logger.error(event=f"TTS websocket error")
    finally:
        logger.info(event="TTS stream finished")
