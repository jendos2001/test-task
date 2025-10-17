import wave
import requests
import numpy as np
from scipy.signal import resample_poly

WAV_PATH = "input.wav"
OUT_PATH = "out_echo.wav"
URL = "http://localhost:8000/api/echo-bytes"

with wave.open(WAV_PATH, "rb") as wf:
    sr = wf.getframerate()
    ch = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    fmt = "pcm16"
    audio_bytes = wf.readframes(wf.getnframes())

params = {"sr": sr, "ch": ch, "lang": "en", "fmt": "s16le"}
resp = requests.post(URL, params=params, data=audio_bytes, stream=True)

if resp.status_code != 200:
    print(f"Error {resp.status_code}: {resp.text}")
    exit(1)

pcm_chunks = []
try:
    for i, chunk in enumerate(resp.iter_content(chunk_size=4096)):
        if chunk:
            if isinstance(chunk, bytes):
                if len(chunk) % 2 != 0:
                    chunk = chunk[:len(chunk) - (len(chunk) % 2)]
                pcm_chunks.append(np.frombuffer(chunk, dtype=np.int16))
                print(f"Received chunk {i}, {len(chunk)} bytes")
except requests.exceptions.ChunkedEncodingError as e:
    print(f"Chunked encoding error: {e}")

if not pcm_chunks:
    print("No audio received")
    exit(1)

pcm_tts = np.concatenate(pcm_chunks, axis=0)

if ch > 1:
    pcm_tts = pcm_tts.reshape(-1, ch)

pcm_final = resample_poly(pcm_tts, sr, 16000, axis=0).astype(np.int16)

with wave.open(OUT_PATH, "wb") as wf_out:
    wf_out.setnchannels(ch)
    wf_out.setsampwidth(sampwidth)
    wf_out.setframerate(sr)
    wf_out.writeframes(pcm_final.tobytes())

print(f"Output saved to: {OUT_PATH}")