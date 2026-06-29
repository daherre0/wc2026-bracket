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
- **Matches today** banner with live status (live minute / FT / scheduled).
- **Languages** — English, Español, and Moroccan Arabic / الدارجة (full right-to-left).
- **Learn-as-you-read Darija** — when Darija is selected, every Darija word is underlined;
  hover or tap it for a tooltip with its pronunciation (🗣 scholarly transliteration,
  ⌨ arabizi "chat alphabet") and English meaning, backed by a collapsible pronunciation
  guide. Numbers render in Arabic-Indic numerals (2026 → ٢٠٢٦) and their tooltip reads the
  whole number out the way a Moroccan says it (٢٠٢٦ → ألفين و ستة و عشرين).
- **Smart auto-refresh** — polls every 20s **only while matches are live**; otherwise it
  goes idle with a light heartbeat. Manual refresh always available.
- Tooltips on every abbreviation, plus accordions explaining the rules and the bracket.

## Notes

- **Data:** ESPN's public API (keyless, CORS-enabled).
- **Highlights** come from FIFA's official YouTube playlist. Because the page is static with
  no backend, the video links are committed to `highlights.json` rather than scraped live in
  the browser. Refresh them after each match day with `python3 scripts/refresh-highlights.py`
  (needs only `curl` + `python3`, no API key) and commit the updated `highlights.json`.
  Note: the page must be served over **http(s)** (not `file://`) for the browser to fetch
  `highlights.json` — the GitHub Pages link and any local server both work.
- The bracket **structure** is hardcoded to the official 2026 draw (FIFA match numbers),
  because ESPN's own knockout feeder data is inconsistent with the real draw; ESPN's
  Round-of-32 events are mapped onto that structure by team.
- Purpose-built for the 2026 tournament (the season and bracket are hardcoded), not a
  generic, season-agnostic app.

Open `index.html` locally, or use the live app linked above.
