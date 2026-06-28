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
  - *Confirmed* — real matchups; undecided slots show which winners feed them.
  - *Projected (live)* — fills slots **only** from games already played or in progress
    (frozen at the current score); upcoming matches stay TBD until kickoff.
- **Third-place standings** (below the bracket, collapsible) — toggle between
  **ESPN official** and a **live-calculated** table (recomputed from results, including
  in-progress games). Top 8 qualify; the gold line is the cut-off.
- **Matches today** banner with live status (live minute / FT / scheduled).
- **Languages** — English, Español, and Moroccan Arabic / الدارجة (full right-to-left).
- **Smart auto-refresh** — polls every 20s **only while matches are live**; otherwise it
  goes idle with a light heartbeat. Manual refresh always available.
- Tooltips on every abbreviation, plus accordions explaining the rules and the bracket.

## Notes

- **Data:** ESPN's public API (keyless, CORS-enabled).
- The bracket **structure** is hardcoded to the official 2026 draw (FIFA match numbers),
  because ESPN's own knockout feeder data is inconsistent with the real draw; ESPN's
  Round-of-32 events are mapped onto that structure by team.
- Purpose-built for the 2026 tournament (the season and bracket are hardcoded), not a
  generic, season-agnostic app.

Open `index.html` locally, or use the live app linked above.
