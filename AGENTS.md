# AGENTS.md — Guitar Trainer (fretboard degree drill)

## What this is

`index.html` — a single self-contained training tool: find every position of a
target note (a degree of a chosen key) on a 24-fret standard-tuned neck.
HTML + CSS + vanilla JS + SVG, **no build step, no dependencies, no backend**.
All UI text and code comments are in English. Visual language: the vintage
printed chart from the guitar poster project — paper/ink pair via CSS
variables, thin rules, seg/chip controls, **dark theme only** (`body.dark`,
warm near-black paper + cream ink, set in the markup). All colors go through
the variables in `:root` / `body.dark` (incl. `--err` for the wrong-click
cross); SVG text inherits `svg text{fill:var(--ink)}`.

## Core principle

**One music model, one app.** Two `<script>` blocks, mirroring the poster:
`#music-model` (pure data + pure functions, no DOM: `NOTES`, `DEG_NAMES`,
`TUNING`, `FRETS`, `notePc`, `degToPc`, `targetPositions`, `selfCheck`) and
the app (state + task lifecycle + rendering). The model is exposed as
`window.__MODEL`, the app as `window.__APP`. Nothing musical is hardcoded in
renderers; target positions are always computed from the real tuning.

## Architecture cheat sheet

- Tuning: `TUNING = [4, 9, 2, 7, 11, 4]` — pitch classes of strings **6→1**
  (E A D G B E). `notePc(str, fret) = (TUNING[6 - str] + fret) % 12`,
  `str` is 6..1, `fret` 0..24. Degrees are the full chromatic set
  `DEG_NAMES = ['1','♭2','2','♭3','3','4','♭5','5','♭6','6','♭7','7']`;
  the target pc is `(keyPc + degIdx) % 12`. Note names are **flat-based**
  (`C D♭ D E♭ E F G♭ G A♭ A B♭ B`) everywhere, including key chips.
- Target-count invariant (verified by `selfCheck()` and the tests): with 25
  positions per string an open-string pc occurs 3× on its own string(s):
  **E = 14, A/D/G/B = 13, the other 7 pcs = 12**, all pcs together tile the
  150 positions exactly once.
- Persisted state (`localStorage` key `guitar-trainer-v1`): `keyPc`, `degIdx`,
  `keyRandom`, `degRandom` — **selections only, never the task**. The runtime
  `task` holds `keyPc, degIdx, targetPc, positions[], found:Set("str:fret"),
  errors, done`.
- Task lifecycle: `newTask()` honours the random toggles (rolls uniformly
  over 12) and clears marks + crosses; `resetProgress()` clears
  found/crosses/errors but keeps the very same task (key/degree/target);
  completion is reached when `found.size === positions.length` — the task bar
  shows `COMPLETE n / n` and reveals the `NEXT TASK →` button. No
  auto-advance.
- Click semantics (`onCellClick`): a hit on the target pc adds the position
  to `found` and draws a permanent mark with the note name; clicking an
  already-found position is a silent no-op (never an error); a miss raises
  `errors` and shows a `×` that auto-removes after `CROSS_MS = 650 ms`
  (`showCross`/`hideCross`, timer map `crossEls`; re-missing the same cell
  restarts its timer; `clearCrosses` is the shared teardown used by reset and
  new task). Crosses and marks live in `pointer-events:none` layers above the
  hit rects, so clicks are never blocked.
- Control semantics: clicking a key/degree chip turns that random mode OFF,
  stores the pick and recreates the task (old marks are always cleared).
  Toggling a seg FIXED|RANDOM only flips the mode and re-renders the chips
  (chips get `.off` = dimmed + `pointer-events:none` while random) — the
  current task stays and the mode applies on the next task. This is
  deliberate; do not "fix" it into an immediate reroll.
- Board geometry (`const G`): string 1 on top, string 6 at the bottom
  (tab/poster convention), `strGap 34`, stroke widths `1 + i*0.32` (bass
  thickest), open-string column (`openX/openW`) separated from the nut by a
  gap, fret cells taper linearly `w1:46 → w24:26`, fret wires 1..24, fret
  numbers 0..24 in `#fnums`, single inlays at 3 5 7 9 15 17 19 21 and double
  inlays at 12 and 24 (each circle carries `data-fret` for the tests).
  `XS[]` holds the fret-line x positions; `cellCX(fret)` / `stringY(str)` are
  the single source for mark/cross placement. Hit rects (`.cell`, 6 open +
  144 fretted = 150) carry `data-str/data-fret/data-pc` and their own click
  listeners; `#marks`/`#crosses` layers are rebuilt on state change, the
  static board is built once.
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

   - `tests/inject_tests.py` generates `tmp/index-test.html` (86 assertions,
     PASS/FAIL panel top-left; the test script **resets persisted state**
     before asserting) and `tmp/index-scenario.html` (key A → ♭3: four C
     finds + one C# miss) from `index.html` into `tmp/` (gitignored).
   - Then headless Firefox captures `tmp/gt-test.png`, `tmp/gt-scenario.png`,
     `tmp/gt-default.png`.
   - **Read `tmp/gt-test.png` and check every line is PASS.**
     `document.title` also becomes `TESTS n/m`.

### Test-harness gotchas

- The app's `$` helper (and the test copy of it) takes a **bare element id**
  — `$('taskLine')`, NOT `$('#taskLine')`. A jQuery-style `#` makes
  `getElementById` return null for every lookup while `querySelector` still
  works; this once ate an afternoon.
- The wrong-click cross expires on a real 650 ms timer; the tests assert its
  presence and then call `window.__APP.clearCrosses()` (the same `hideCross`
  path the timer uses) instead of waiting.

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
