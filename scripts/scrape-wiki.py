#!/usr/bin/env python3
"""
Wiki Raw 数据抓取脚本
通过用户 Chrome CDP (端口 9222) 抓取 6 只 Legendary Pal 的 wikitext 数据
输出: scripts/data/legendary-pals.json
"""
import asyncio, json, re, sys
from pathlib import Path
sys.path.insert(0, r"C:\Users\yh\AppData\Local\hermes\skills\browser-use-init\scripts")
from playwright_connect import get_page

LEGENDARY_PALS = [
    "Jetragon",
    "Frostallion",
    "Frostallion_Noct",
    "Paladius",
    "Necromus",
    "Neptilius",
]

WIKI_BASE = "https://palworld.fandom.com/wiki"
OUTPUT = Path(__file__).parent / "data" / "legendary-pals.json"


def parse_pal_template(raw: str) -> dict:
    """解析 {{Pal|...}} 模板"""
    data = {}
    # 提取 Pal 模板
    m = re.search(r'\{\{Pal\s*\n(.+?)\}\}', raw, re.DOTALL)
    if m:
        for line in m.group(1).split('\n'):
            kv = re.match(r'\|\s*(\w+)\s*=\s*(.+)', line.strip())
            if kv:
                data[kv.group(1).strip()] = kv.group(2).strip()

    # 提取 Stats 模板
    m2 = re.search(r'\{\{Pal Table Stats\s*\n(.+?)\}\}', raw, re.DOTALL)
    if m2:
        for line in m2.group(1).split('\n'):
            kv = re.match(r'\|\s*(\w+)\s*=\s*(.+)', line.strip())
            if kv:
                data[kv.group(1).strip()] = kv.group(2).strip()

    return data


def parse_availability(raw: str) -> str:
    """提取 == Availability == 章节的完整文本"""
    m = re.search(r'== Availability ==\n(.+?)(?:\n==|\Z)', raw, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_drops(raw: str) -> str:
    m = re.search(r'== Drops ==\n(.+?)(?:\n==|\Z)', raw, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_partner_skill(raw: str) -> str:
    m = re.search(r'== Partner Skill ==\n(.+?)(?:\n==|\Z)', raw, re.DOTALL)
    return m.group(1).strip() if m else ""


async def main():
    pw, browser, page = await get_page()
    results = []

    for pal_name in LEGENDARY_PALS:
        url = f"{WIKI_BASE}/{pal_name}?action=raw"
        print(f"📥 Fetching: {pal_name}...")

        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)

        raw = await page.evaluate("() => document.body.innerText")

        if len(raw) < 100:
            print(f"  ⚠️  Too short ({len(raw)} chars) — Cloudflare block?")
            continue

        parsed = parse_pal_template(raw)
        availability = parse_availability(raw)
        drops = parse_drops(raw)
        partner_skill = parse_partner_skill(raw)

        # Extract stats if present
        stats = {}
        for key in ("hp", "attack", "defense"):
            if key in parsed:
                stats[key] = parsed[key]

        result = {
            "name": pal_name.replace("_", " "),
            "slug": pal_name.lower().replace("_", "-"),
            "no": parsed.get("no", ""),
            "elements": [v for k, v in parsed.items() if k.startswith("ele")],
            "drops_raw": parsed.get("drops", ""),
            "partner_skill": parsed.get("partnerskill", ""),
            "ride_speed": parsed.get("ridespeed", ""),
            "stamina": parsed.get("stamina", ""),
            "food": parsed.get("food", ""),
            "breed_power": parsed.get("breedpower", ""),
            **stats,
            "availability": availability,
            "drops_section": drops,
            "partner_skill_section": partner_skill,
            "raw_length": len(raw),
        }
        results.append(result)
        print(f"  ✅ {len(raw)} chars, parsed {len(parsed)} fields")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n✅ Saved {len(results)} pals to {OUTPUT}")

    await pw.stop()

asyncio.run(main())
