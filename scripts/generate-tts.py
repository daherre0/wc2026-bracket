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
import sys

import edge_tts

HTML = "index.html"
OUT_DIR = "audio"
MANIFEST = os.path.join(OUT_DIR, "manifest.json")
DEFAULT_VOICE = "ar-MA-JamalNeural"
CONCURRENCY = 8


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


def slug(term):
    return hashlib.sha1(term.encode("utf-8")).hexdigest()[:16] + ".mp3"


async def synth(term, voice, sem):
    path = os.path.join(OUT_DIR, slug(term))
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return term, False
    async with sem:
        try:
            await edge_tts.Communicate(term, voice).save(path)
            return term, True
        except Exception as e:                       # network blip / transient endpoint error
            print(f"  ! failed {term!r}: {e}", file=sys.stderr)
            if os.path.exists(path):
                os.remove(path)
            return term, None


async def main_async(voice):
    os.makedirs(OUT_DIR, exist_ok=True)
    terms = glossary_terms()
    print(f"{len(terms)} glossary terms · voice {voice}")
    sem = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(*(synth(t, voice, sem) for t in terms))

    made = sum(1 for _, r in results if r is True)
    failed = [t for t, r in results if r is None]
    # manifest only references terms whose file actually exists
    manifest = {t: f"{OUT_DIR}/{slug(t)}" for t in terms
                if os.path.exists(os.path.join(OUT_DIR, slug(t)))}
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
