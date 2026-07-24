#!/usr/bin/env python3
"""
Agnes AI 生成 Palworld 帕鲁配图
输入: scripts/data/legendary-pals.json
输出: public/images/{slug}.jpg
"""
import json, asyncio, pathlib, os, sys

AGNES_KEY = os.environ.get("AGNES_API_KEY")
AGNES_URL = "https://apihub.agnes-ai.com/v1/images/generations"
DATA_FILE = pathlib.Path(__file__).parent / "data" / "legendary-pals.json"
OUT_DIR = pathlib.Path(__file__).parent.parent / "public" / "images"

import aiohttp

async def generate_image(pal: dict) -> str:
    """Generate Pal artwork via Agnes"""
    prompt = (
        f"A majestic {pal['name']} from Palworld, "
        f"a legendary {'/'.join(pal.get('elements', ['Pal']))} type creature, "
        f"dramatic pose, game art style, high quality, "
        f"vibrant colors, epic fantasy creature design, "
        f"video game concept art, detailed"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            AGNES_URL,
            headers={
                "Authorization": f"Bearer {AGNES_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "agnes-image-2.1-flash",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
            },
            timeout=120,
        ) as resp:
            data = await resp.json()
            url = data.get("data", [{}])[0].get("url", "")
            return url


async def main():
    if not AGNES_KEY:
        print("❌ AGNES_API_KEY not set — skipping image generation")
        sys.exit(0)

    pals = json.loads(DATA_FILE.read_text())
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for pal in pals:
        slug = pal["slug"]
        print(f"  🎨 Generating: {pal['name']}...")
        try:
            url = await generate_image(pal)
            if url:
                print(f"     ✅ {url}")
                # Download image
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as r:
                        if r.status == 200:
                            ext = url.split(".")[-1].split("?")[0] or "jpg"
                            (OUT_DIR / f"{slug}.{ext}").write_bytes(await r.read())
                            print(f"     📁 Saved: public/images/{slug}.{ext}")
            else:
                print(f"     ⚠️  No URL returned")
        except Exception as e:
            print(f"     ❌ Failed: {e}")


asyncio.run(main())
