#!/usr/bin/env python3
"""Pre-generate a goal-celebration chant for every national team, in every UI language.

When a goal is scored in a live match, the page fires fireworks and plays a chant
naming the team that scored — in whichever language the reader picked (English /
Español / Darija). Same static-site reasoning as the Darija audio: no backend to call
a TTS service at runtime, so the clips are snapshotted here with edge-tts (free,
keyless), one upbeat voice per language. Files land in audio/goals/, keyed by language
then by team name in audio/goals.json (both the full and short ESPN names, run through
the same normaliser the page uses, so live-match names resolve).

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
CONCURRENCY = 8

# One chant per UI language: (voice, "Goal!" phrasing template, edge-tts prosody).
# The exclamation + voice carry the language; the team name stays as ESPN spells it.
LANGS = {
    "en": ("en-US-GuyNeural",   "Goal! {team}!",        {"rate": "+12%", "pitch": "+20Hz"}),
    "es": ("es-MX-JorgeNeural",  "¡Gooool! ¡{team}!", {"rate": "+10%", "pitch": "+15Hz"}),
    # Darija: گووول = "goool" (the page's goalLabel), then the team.
    "ar": ("ar-MA-JamalNeural",  "گووول! {team}!", {"rate": "+8%", "pitch": "+15Hz"}),
}

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


def slug(lang, team):
    return hashlib.sha1(f"{lang}|{team}".encode("utf-8")).hexdigest()[:16] + ".mp3"


def teams():
    raw = subprocess.run(["curl", "-s", STANDINGS], capture_output=True, text=True, check=True).stdout
    data = json.loads(raw)
    out = []
    for g in data.get("children", []):
        for e in (g.get("standings", {}) or {}).get("entries", []):
            t = e["team"]
            out.append((t.get("displayName"), t.get("shortDisplayName")))
    return out


async def synth(lang, display, sem):
    voice, template, prosody = LANGS[lang]
    path = os.path.join(OUT_DIR, slug(lang, display))
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return lang, display, False
    async with sem:
        try:
            await edge_tts.Communicate(template.format(team=display), voice, **prosody).save(path)
            return lang, display, True
        except Exception as e:
            print(f"  ! failed {lang} {display!r}: {e}", file=sys.stderr)
            if os.path.exists(path):
                os.remove(path)
            return lang, display, None


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ts = teams()
    print(f"{len(ts)} teams × {len(LANGS)} langs ({', '.join(LANGS)})")
    sem = asyncio.Semaphore(CONCURRENCY)
    await asyncio.gather(*(synth(lang, d, sem) for lang in LANGS for d, _ in ts))

    manifest = {lang: {} for lang in LANGS}
    for lang in LANGS:
        for display, short in ts:
            if not os.path.exists(os.path.join(OUT_DIR, slug(lang, display))):
                continue
            rel = f"{OUT_DIR}/{slug(lang, display)}"
            for name in (display, short):
                if name:
                    manifest[lang][norm(name)] = rel
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(f"{sum(len(v) for v in manifest.values())} name keys across {len(LANGS)} langs → {MANIFEST}")


if __name__ == "__main__":
    asyncio.run(main())
