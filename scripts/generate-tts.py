#!/usr/bin/env python3
"""Pre-generate Arabic pronunciation audio for every glossary entry.

The page is static with no backend, so we can't call a paid TTS service at runtime
(no place to hide a key). Instead we snapshot the audio: this script reads a glossary
dictionary out of index.html and, for each word/expression, generates a small MP3 via
Microsoft's neural voices through edge-tts — free, keyless, the same voices Edge/Bing
"read aloud" uses. Files land in audio/, and a manifest maps each word to its file so
the 🔊 button can play it.

Two Arabic layers, each with its own voice, glossary and manifest:

    --lang ar   (default)  Moroccan Darija · GLOSS      · ar-MA-JamalNeural · audio/manifest.json
    --lang fus             Standard Arabic · GLOSS_FUS  · ar-SA-HamedNeural · audio/manifest-fus.json

Re-run after adding glossary entries (it skips files already generated), then commit
the new audio/ files:

    pip install edge-tts
    python3 scripts/generate-tts.py            # Darija
    python3 scripts/generate-tts.py --lang fus # Modern Standard Arabic
    git add audio && git commit -m "Regenerate TTS audio"

Override the voice with --voice <ShortName>.
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
CONCURRENCY = 8
# Numbers shown on the page: scores, stats, ranks (0-104) plus the tournament year.
NUMBERS = list(range(0, 105)) + [2026]

# Per-layer config: glossary object, spell-set, default voice, manifest, and slug prefix.
# The slug prefix keeps each layer's files distinct even when the two share a surface word.
LANGS = {
    "ar":  {"gloss": "GLOSS",     "spell": "SPELL_AR",  "voice": "ar-MA-JamalNeural",
            "manifest": "manifest.json",     "prefix": ""},
    "fus": {"gloss": "GLOSS_FUS", "spell": "SPELL_FUS", "voice": "ar-SA-HamedNeural",
            "manifest": "manifest-fus.json", "prefix": "fus:"},
}


def glossary_terms(obj):
    """Pull every key from the `const <obj> = { … }` object in index.html."""
    html = open(HTML, encoding="utf-8").read()
    block = re.search(r"const " + re.escape(obj) + r" = \{(.*?)\n  \};", html, re.S)
    if not block:
        sys.exit("Could not find the %s object in index.html." % obj)
    terms = re.findall(r'"([^"]+)":\s*\[', block.group(1))
    # keep only entries containing Arabic letters; de-dup, stable order
    seen, out = set(), []
    for t in terms:
        if re.search(r"[؀-ۿ]", t) and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def slug(prefix, key):
    return hashlib.sha1((prefix + key).encode("utf-8")).hexdigest()[:16] + ".mp3"


def number_readings(spell):
    """Reuse the page's OWN number speller so the audio matches the tooltip exactly:
    extract the number-speller block (between the <number-speller> markers) from
    index.html and run it in node with the chosen spell-set to get, for each number,
    its Arabic-Indic form (what the gloss shows) → spoken Arabic reading."""
    html = open(HTML, encoding="utf-8").read()
    block = re.search(r"// <number-speller>[^\n]*\n(.*?)\n[^\n]*// </number-speller>", html, re.S)
    if not block:
        print("  ! could not extract number speller — skipping number audio", file=sys.stderr)
        return {}
    js = block.group(1) + f"""
      const out = {{}};
      for (const n of {json.dumps(NUMBERS)}) {{ const g = numberGloss(String(n), {spell}); if (g) out[g.disp] = g.tip[2]; }}
      process.stdout.write(JSON.stringify(out));
    """
    try:
        res = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True)
        return json.loads(res.stdout)           # { "٢٠٢٦": "ألفان و ستة و عشرون", ... }
    except Exception as e:
        print(f"  ! number speller failed ({e}) — skipping number audio", file=sys.stderr)
        return {}


async def synth(prefix, key, text, voice, sem):
    """Generate audio of `text`; file is named for `key` (the manifest lookup key)."""
    path = os.path.join(OUT_DIR, slug(prefix, key))
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


async def main_async(cfg, voice):
    os.makedirs(OUT_DIR, exist_ok=True)
    prefix = cfg["prefix"]
    # (manifest key, text to speak): glossary words speak themselves; numbers speak their reading.
    items = [(t, t) for t in glossary_terms(cfg["gloss"])]
    nums = number_readings(cfg["spell"])
    items += [(disp, reading) for disp, reading in nums.items()]
    print(f"{len(items)} clips ({len(items) - len(nums)} words + {len(nums)} numbers) · voice {voice}")

    sem = asyncio.Semaphore(CONCURRENCY)
    results = await asyncio.gather(*(synth(prefix, k, txt, voice, sem) for k, txt in items))

    made = sum(1 for _, r in results if r is True)
    failed = [k for k, r in results if r is None]
    # manifest only references keys whose file actually exists
    manifest = {k: f"{OUT_DIR}/{slug(prefix, k)}" for k, _ in items
                if os.path.exists(os.path.join(OUT_DIR, slug(prefix, k)))}
    with open(os.path.join(OUT_DIR, cfg["manifest"]), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")

    print(f"generated {made} new · {len(manifest)} total in {cfg['manifest']}")
    if failed:
        print(f"  {len(failed)} failed (re-run to retry): {', '.join(failed[:8])}"
              + (" …" if len(failed) > 8 else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="ar", choices=list(LANGS))
    ap.add_argument("--voice", default=None, help="override the default voice for the chosen lang")
    args = ap.parse_args()
    cfg = LANGS[args.lang]
    asyncio.run(main_async(cfg, args.voice or cfg["voice"]))


if __name__ == "__main__":
    main()
