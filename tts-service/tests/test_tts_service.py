import pytest
import websockets
import json


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text, expect_error",
    [
        ("Hello world", False),
        ("", True),
        ("F" * 100, False),
    ]
)
async def test_tts_ws(input_text, expect_error):
    async with websockets.connect("ws://tts:8082/ws/tts") as websocket:
        await websocket.send(json.dumps({"text": input_text}))

        response = await websocket.recv()

        if expect_error:
            data = json.loads(response)
            assert "error" in data
        else:
            assert isinstance(response, (bytes, bytearray))
            assert len(response) > 0
