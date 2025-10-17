import asyncio
import websockets
import wave
import time
import json


async def stream_tts():
    uri = "ws://localhost:8000/ws/tts"
    text = {"text": "Hello! My name is Evgeny."}

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(text))
        print(f"Отправлено: {json.dumps(text)}")

        with wave.open("out.wav", "wb") as wf:
            wf.setnchannels(1)      
            wf.setsampwidth(2)     
            wf.setframerate(16000) 

            start_time = time.time()
            while True:
                try:
                    frame = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    if isinstance(frame, bytes):
                        wf.writeframes(frame)
                        elapsed = time.time() - start_time
                        print(f"[{elapsed:.8f}s] Получен фрейм: {len(frame)} байт")
                        start_time = time.time()
                except websockets.ConnectionClosed:
                    print("Соединение закрыто сервером")
                    break
                except TimeoutError:
                    print("Стрим закончен")
                    break

if __name__ == "__main__":
    asyncio.run(stream_tts())