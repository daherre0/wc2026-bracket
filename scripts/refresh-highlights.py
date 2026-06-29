#!/usr/bin/env python3
"""Regenerate highlights.json from FIFA's official YouTube highlights playlist.

The site is a single static page with no backend, so match-highlight links can't
be discovered live in the browser (YouTube's HTML is JS-rendered and scraping it
client-side is brittle + against their ToS). Instead we snapshot the playlist here
and commit the result. Re-run after each match day and commit highlights.json:

    python3 scripts/refresh-highlights.py
    git add highlights.json && git commit -m "Refresh match highlights"

It needs only curl + python3 (no API key). The playlist is FIFA's own channel:
https://www.youtube.com/playlist?list=PLBRLtDhTHh5o
"""
import json
import re
import subprocess
import sys
import unicodedata

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLBRLtDhTHh5o"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
OUT = "highlights.json"
MANUAL = "highlights-manual.json"   # hand-added videos for matches FIFA hasn't posted (e.g. DSports)

# FIFA highlight titles arrive mostly in Spanish (a few in English). Normalise every
# team to the English name ESPN uses, so the site reads consistently in any language.
TEAMS = {
    "argelia": "Algeria", "austria": "Austria", "jordania": "Jordan",
    "argentina": "Argentina", "colombia": "Colombia", "portugal": "Portugal",
    "rd del congo": "Congo DR", "rd congo": "Congo DR", "rdc": "Congo DR",
    "uzbekistan": "Uzbekistan", "croacia": "Croatia", "ghana": "Ghana",
    "panama": "Panama", "inglaterra": "England", "egipto": "Egypt",
    "ri iran": "IR Iran", "iran": "IR Iran", "nueva zelanda": "New Zealand",
    "belgica": "Belgium", "cabo verde": "Cape Verde", "arabia saudita": "Saudi Arabia",
    "new zealand": "New Zealand", "egypt": "Egypt",
    "uruguay": "Uruguay", "espana": "Spain", "senegal": "Senegal", "irak": "Iraq",
    "iraq": "Iraq", "noruega": "Norway", "norway": "Norway", "francia": "France",
    "france": "France", "turkiye": "Türkiye", "turquia": "Türkiye",
    "ee. uu.": "United States", "ee.uu.": "United States", "usa": "United States",
    "paraguay": "Paraguay", "australia": "Australia", "japon": "Japan",
    "suecia": "Sweden", "tunez": "Tunisia", "paises bajos": "Netherlands",
    "curazao": "Curaçao", "costa de marfil": "Ivory Coast", "ecuador": "Ecuador",
    "alemania": "Germany", "sudafrica": "South Africa",
    "republica de corea": "Korea Republic", "corea": "Korea Republic",
    "chequia": "Czechia", "czechia": "Czechia", "mexico": "Mexico",
    "marruecos": "Morocco", "haiti": "Haiti", "escocia": "Scotland",
    "brasil": "Brazil", "bosnia y herzegovina": "Bosnia-Herzegovina",
    "catar": "Qatar", "suiza": "Switzerland", "canada": "Canada",
    # already-English names that appear verbatim in some titles
    "korea republic": "Korea Republic", "mexico ": "Mexico",
}

SCORE_RE = re.compile(r"^\s*(.+?)\s+(\d+)\s*-\s*(\d+)\s+(.+?)\s*$")


def strip(s):
    """lowercase + drop accents, for tolerant team-name lookup."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def team(name):
    key = strip(name)
    if key in TEAMS:
        return TEAMS[key]
    print(f"  ! unknown team {name!r} — left as-is (add it to TEAMS)", file=sys.stderr)
    return name.strip()


def fetch_html():
    return subprocess.run(
        ["curl", "-sL", "-A", UA, PLAYLIST_URL],
        capture_output=True, text=True, check=True,
    ).stdout


def parse(html):
    m = re.search(r"ytInitialData\s*=\s*(\{.*?\});</script>", html, re.S)
    if not m:
        sys.exit("Could not find ytInitialData — YouTube markup may have changed.")
    data = json.loads(m.group(1))

    lockups = []

    def walk(o):
        if isinstance(o, dict):
            if "lockupViewModel" in o:
                lockups.append(o["lockupViewModel"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(data)

    out, skipped = [], 0
    for lv in lockups:
        vid = lv.get("contentId")
        title = (lv.get("metadata", {})
                   .get("lockupMetadataViewModel", {})
                   .get("title", {}).get("content", "")) or ""
        # the score "Team A X-Y Team B" lives in one of the pipe-separated segments
        seg = next((s for s in title.split("|") if SCORE_RE.match(s)), None)
        sm = SCORE_RE.match(seg) if seg else None
        if not (vid and sm):
            skipped += 1
            continue
        out.append({
            "home": team(sm.group(1)),
            "away": team(sm.group(4)),
            "hs": int(sm.group(2)),
            "as": int(sm.group(3)),
            "videoId": vid,
            "title": title.strip(),
        })
    if skipped:
        print(f"  (skipped {skipped} entries with no parseable score)", file=sys.stderr)
    return out


def pair_key(m):
    return tuple(sorted((strip(m["home"]), strip(m["away"]))))


def merge_manual(matches):
    """Add hand-curated entries (highlights-manual.json) for matches the FIFA playlist
    doesn't carry yet. FIFA's own entry always wins, so once it posts an embeddable
    version the manual one is dropped automatically — no cleanup needed."""
    try:
        with open(MANUAL, encoding="utf-8") as f:
            manual = json.load(f)
    except FileNotFoundError:
        return matches
    have = {pair_key(m) for m in matches}
    added = 0
    for m in manual:
        if pair_key(m) in have:
            print(f"  · skip manual {m['home']} v {m['away']} — already in FIFA playlist")
            continue
        matches.append(m)
        added += 1
    if added:
        print(f"  + merged {added} manual entr{'y' if added == 1 else 'ies'} from {MANUAL}")
    return matches


def main():
    print("Fetching playlist…")
    matches = merge_manual(parse(fetch_html()))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"Wrote {len(matches)} matches → {OUT}")


if __name__ == "__main__":
    main()
