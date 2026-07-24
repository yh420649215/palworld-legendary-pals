#!/usr/bin/env python3
"""
DeepSeek 批量生成英文攻略 — 输出纯 MDX (content collection 格式)
输入: scripts/data/legendary-pals.json
输出: src/content/pals/{slug}.md
"""
import json, os, pathlib, sys, asyncio, aiohttp

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")
DATA = pathlib.Path(__file__).parent / "data" / "legendary-pals.json"
OUT = pathlib.Path(__file__).parent.parent / "src" / "content" / "pals"

SYSTEM_PROMPT = """You write Palworld guide articles in plain markdown. No HTML wrappers, no code blocks around the output, no frontmatter (I'll add that separately). 

Style rules:
- Use ## for section headings (## Location & Spawn, ## How to Catch, etc.)
- Short sentences mixed with longer ones. Read like a gamer wrote it, not a wiki bot.
- Never use: additionally, moreover, furthermore, consequently, it is noteworthy, serves as, stands as, nestled, underscores, highlights the significance.
- Use plain words. "is" not "serves as". "has" not "boasts".
- Be specific with coordinates, spawn times, level requirements. Use the data I provide, do not invent.
- Include practical gameplay tips at the end.
- Do NOT add "Data source" or "Data sourced from" lines anywhere.

Format: pure markdown only. Start with ## immediately."""

TEMPLATE = """Write a Palworld 1.0 guide for {name}.

Game data:
- Paldeck No: {no}
- Element: {elements}
- Drops: {drops}
- Partner Skill: {partner_skill}
- Ride Speed: {ride_speed}
- Stamina: {stamina}
- Food Level: {food}
- Breeding Power: {breed_power}

Location & Availability:
{availability}

Stats:
{stats}

Drops data:
{drops_section}

Sections (use ## headings):
## Location & Spawn
## How to Catch
## Stats
## Drops
## Partner Skill
## Tips & Strategy

Be specific. Use exact coordinates from the availability data. Include the 1.0 map location (Sunreach, Mount Obsidian, etc) and spawn conditions."""


def clean_name(name: str) -> str:
    return name.replace("_", " ")


def build_user_prompt(pal: dict) -> str:
    stats_lines = [f"- {k.capitalize()}: {v}" for k, v in pal.items()
                   if k in ("hp", "attack", "defense")]
    return TEMPLATE.format(
        name=clean_name(pal["name"]),
        no=pal.get("no", "?"),
        elements=" / ".join(pal.get("elements", ["?"])),
        drops=pal.get("drops_raw", "Unknown"),
        partner_skill=pal.get("partner_skill", "Unknown"),
        ride_speed=pal.get("ride_speed", "?"),
        stamina=pal.get("stamina", "?"),
        food=pal.get("food", "?"),
        breed_power=pal.get("breed_power", "?"),
        availability=pal.get("availability", "No location data"),
        stats="\n".join(stats_lines) if stats_lines else "No stats available",
        drops_section=pal.get("drops_section", ""),
    )


def frontmatter(pal: dict) -> str:
    fm = f"""---
name: {clean_name(pal["name"])}
type: {" / ".join(pal.get("elements", ["?"]))}
level: 50
no: "{pal.get("no", "")}"
"""
    for k in ("hp", "attack", "defense"):
        if k in pal:
            fm += f"{k}: {pal[k]}\n"
    fm += "---\n\n"
    return fm


async def generate(pal: dict) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(pal)},
                ],
                "temperature": 0.7,
                "max_tokens": 3000,
            },
            timeout=60,
        ) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]


async def main():
    if not DEEPSEEK_KEY:
        print("❌ DEEPSEEK_API_KEY not set")
        return

    pals = json.loads(DATA.read_text())
    print(f"📦 Loaded {len(pals)} pals")

    OUT.mkdir(parents=True, exist_ok=True)
    for pal in pals:
        slug = pal["slug"]
        out_path = OUT / f"{slug}.md"
        print(f"  Generating: {pal['name']}...")

        try:
            content = await generate(pal)
            # Clean fences
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                lines = [l for l in lines if not l.startswith("```")]
                content = "\n".join(lines)

            # No footer — Layout already adds data source note
            out_path.write_text(frontmatter(pal) + content, encoding="utf-8")
            print(f"     {len(content)} chars -> {out_path}")

        except Exception as e:
            print(f"     ❌ Failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
