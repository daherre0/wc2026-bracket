#!/usr/bin/env python3
"""Pre-generate Darija pronunciation audio for every glossary entry.

The page is static with no backend, so we can't call a paid TTS service at runtime
(no place to hide a key). Instead we snapshot the audio: this script reads the GLOSS
dictionary out of index.html and, for each Darija word/expression, generates a small
MP3 with Microsoft's Moroccan-Arabic neural voice (ar-MA-JamalNeural) via edge-tts —
free, keyless, the same voice Edge/Bing "read aloud" uses. Files land in audio/, and
audio/manifest.json maps each word to its file so the 🔊 button can play it.

Re-run after adding glossary entries (it skips files already generated), then commit
the new audio/ files:

    pip install edge-tts
    python3 scripts/generate-tts.py
    git add audio && git commit -m "Regenerate Darija TTS audio"

Switch voice with --voice ar-MA-MounaNeural (female).
"""
import argparse
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys

import edge_tts

HTML = "index.html"
OUT_DIR = "audio"
MANIFEST = os.path.join(OUT_DIR, "manifest.json")
DEFAULT_VOICE = "ar-MA-JamalNeural"
CONCURRENCY = 8
# Numbers shown on the page: scores, stats, ranks (0-104) plus the tournament year.
NUMBERS = list(range(0, 105)) + [2026]


def glossary_terms():
    """Pull every key from the `const GLOSS = { … }` object in index.html."""
    html = open(HTML, encoding="utf-8").read()
    block = re.search(r"const GLOSS = \{(.*?)\n  \};", html, re.S)
    if not block:
        sys.exit("Could not find the GLOSS object in index.html.")
    terms = re.findall(r'"([^"]+)":\s*\[', block.group(1))
    # keep only entries containing Arabic letters; de-dup, stable order
    seen, out = set(), []
    for t in terms:
        if re.search(r"[؀-ۿ]", t) and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def slug(key):
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16] + ".mp3"


def number_readings():
    """Reuse the page's OWN number speller so the audio matches the tooltip exactly:
    extract the Darija number code from index.html and run it in node to get, for each
    number, its Arabic-Indic form (what the gloss shows) → spoken Arabic reading."""
    html = open(HTML, encoding="utf-8").read()
    block = re.search(r"const N_ZERO.*?function numberGloss\(raw\) \{.*?\n  \}", html, re.S)
    if not block:
        print("  ! could not extract number speller — skipping number audio", file=sys.stderr)
        return {}
    js = block.group(0) + f"""
      const out = {{}};
      for (const n of {json.dumps(NUMBERS)}) {{ const g = numberGloss(String(n)); if (g) out[g.disp] = g.tip[2]; }}
      process.stdout.write(JSON.stringify(out));
    """
    try:
        res = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True)
        return json.loads(res.stdout)           # { "٢٠٢٦": "ألفين و ستة و عشرين", ... }
    except Exception as e:
        print(f"  ! number speller failed ({e}) — skipping number audio", file=sys.stderr)
        return {}


async def synth(key, text, voice, sem):
    """Generate audio of `text`; file is named for `key` (the manifest lookup key)."""
    path = os.path.join(OUT_DIR, slug(key))
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return key, False
    async with sem:
        try:
            await edge_tts.Communicate(text, voice).save(path)
            return key, True
        except Exception as e:                       # network blip / transient endpoint error
            print(f"  ! failed {key!r}: {e}", file=sys.stderr)
            if os.path.exists(path):
                os.remove(path)
            return key, None


async def main_async(voice):
    os.makedirs(OUT_DIR, exist_ok=True)
    # (manifest key, text to speak): glossary words speak themselves; numbers speak their reading.
    items = [(t, t) for t in glossary_terms()]
    nums = number_readings()
    items += [(disp, reading) for disp, reading in nums.items()]
    print(f"{len(items)} clips ({len(items) - len(nums)} words + {len(nums)} numbers) · voice {voice}")

    sem = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(*(synth(k, txt, voice, sem) for k, txt in items))

    made = sum(1 for _, r in results if r is True)
    failed = [k for k, r in results if r is None]
    # manifest only references keys whose file actually exists
    manifest = {k: f"{OUT_DIR}/{slug(k)}" for k, _ in items
                if os.path.exists(os.path.join(OUT_DIR, slug(k)))}
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")

    print(f"generated {made} new · {len(manifest)} total in manifest")
    if failed:
        print(f"  {len(failed)} failed (re-run to retry): {', '.join(failed[:8])}"
              + (" …" if len(failed) > 8 else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    asyncio.run(main_async(ap.parse_args().voice))


if __name__ == "__main__":
    main()
