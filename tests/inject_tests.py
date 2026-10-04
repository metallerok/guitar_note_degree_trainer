#!/usr/bin/env python3
"""
Generates headless test pages from ../index.html into ../tmp/ (gitignored).

Outputs:
  tmp/index-test.html      - copy of index.html + smoke-test script (PASS/FAIL panel top-left)
  tmp/index-scenario.html  - copy of index.html + scenario script (A -> b3: several finds, one miss)

Run tests/run_tests.sh afterwards to capture headless-Firefox screenshots.
NOTE: the app's $ helper takes a BARE element id (no '#'), like the app itself.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
DST_DIR = os.path.join(ROOT, 'tmp')
os.makedirs(DST_DIR, exist_ok=True)

TEST_JS = r"""
(function(){
  document.head.insertAdjacentHTML('beforeend', '<style>*{transition:none!important}#testres{position:fixed;top:8px;left:8px;z-index:999;background:#f4f1e8;border:1px solid #191712;padding:8px 12px;font:11px monospace;color:#191712;max-width:84ch;max-height:92vh;overflow:auto;white-space:pre-wrap}</style>');
  const out = [];
  const ok = (name, cond) => out.push((cond ? 'PASS ' : 'FAIL ') + name);
  try {
    // ---------- clean slate (ignore persisted state from previous runs) ----------
    localStorage.removeItem('guitar-trainer-v1');
    Object.assign(window.__APP.state, { keyPc:0, degIdx:0, keyRandom:false, degRandom:false });
    window.__APP.newTask();

    const M = window.__MODEL, A = window.__APP;
    const $ = id => document.getElementById(id);          // bare id, like the app
    const cell = (s, f) => document.querySelector('.cell[data-str="' + s + '"][data-fret="' + f + '"]');
    const click = elm => elm.dispatchEvent(new MouseEvent('click', { bubbles:true }));
    const chipBy = (rowId, pred) => [...document.querySelectorAll('#' + rowId + ' .chip')].find(pred);

    // ---------- model: note math on the real neck ----------
    ok('selfCheck clean (' + (M.selfCheck()[0] || 'none') + ')', M.selfCheck().length === 0);
    ok('s6 open E (pc 4)', M.notePc(6, 0) === 4);
    ok('s6 f12 E (octave)', M.notePc(6, 12) === 4);
    ok('s6 f24 E (two octaves)', M.notePc(6, 24) === 4);
    ok('s1 open E', M.notePc(1, 0) === 4);
    ok('s1 f12 E', M.notePc(1, 12) === 4);
    ok('s5 open A', M.notePc(5, 0) === 9);
    ok('s4 open D', M.notePc(4, 0) === 2);
    ok('s3 open G', M.notePc(3, 0) === 7);
    ok('s2 open B', M.notePc(2, 0) === 11);
    ok('s6 f8 = C', M.notePc(6, 8) === 0);
    ok('s5 f1 = Bb', M.notePc(5, 1) === 10);
    ok('s3 f4 = B', M.notePc(3, 4) === 11);
    ok('s2 f5 = E', M.notePc(2, 5) === 4);
    ok('s4 f10 = C', M.notePc(4, 10) === 0);

    // ---------- model: degree -> note (spec examples) ----------
    ok('C + 1 = C', M.degToPc(0, 0) === 0);
    ok('C + b3 = Eb', M.degToPc(0, 3) === 3 && M.NOTES[3] === 'E\u266d');
    ok('C + 3 = E', M.degToPc(0, 4) === 4);
    ok('A + b3 = C', M.degToPc(9, 3) === 0);
    ok('E + 5 = B', M.degToPc(4, 7) === 11);
    ok('G + b7 = F', M.degToPc(7, 10) === 5);

    // ---------- model: target counts on a 24-fret neck ----------
    ok('12 C positions', M.targetPositions(0).length === 12);
    ok('14 E positions', M.targetPositions(4).length === 14);
    ok('13 A positions', M.targetPositions(9).length === 13);
    ok('13 D positions', M.targetPositions(2).length === 13);
    ok('13 G positions', M.targetPositions(7).length === 13);
    ok('13 B positions', M.targetPositions(11).length === 13);
    let total = 0;
    for (let pc = 0; pc < 12; pc++) total += M.targetPositions(pc).length;
    ok('all pcs tile 150 positions', total === 150);
    const cset = new Set(M.targetPositions(0).map(p => p.str + ':' + p.fret));
    ok('C positions spot check', ['6:8','6:20','5:3','5:15','4:10','4:22','3:5','3:17','2:1','2:13','1:8','1:20']
      .every(k => cset.has(k)) && cset.size === 12);

    // ---------- board structure ----------
    ok('12 key chips', document.querySelectorAll('#keyRow .chip').length === 12);
    ok('12 degree chips, exact labels',
      JSON.stringify([...document.querySelectorAll('#degRow .chip')].map(c => c.textContent)) ===
      JSON.stringify(M.DEG_NAMES));
    ok('key seg FIXED|RANDOM',
      JSON.stringify([...$('keyModeRow').children].map(b => b.textContent)) ===
      JSON.stringify(['FIXED','RANDOM']));
    ok('150 hit cells (6 open + 144 fretted)', document.querySelectorAll('#boardSvg .cell').length === 150);
    ok('24 fret wires', document.querySelectorAll('#boardSvg .g-fret').length === 24);
    ok('nut present', !!document.querySelector('#boardSvg .g-nut'));
    ok('6 strings, s6 thicker than s1',
      document.querySelectorAll('#boardSvg .g-string').length === 6 &&
      +document.querySelector('#boardSvg .g-string[data-str="6"]').getAttribute('stroke-width') >
      +document.querySelector('#boardSvg .g-string[data-str="1"]').getAttribute('stroke-width'));
    const openLbls = [...document.querySelectorAll('#boardSvg .g-open')]
      .sort((a, b) => a.getAttribute('y') - b.getAttribute('y')).map(t => t.textContent);
    ok('string 1 on top (E B G D A E)', JSON.stringify(openLbls) === JSON.stringify(['E','B','G','D','A','E']));
    const fnums = [...document.querySelectorAll('#fnums text')].map(t => t.textContent);
    ok('fret numbers 0..24', fnums.length === 25 && fnums[0] === '0' && fnums.includes('12') && fnums.includes('24'));
    const inlays = {};
    [...document.querySelectorAll('#boardSvg .g-inlay')].forEach(c => {
      const f = c.dataset.fret; inlays[f] = (inlays[f] || 0) + 1;
    });
    ok('inlays 3,5,7,9,15,17,19,21 single', [3,5,7,9,15,17,19,21].every(f => inlays[f] === 1));
    ok('double inlays at 12 and 24', inlays[12] === 2 && inlays[24] === 2);
    ok('10 marked frets only', Object.keys(inlays).length === 10);
    const openCell = cell(6, 0), nut = document.querySelector('#boardSvg .g-nut');
    ok('open column left of the nut',
      +openCell.getAttribute('x') + +openCell.getAttribute('width') < +nut.getAttribute('x'));
    ok('fret 24 cell exists', !!cell(3, 24) && +cell(3, 24).getAttribute('x') > +cell(3, 23).getAttribute('x'));

    // ---------- task: default C + 1 ----------
    const T = A.getTask();
    ok('default task C / 1 / C', T.keyPc === 0 && T.degIdx === 0 && T.targetPc === 0);
    ok('taskLine "C -> 1 (C)"', $('taskLine').textContent === 'C \u2192 1 (C)');
    ok('progress 0 / 12', $('progressLbl').textContent === 'PROGRESS 0 / 12');
    ok('errors 0', $('errorsLbl').textContent === 'ERRORS 0');
    ok('next hidden', $('nextBtn').hidden);

    // ---------- correct click ----------
    click(cell(6, 8));                             // C on the low E string, 8th fret
    ok('found mark drawn', document.querySelectorAll('#marks .found').length === 1);
    ok('mark shows note name C', document.querySelector('#marks .found text').textContent === 'C');
    ok('progress 1 / 12', $('progressLbl').textContent === 'PROGRESS 1 / 12');
    ok('no errors on hit', $('errorsLbl').textContent === 'ERRORS 0');

    // repeat click on the found position: no progress, no error
    click(cell(6, 8));
    ok('repeat click is a no-op',
      document.querySelectorAll('#marks .found').length === 1 &&
      $('progressLbl').textContent === 'PROGRESS 1 / 12' &&
      $('errorsLbl').textContent === 'ERRORS 0');

    // ---------- wrong clicks ----------
    click(cell(6, 9));                             // C#
    ok('wrong click counts error', $('errorsLbl').textContent === 'ERRORS 1');
    ok('cross shown', document.querySelectorAll('#crosses .cross').length === 1);
    ok('wrong click keeps progress', $('progressLbl').textContent === 'PROGRESS 1 / 12');
    ok('no found mark added', document.querySelectorAll('#marks .found').length === 1);
    A.clearCrosses();
    ok('cross removed', document.querySelectorAll('#crosses .cross').length === 0);

    click(cell(5, 4));                             // Bb on the A string (wrong)
    ok('second error', $('errorsLbl').textContent === 'ERRORS 2');
    click(cell(6, 8));                             // re-click found: no new error, no cross
    ok('found re-click adds no error', $('errorsLbl').textContent === 'ERRORS 2');
    click(cell(6, 9));                             // wrong again while a cross is up
    ok('crosses coexist (no input blocking)', document.querySelectorAll('#crosses .cross').length === 2);
    ok('errors counted per wrong click', $('errorsLbl').textContent === 'ERRORS 3');
    A.clearCrosses();
    ok('found marks survive', document.querySelectorAll('#marks .found').length === 1);

    // ---------- completion ----------
    M.targetPositions(0).forEach(p => click(cell(p.str, p.fret)));
    ok('all 12 found', document.querySelectorAll('#marks .found').length === 12);
    ok('task done', A.getTask().done);
    ok('complete banner', $('progressLbl').textContent === 'COMPLETE 12 / 12');
    ok('next button appears', !$('nextBtn').hidden);
    const errsBefore = $('errorsLbl').textContent;
    click(cell(6, 9));
    ok('clicks ignored after done', $('errorsLbl').textContent === errsBefore);

    // next task from the banner: cleared state, same fixed key/degree
    click($('nextBtn'));
    ok('next task resets state',
      A.getTask().found.size === 0 && !A.getTask().done &&
      A.getTask().keyPc === 0 && A.getTask().degIdx === 0 &&
      $('progressLbl').textContent === 'PROGRESS 0 / 12' &&
      $('nextBtn').hidden);

    // ---------- key / degree change recreates the task ----------
    chipBy('keyRow', c => c.textContent === 'A').click();
    ok('key chip A -> task A / 1 (A)',
      A.getTask().keyPc === 9 && A.getTask().targetPc === 9 &&
      $('taskLine').textContent === 'A \u2192 1 (A)');
    click(cell(6, 5));                             // A on the low E string
    ok('found 1 on A (13 total)', $('progressLbl').textContent === 'PROGRESS 1 / 13');
    click(cell(6, 6));                             // Bb - error
    ok('error on A task', $('errorsLbl').textContent === 'ERRORS 1');
    chipBy('degRow', c => c.textContent === '\u266d3').click();   // b3
    ok('A + b3 -> C, marks and errors cleared',
      A.getTask().targetPc === 0 && A.getTask().found.size === 0 &&
      $('taskLine').textContent === 'A \u2192 \u266d3 (C)' &&
      $('progressLbl').textContent === 'PROGRESS 0 / 12' &&
      $('errorsLbl').textContent === 'ERRORS 0');
    ok('C target: 12 positions', A.getTask().positions.length === 12);

    // ---------- reset progress ----------
    click(cell(6, 8)); click(cell(5, 3));          // two Cs
    click(cell(6, 9));                             // one error
    const targetBefore = A.getTask().targetPc, lineBefore = $('taskLine').textContent;
    click($('resetBtn'));
    ok('reset clears marks/errors, keeps task',
      A.getTask().found.size === 0 && A.getTask().errors === 0 && !A.getTask().done &&
      $('progressLbl').textContent === 'PROGRESS 0 / 12' &&
      $('taskLine').textContent === lineBefore &&
      A.getTask().targetPc === targetBefore);
    ok('marks layer empty after reset', document.querySelectorAll('#marks .found').length === 0);

    // ---------- new task with fixed modes: same key/degree ----------
    click($('newBtn'));
    ok('fixed new task keeps key/degree',
      A.getTask().keyPc === 9 && A.getTask().degIdx === 3 && A.getTask().targetPc === 0 &&
      A.getTask().found.size === 0);

    // ---------- random modes really randomize ----------
    [...$('keyModeRow').children].find(b => b.textContent === 'RANDOM').click();
    ok('random key dims key chips', $('keyRow').classList.contains('off'));
    const keys = new Set();
    for (let i = 0; i < 40; i++){ A.newTask(); keys.add(A.getTask().keyPc); }
    ok('random key varies (' + keys.size + ' of 12 in 40 draws)', keys.size > 1);
    ok('stored key pick untouched', A.state.keyPc === 9);
    [...$('degModeRow').children].find(b => b.textContent === 'RANDOM').click();
    const degs = new Set();
    for (let i = 0; i < 40; i++){ A.newTask(); degs.add(A.getTask().degIdx); }
    ok('random degree varies (' + degs.size + ' of 12 in 40 draws)', degs.size > 1);
    ok('both segs lit RANDOM',
      [...$('keyModeRow').children].find(b => b.textContent === 'RANDOM').classList.contains('on') &&
      [...$('degModeRow').children].find(b => b.textContent === 'RANDOM').classList.contains('on'));

    // back to fixed via the segs
    [...$('keyModeRow').children].find(b => b.textContent === 'FIXED').click();
    [...$('degModeRow').children].find(b => b.textContent === 'FIXED').click();
    ok('fixed again: chips enabled and highlight picks',
      !$('keyRow').classList.contains('off') &&
      chipBy('keyRow', c => c.textContent === 'A').classList.contains('on') &&
      chipBy('degRow', c => c.textContent === '\u266d3').classList.contains('on'));
    A.newTask();
    ok('fixed task after seg reset', A.getTask().keyPc === 9 && A.getTask().degIdx === 3);

    // ---------- persistence of the controls ----------
    chipBy('keyRow', c => c.textContent === 'F').click();
    ok('F -> b3 task line', $('taskLine').textContent === 'F \u2192 \u266d3 (A\u266d)');
    const saved = JSON.parse(localStorage.getItem('guitar-trainer-v1'));
    ok('selections persisted',
      saved.keyPc === 5 && saved.degIdx === 3 &&
      saved.keyRandom === false && saved.degRandom === false);
  } catch (err) {
    out.push('ERROR ' + (err && (err.name + ': ' + err.message + '\n' + err.stack) || err));
  }
  const pass = out.filter(s => s.startsWith('PASS')).length;
  document.title = 'TESTS ' + pass + '/' + out.length;
  const d = document.createElement('div');
  d.id = 'testres';
  d.textContent = out.join('\n');
  document.body.appendChild(d);
  document.getAnimations().forEach(a => a.finish());
})();
"""

SCEN_JS = r"""
(function(){
  document.head.insertAdjacentHTML('beforeend', '<style>*{transition:none!important}</style>');
  // Scenario: key A, degree b3 -> find every C; 4 finds + 1 miss (C#).
  localStorage.removeItem('guitar-trainer-v1');
  Object.assign(window.__APP.state, { keyPc:9, degIdx:3, keyRandom:false, degRandom:false });
  window.__APP.newTask();
  const cell = (s, f) => document.querySelector('.cell[data-str="' + s + '"][data-fret="' + f + '"]');
  const click = elm => elm.dispatchEvent(new MouseEvent('click', { bubbles:true }));
  window.__MODEL.targetPositions(0).slice(0, 4)
    .forEach(p => click(cell(p.str, p.fret)));
  click(cell(6, 9));
  document.getAnimations().forEach(a => a.finish());
})();
"""

def inject(path, js):
    with open(SRC, encoding='utf-8') as f:
        html = f.read()
    assert html.count('</body>') == 1
    html = html.replace('</body>', '<script>' + js + '</script>\n</body>')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

inject(os.path.join(DST_DIR, 'index-test.html'), TEST_JS)
inject(os.path.join(DST_DIR, 'index-scenario.html'), SCEN_JS)
print('written:', DST_DIR)
