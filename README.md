# World Cup 2026 — Live Bracket & Standings

**🔗 Live app: https://daherre0.github.io/wc2026-bracket/**

A single, self-contained static page (one `index.html`, no backend) that follows the
FIFA World Cup 2026 live: the full knockout bracket plus the third-place standings.

## Features

- **Phase-aware title** — the page/tab title reflects where the tournament is right now
  (Group Stage → Round of 32 → Round of 16 → … → Final).
- **Knockout bracket** (top section, collapsible) — left-to-right tournament tree with
  connector lines, each tie showing kick-off date/time in **your local timezone** and the
  **venue**. Two modes:
  - *Confirmed* — real matchups; once a tie is **final** the slot it feeds shows the
    actual advancing team, while still-undecided slots show which winners feed them.
  - *Projected (live)* — fills slots **only** from games already played or in progress
    (frozen at the current score); upcoming matches stay TBD until kickoff.
- **Third-place standings** (below the bracket, collapsible) — toggle between
  **ESPN official** and a **live-calculated** table (recomputed from results, including
  in-progress games). Top 8 qualify; the gold line is the cut-off.
- **Match highlights** (collapsible section) — every played match as a clickable card,
  bucketed by group (A–L) with team crests and the final score. Click a card to watch the
  **official FIFA highlight** in an embedded player (with a "Watch on YouTube" fallback for
  any geo-blocked video). Links are snapshotted from FIFA's own YouTube highlights playlist
  into `highlights.json`; group/crest come from the same ESPN data the page already loads.
- **Matches today** banner with live status (live minute / FT / scheduled), kickoff time in
  your local timezone, and venue.
- **Goal celebrations** — while a match is live, scoring a goal fires a **fireworks** burst and
  a chant naming the team that scored (pre-generated per-team audio, plus a procedural crowd
  roar). Toggle with the 🎆 button in the status bar. Detected by diffing each live match's
  score between polls.
- **Languages** — English, Español, and Moroccan Arabic / الدارجة (full right-to-left).
- **Learn-as-you-read Darija** — when Darija is selected, every Darija word is underlined;
  hover or tap it for a tooltip with its pronunciation (🗣 scholarly transliteration,
  ⌨ arabizi "chat alphabet") and English meaning, backed by a collapsible pronunciation
  guide. Numbers render in Arabic-Indic numerals (2026 → ٢٠٢٦) and their tooltip reads the
  whole number out the way a Moroccan says it (٢٠٢٦ → ألفين و ستة و عشرين).
  **Click any underlined word to hear it** — pronounced by Microsoft's Moroccan-Arabic
  neural voice (Jamal), pre-generated to MP3 so it plays for everyone with no API key.
- **Smart auto-refresh** — polls every 20s **only while matches are live**; otherwise it
  goes idle with a light heartbeat. Manual refresh always available.
- Tooltips on every abbreviation, plus accordions explaining the rules and the bracket.

## Updating the highlights

Match highlights come from [FIFA's official YouTube playlist][playlist]. Because the page is
static with no backend, the video links are committed to `highlights.json` rather than scraped
live in the browser. After each match day, regenerate the file and commit it:

```bash
python3 scripts/refresh-highlights.py     # re-reads the playlist → rewrites highlights.json
git add highlights.json
git commit -m "Refresh match highlights"
git push
```

The script needs only `curl` and `python3` (no API key). It pulls every video from the
playlist, parses the teams + score from each title, and normalizes team names to the English
names ESPN uses (so the cards bucket under their real group). Notes:

- A match shows up only once FIFA posts its highlight; until then the card is simply absent.
- If a team name ever prints unchanged (the script warns `! unknown team ...`), add it to the
  `TEAMS` map at the top of `scripts/refresh-highlights.py`.
- To follow a different playlist, change `PLAYLIST_URL` in the script.

**Adding a video by hand.** For a match FIFA hasn't posted yet (e.g. a knockout tie a
broadcaster like DSports uploaded first), add an entry to `highlights-manual.json` and re-run
the script — it merges manual entries for any pair the FIFA playlist doesn't already cover
(FIFA always wins, so a later official upload replaces yours automatically):

```json
{ "home": "South Africa", "away": "Canada", "hs": 0, "as": 1,
  "videoId": "t1EwOwZWH60", "title": "Sudáfrica 0–1 Canadá | Resumen (DSports)",
  "embeddable": false }
```

Set `"embeddable": false` when the video blocks embedding or is region-locked (common for
broadcaster clips); those cards open YouTube in a new tab instead of the in-page player.
Highlights whose two teams are in different groups are shown under a **Knockout stage**
heading rather than a group.

[playlist]: https://www.youtube.com/playlist?list=PLBRLtDhTHh5o

## Regenerating the Darija audio

Each glossary word **and number** has a pre-generated pronunciation clip (Microsoft's
`ar-MA-JamalNeural` voice) under `audio/`, mapped by `audio/manifest.json`. Numbers reuse the
page's own Darija speller (run via node at build time) so the audio matches the tooltip. Same reasoning as the highlights:
a static page can't call a paid TTS service at runtime, so the audio is snapshotted and
committed. After adding glossary entries, regenerate (it skips clips already made) and commit:

```bash
pip install edge-tts
python3 scripts/generate-tts.py            # --voice ar-MA-MounaNeural for the female voice
git add audio && git commit -m "Regenerate Darija TTS audio"
```

`edge-tts` is free and keyless (the same voice Edge/Bing "read aloud" uses). As with the
highlights, the audio loads only over **http(s)** — on `file://` the button is silent.

The **goal-celebration chants** are generated similarly (one per national team, upbeat English
voice) into `audio/goals/`, keyed by team name in `audio/goals.json`:

```bash
python3 scripts/generate-goal-audio.py     # pulls the 48 teams from ESPN, no API key
git add audio/goals audio/goals.json && git commit -m "Regenerate goal chants"
```

Browser autoplay rules mean the chant/cheer only sound after the user has interacted with the
page at least once (the 🎆 toggle counts); the fireworks always show.

## Live Darija text-to-speech (paste-and-listen)

When **Darija is selected**, a final 🎙️ section lets you paste any Darija text and hear it. The
audio is generated on demand and cached only in memory (never committed). Because a normal
browser can't reach the Jamal voice directly (Microsoft blocks non-Edge browsers; no free CORS
Darija API exists), it picks the best engine available:

1. **Proxy** — real Jamal in any browser, if you deploy the tiny relay in `scripts/tts-proxy.ts`
   (easiest on [Val.town](https://val.town): New → HTTP val → paste → save → put the URL in the
   section's ⚙️ settings). Free, keyless.
2. **In-browser edge-tts** — real Jamal with no deploy, but **only in Microsoft Edge** (other
   browsers are blocked by Microsoft); loaded on demand from a CDN.
3. **Web Speech API** — last-resort fallback using the device's own Arabic (MSA) voice, which is
   often absent (e.g. Linux/Chrome) and isn't true Darija. The section tells you which is active.

## Notes

- **Data:** ESPN's public API (keyless, CORS-enabled).
- The page must be served over **http(s)** (not `file://`) for the browser to fetch
  `highlights.json` — the GitHub Pages link and any local server both work.
- The bracket **structure** is hardcoded to the official 2026 draw (FIFA match numbers),
  because ESPN's own knockout feeder data is inconsistent with the real draw; ESPN's
  Round-of-32 events are mapped onto that structure by team.
- Purpose-built for the 2026 tournament (the season and bracket are hardcoded), not a
  generic, season-agnostic app.

Open `index.html` locally, or use the live app linked above.
