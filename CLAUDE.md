# World Cup 2026 Bracket — Project Instructions

Single static `index.html` (no backend/build) that tracks the FIFA World Cup 2026 live from
ESPN's public API. Trilingual: English / Español / Moroccan Arabic (Darija), with a
learn-as-you-read Darija layer (gloss tooltips + pre-generated pronunciation audio).

## ALWAYS: new Darija text must be glossable and pronounceable

Whenever you add or change **any Darija (Arabic-script) text** that a user can read — i18n `ar`
strings, section copy, labels, status messages, example words, etc. — you MUST also make it
glossable and give it sound. Do not ship Darija text without this. (Example of the miss to
avoid: the TTS-lab section was added with Darija copy but its words weren't glossed or voiced.)

For each change:

1. **Dictionary** — add every new Darija word/expression to the `GLOSS` object in `index.html`
   as `"الكلمة": ["<academic>", "<arabizi>", "<English>"]`. Add multi-word **expressions** too
   (they're matched longest-first) for nicer tooltips. Don't duplicate keys already present —
   grep the `GLOSS` block first.
2. **Don't bury it in `gloss-skip`** — readable Darija prose should sit outside any
   `.gloss-skip` container so the auto-glosser underlines it. Only keep `gloss-skip` (or rely on
   `<input>/<textarea>/<code>` which are skipped) for **interactive controls and user-typed
   text**, because a glossed word inside a `<button>` hijacks the button's click.
3. **Audio** — regenerate the pronunciation clips so the new words speak, then commit them:
   ```
   pip install edge-tts
   python3 scripts/generate-tts.py      # reads GLOSS, makes one Jamal MP3 per word + numbers
   git add audio audio/manifest.json
   ```
   The generator covers words, the 0–104 + 2026 number range, and reuses the page's own number
   speller. New month-style or special words just need a `GLOSS` entry (step 1) before running.
4. **Verify** — every `GLOSS` key resolves to an audio file and there are no duplicate keys:
   ```
   python3 - <<'PY'
   import re, json
   html=open('index.html',encoding='utf-8').read()
   keys=re.findall(r'"([^"]+)":\s*\[', re.search(r'const GLOSS = \{(.*?)\n  \};',html,re.S).group(1))
   m=json.load(open('audio/manifest.json'))
   print('dupes:', [k for k in set(keys) if keys.count(k)>1] or 'none')
   print('missing audio:', [k for k in keys if k not in m] or 'none')
   PY
   ```

## Other standing rules

- **No quotation marks in any tooltip text** (gloss tooltips, `title`/`data-tip`, venue/time
  tips). Phrase glosses and tips without `" ' “ ” ‘ ’`.
- **Arabizi digits stay Western** (7=ح, 9=ق, 2=ء, 3=ع). The glosser already skips number-glossing
  for digits adjacent to Latin letters — don't reintroduce conversion of arabizi digits.
- **Keep it a single static file** — no backend, no build step, no API keys in the client. Audio
  and data (highlights, goal chants) are snapshotted by `scripts/*.py` and committed; runtime-only
  things (the live TTS lab) use an optional user-deployed proxy, never a committed secret.
- **Pre-commit env-var check** still applies (see global instructions) if any new env var appears.
