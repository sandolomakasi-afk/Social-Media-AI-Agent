from fastapi import FastAPI
from pydantic import BaseModel
import edge_tts
import asyncio
import base64
import httpx
import subprocess
import os
import random

app = FastAPI()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"

class VideoRequest(BaseModel):
    story_script: str
    audio_base64: str
    keyword: str = "betrayal drama revenge"
    hook_text: str = "You won't believe what happened..."

@app.post("/tts")
async def generate_tts(req: TTSRequest):
    filename = "/tmp/output.mp3"
    communicate = edge_tts.Communicate(req.text, req.voice)
    await communicate.save(filename)
    with open(filename, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()
    return {"audio_base64": audio_b64}

@app.post("/generate-video")
async def generate_video(req: VideoRequest):
    # 1. Audio save
    audio_data = base64.b64decode(req.audio_base64)
    with open("/tmp/voice.mp3", "wb") as f:
        f.write(audio_data)

    # 2. Pexels မှ random copyright-free video
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": req.keyword, "per_page": 5, "orientation": "landscape"}
        )
    videos = res.json()["videos"]
    chosen = random.choice(videos)
    video_url = chosen["video_files"][0]["link"]

    # 3. Video download
    async with httpx.AsyncClient(timeout=60) as client:
        vid = await client.get(video_url)
    with open("/tmp/stock.mp4", "wb") as f:
        f.write(vid.content)

    # 4. Text overlay + audio merge
    safe_text = req.hook_text.replace("'", "").replace('"', '')
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "/tmp/stock.mp4",
        "-i", "/tmp/voice.mp3",
        "-vf", f"drawtext=text='{safe_text}':fontcolor=white:fontsize=40:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-80",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "/tmp/final.mp4"
    ])

    # 5. Base64 ပြန်ပို့
    with open("/tmp/final.mp4", "rb") as f:
        video_b64 = base64.b64encode(f.read()).decode()
    return {"video_base64": video_b64}
