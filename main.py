from fastapi import FastAPI
from pydantic import BaseModel
import edge_tts
import asyncio
import base64

app = FastAPI()

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"

@app.post("/tts")
async def generate_tts(req: TTSRequest):
    filename = "/tmp/output.mp3"
    communicate = edge_tts.Communicate(req.text, req.voice)
    await communicate.save(filename)
    with open(filename, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()
    return {"audio_base64": audio_b64}
