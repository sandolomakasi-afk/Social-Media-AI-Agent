@app.post("/generate-video")
async def generate_video(req: VideoRequest):
    # Audio save
    audio_data = base64.b64decode(req.audio_base64)
    with open("/tmp/voice.mp3", "wb") as f:
        f.write(audio_data)

    # Pexels မှ COPYRIGHT-FREE video ရယူ
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={
                "query": req.keyword,
                "per_page": 5,
                "orientation": "landscape"
            }
        )
    videos = res.json()["videos"]
    # Random video ရွေး → same video မဖြစ်အောင်
    import random
    chosen = random.choice(videos)
    video_url = chosen["video_files"][0]["link"]

    # Download
    async with httpx.AsyncClient(timeout=60) as client:
        vid = await client.get(video_url)
    with open("/tmp/stock.mp4", "wb") as f:
        f.write(vid.content)

    # Text overlay ထည့် (hook text)
    hook_text = req.hook_text.replace("'", "\\'")
    
    # FFmpeg: video + audio + text overlay
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "/tmp/stock.mp4",
        "-i", "/tmp/voice.mp3",
        "-vf", f"drawtext=text='{hook_text}':fontcolor=white:fontsize=48:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-100",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        "/tmp/final.mp4"
    ])

    with open("/tmp/final.mp4", "rb") as f:
        video_b64 = base64.b64encode(f.read()).decode()
    return {"video_base64": video_b64}
