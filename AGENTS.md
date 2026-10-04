# AGENTS.md — Guitar Trainer (fretboard degree drill)

## What this is

`index.html` — a single self-contained training tool: find positions of a
target note (a degree of the chosen key's major/natural-minor scale) on a
24-fret standard-tuned neck. Normal mode drills one degree across the whole
neck; flash mode asks for any 3 positions of a random degree, then advances
by itself. HTML + CSS + vanilla JS + SVG, **no build step, no dependencies,
no backend**.
All UI text and code comments are in English. Visual language: the vintage
printed chart from the guitar poster project — paper/ink pair via CSS
variables, thin rules, seg/chip controls, **dark theme only** (`body.dark`,
warm near-black paper + cream ink, set in the markup). All colors go through
the variables in `:root` / `body.dark` (incl. `--err` for the wrong-click
cross); SVG text inherits `svg text{fill:var(--ink)}`.

## Core principle

**One music model, one app.** Two `<script>` blocks, mirroring the poster:
`#music-model` (pure data + pure functions, no DOM: `NOTES`, `DEG_NAMES`,
`SCALES`, `TUNING`, `FRETS`, `notePc`, `degToPc`, `targetPositions`,
`selfCheck`) and the app (state + task lifecycle + rendering). The model is
exposed as `window.__MODEL`, the app as `window.__APP`. Nothing musical is
hardcoded in renderers; target positions are always computed from the real
tuning.

## Architecture cheat sheet

- Tuning: `TUNING = [4, 9, 2, 7, 11, 4]` — pitch classes of strings **6→1**
  (E A D G B E). `notePc(str, fret) = (TUNING[6 - str] + fret) % 12`,
  `str` is 6..1, `fret` 0..24. Degree **labels** are the chromatic set
  `DEG_NAMES = ['1','♭2','2','♭3','3','4','♭5','5','♭6','6','♭7','7']`,
  indexed by semitone offset; the target pc is `(keyPc + degIdx) % 12` where
  `degIdx` is always a **scale offset** — one of `SCALES[state.scale]`
  (`major: [0,2,4,5,7,9,11]`, `minor: [0,2,3,5,7,8,10]` natural minor).
  Degree chips show the 7 offsets of the current scale, rebuilt by
  `buildDegChips()` on a scale change. Note names are **flat-based**
  (`C D♭ D E♭ E F G♭ G A♭ A B♭ B`) everywhere, including key chips.
- Target-count invariant (verified by `selfCheck()` and the tests): with 25
  positions per string an open-string pc occurs 3× on its own string(s):
  **E = 14, A/D/G/B = 13, the other 7 pcs = 12**, all pcs together tile the
  150 positions exactly once.
- Persisted state (`localStorage` key `guitar-trainer-v2`): `keyPc`, `degIdx`
  (a scale offset), `keyRandom`, `degRandom`, `scale` (`'major'` default),
  `showNotes` (`true` default), `flash` (`false` default) — **selections
  only, never the task**; on load an off-scale `degIdx` resets to the tonic.
  The runtime `task` holds `keyPc, degIdx, targetPc, scale, flash,
  positions[], needed, muted (flash only), found:Set("str:fret"), errors,
  done`.
- Task lifecycle: `newTask()` honours the random toggles (degree random rolls
  uniformly over the 7 scale offsets) and clears marks + crosses; needed is
  `positions.length` normally, `FLASH_TARGET = 3` in flash. `resetProgress()`
  clears found/crosses/errors but keeps the very same task (key/degree/
  target/mutes). Completion is reached at `found.size >= needed` — the task
  bar shows `COMPLETE n / n` and reveals the `NEXT TASK →` button (hidden in
  flash, which advances by itself). No auto-advance in normal mode.
- Flash mode: any 3 positions of the target degree complete the step, then a
  `FLASH_ADVANCE_MS = 700` timer calls `flashAdvance()` (exported; cancels the
  pending timer, guarded no-op outside a done flash task) — new random degree
  **never equal to the previous one**, fresh `muted` pair, marks cleared, and
  the **error total carries over the series** (`flashErrors`, shown by
  ERRORS while flash; reset by manual NEW TASK, RESET PROGRESS and mode/
  seg-driven `newTask`s). Two distinct random strings are muted per step
  (`task.muted`, `pickMuted()`): their cells get `.muted`
  (`pointer-events:none`) and their string line / open label / number get
  `.dimmed` (opacity .25, all carry `data-str`); clicks on muted strings are
  silent no-ops **even on target positions**; the bar shows `MUTED s·s`;
  degree chips + deg seg are dimmed (`.off`) while flash owns the degree.
- Click semantics (`onCellClick`): a hit on the target pc adds the position
  to `found` and draws a permanent mark labelled `NOTES[targetPc]` (NOTES
  display) or `DEG_NAMES[degIdx]` (DEGREES display); clicking an
  already-found position is a silent no-op (never an error); a miss raises
  `errors` (and `flashErrors` in flash) and shows a `×` that auto-removes
  after `CROSS_MS = 650 ms` (`showCross`/`hideCross`, timer map `crossEls`;
  re-missing the same cell restarts its timer; `clearCrosses` is the shared
  teardown used by reset and new task). Crosses and marks live in
  `pointer-events:none` layers above the hit rects, so clicks are never
  blocked.
- Completion overlay: when a normal-mode task completes, `renderScale()`
  (called from `renderStatus`) draws every position of all 7 scale degrees as
  subdued `.g-scale` dots (r 6, `--paper2`/`--mid`) in the `#scaleMarks`
  layer **below** `#marks`, so the task's own bright marks stay highlighted;
  cleared on next task / reset; never shown in flash.
- Control semantics: clicking a key/degree chip turns that random mode OFF,
  stores the pick and recreates the task (old marks are always cleared).
  Toggling a seg FIXED|RANDOM only flips the mode and re-renders the chips
  (chips get `.off` = dimmed + `pointer-events:none` while random) — the
  current task stays and the mode applies on the next task. This is
  deliberate; do not "fix" it into an immediate reroll. SCALE (MAJOR|MINOR,
  `switchScale()`: remaps `degIdx` by scale-degree position so major `3` ↔
  minor `♭3`, rebuilds chips) and MODE (NORMAL|FLASH) change the drill itself
  and start a new task immediately; DISPLAY (NOTES|DEGREES) is a pure
  re-render (task line drops the `(note)` part and marks show degree labels
  in DEGREES; open-string labels stay note names). Segs are built by
  `buildChoiceSeg()` and lit by `renderSegs()` via each seg's `getCur()`.
- Board geometry (`const G`): string 1 on top, string 6 at the bottom
  (tab/poster convention), `strGap 34`, stroke widths `1 + i*0.32` (bass
  thickest), open-string column (`openX/openW`) separated from the nut by a
  gap, fret cells taper linearly `w1:46 → w24:26`, fret wires 1..24, fret
  numbers 0..24 in `#fnums`, single inlays at 3 5 7 9 15 17 19 21 and double
  inlays at 12 and 24 (each circle carries `data-fret` for the tests).
  `XS[]` holds the fret-line x positions; `cellCX(fret)` / `stringY(str)` are
  the single source for mark/cross placement. Hit rects (`.cell`, 6 open +
  144 fretted = 150) carry `data-str/data-fret/data-pc` and their own click
  listeners; `#scaleMarks`/`#marks`/`#crosses` layers are rebuilt on state
  change, the static board is built once.
- **Watch out:** geometry fields are `G.top/G.strGap/...` — a mistyped
  property (e.g. `G.gap`) silently yields `NaN` coordinates and a visually
  collapsed board while all DOM assertions still pass.
- The fretboard scrolls horizontally on narrow screens (`.scroll` +
  `#boardSvg{min-width:920px}`) and fills the desktop width otherwise.

## Verifying changes

1. Syntax-check both inline scripts:

   ```bash
   python3 -c "import re;src=open('index.html',encoding='utf-8').read();\
   ss=re.findall(r'<script[^>]*>\n(.*?)\n</script>',src,re.S);\
   [open(f'/tmp/opencode/gt{i}.js','w',encoding='utf-8').write(s) for i,s in enumerate(ss)]" \
   && node --check /tmp/opencode/gt0.js && node --check /tmp/opencode/gt1.js
   ```

2. Smoke tests + screenshots (self-contained):

   ```bash
   tests/run_tests.sh
   ```

   - `tests/inject_tests.py` generates `tmp/index-test.html` (136 assertions,
     PASS/FAIL panel top-left; the test script **resets persisted state**
     before asserting), `tmp/index-scenario.html` (A major `3` →
     `switchScale('minor')` → ♭3: four C finds + one C# miss, then full
     completion so the scale overlay is visible) and `tmp/index-flash.html`
     (flash: 2 of 3 marks, MUTED 2·6 dimmed, one error) from `index.html`
     into `tmp/` (gitignored).
   - Then headless Firefox captures `tmp/gt-test.png`, `tmp/gt-scenario.png`,
     `tmp/gt-flash.png`, `tmp/gt-default.png`.
   - **Read `tmp/gt-test.png` and check every line is PASS** (the window is
     1500×2300 so the whole panel fits).
     `document.title` also becomes `TESTS n/m`.

### Test-harness gotchas

- The app's `$` helper (and the test copy of it) takes a **bare element id**
  — `$('taskLine')`, NOT `$('#taskLine')`. A jQuery-style `#` makes
  `getElementById` return null for every lookup while `querySelector` still
  works; this once ate an afternoon.
- The wrong-click cross expires on a real 650 ms timer; the tests assert its
  presence and then call `window.__APP.clearCrosses()` (the same `hideCross`
  path the timer uses) instead of waiting.
- The flash auto-advance is a real 700 ms timer; the tests assert the done
  step and then call `window.__APP.flashAdvance()` directly (which first
  cancels the pending timer) — deterministic and synchronous.
- Scenario pages must go through the app's own entry points
  (`switchScale`, not raw `state.scale = ...`): raw mutation skips
  `buildDegChips()`, leaving stale major chips in a minor scenario.

### Firefox on this machine is a SNAP

- The `--profile <dir>` directory must **already exist** (hence `mkdir -p`).
- Input/output paths must be **absolute and under `$HOME`** — the project dir
  works; `/tmp` does **not** (snap-private tmp namespace).
- Use `--no-remote --headless --window-size=WxH --screenshot OUT file://...`.
- For deterministic screenshots the test pages freeze CSS transitions
  (`*{transition:none!important}`) and finish animations
  (`document.getAnimations().forEach(a => a.finish())`).

## Conventions

- `tmp/` is gitignored: scratch pages, screenshots, extracted scripts.
- Reusable test code lives in `tests/`.
- Do not commit unless explicitly asked.
