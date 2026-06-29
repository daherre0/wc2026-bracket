#!/usr/bin/env python3
"""Pre-generate a goal-celebration chant for every national team.

When a goal is scored in a live match, the page fires fireworks and plays a chant
naming the team that scored. Same static-site reasoning as the Darija audio: no
backend to call a TTS service at runtime, so the clips are snapshotted here with
edge-tts (free, keyless) using an upbeat English voice. Files land in audio/goals/,
keyed by team name in audio/goals.json (both the full and short ESPN names, run
through the same normaliser the page uses, so live-match names resolve).

    pip install edge-tts
    python3 scripts/generate-goal-audio.py
    git add audio/goals audio/goals.json && git commit -m "Regenerate goal chants"
"""
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata

import edge_tts

STANDINGS = "https://site.api.espn.com/apis/v2/sports/soccer/fifa.world/standings?season=2026"
OUT_DIR = os.path.join("audio", "goals")
MANIFEST = os.path.join("audio", "goals.json")
VOICE = "en-US-GuyNeural"
CONCURRENCY = 8

# Mirror index.html's HL_ALIAS so cross-endpoint name variants collapse to one key.
ALIAS = {
    "korearepublic": "korea", "southkorea": "korea", "iriran": "iran",
    "czechrepublic": "czechia", "turkiye": "turkey", "drcongo": "congodr",
    "rdcongo": "congodr", "democraticrepublicofthecongo": "congodr",
    "cotedivoire": "ivorycoast", "caboverde": "capeverde",
    "bosniaandherzegovina": "bosnia", "bosniaherzegovina": "bosnia",
}


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    k = re.sub(r"[^a-z0-9]", "", s.lower())
    return ALIAS.get(k, k)


def slug(team):
    return hashlib.sha1(team.encode("utf-8")).hexdigest()[:16] + ".mp3"


def teams():
    raw = subprocess.run(["curl", "-s", STANDINGS], capture_output=True, text=True, check=True).stdout
    data = json.loads(raw)
    out = []
    for g in data.get("children", []):
        for e in (g.get("standings", {}) or {}).get("entries", []):
            t = e["team"]
            out.append((t.get("displayName"), t.get("shortDisplayName")))
    return out


async def synth(display, sem):
    path = os.path.join(OUT_DIR, slug(display))
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return display, False
    async with sem:
        try:
            await edge_tts.Communicate(f"Goal! {display}!", VOICE,
                                       rate="+12%", pitch="+20Hz").save(path)
            return display, True
        except Exception as e:
            print(f"  ! failed {display!r}: {e}", file=sys.stderr)
            if os.path.exists(path):
                os.remove(path)
            return display, None


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ts = teams()
    print(f"{len(ts)} teams · voice {VOICE}")
    sem = asyncio.Semaphore(CONCURRENCY)
    await asyncio.gather(*(synth(d, sem) for d, _ in ts))

    manifest = {}
    for display, short in ts:
        if not os.path.exists(os.path.join(OUT_DIR, slug(display))):
            continue
        rel = f"{OUT_DIR}/{slug(display)}"
        for name in (display, short):
            if name:
                manifest[norm(name)] = rel
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(f"{len(manifest)} name keys → {MANIFEST}")


if __name__ == "__main__":
    asyncio.run(main())
