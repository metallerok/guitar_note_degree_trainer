#!/usr/bin/env python3
"""
Generates headless test pages from ../index.html into ../tmp/ (gitignored).

Outputs:
  tmp/index-test.html      - copy of index.html + smoke-test script (PASS/FAIL panel top-left)
  tmp/index-scenario.html  - copy of index.html + scenario script (A minor -> b3: all Cs,
                             one miss, then completion reveals the scale overlay)
  tmp/index-flash.html     - copy of index.html + flash-mode scenario (2 of 3 marks,
                             two muted strings, one error)

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
    localStorage.removeItem('guitar-trainer-v2');
    Object.assign(window.__APP.state, {
      keyPc:0, degIdx:0, keyRandom:false, degRandom:false,
      scale:'major', showNotes:true, flash:false });
    window.__APP.newTask();

    const M = window.__MODEL, A = window.__APP;
    const $ = id => document.getElementById(id);          // bare id, like the app
    const cell = (s, f) => document.querySelector('.cell[data-str="' + s + '"][data-fret="' + f + '"]');
    const click = elm => elm.dispatchEvent(new MouseEvent('click', { bubbles:true }));
    const chipBy = (rowId, pred) => [...document.querySelectorAll('#' + rowId + ' .chip')].find(pred);
    const segBtn = (rowId, label) => [...$(rowId).children].find(b => b.textContent === label);
    const marksText = () => {
      const t = document.querySelector('#marks .found text');
      return t ? t.textContent : null;
    };

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

    // ---------- model: scales (major default, natural minor) ----------
    ok('major scale offsets', JSON.stringify(M.SCALES.major) === JSON.stringify([0,2,4,5,7,9,11]));
    ok('minor scale offsets', JSON.stringify(M.SCALES.minor) === JSON.stringify([0,2,3,5,7,8,10]));
    ok('scales: 7 distinct pcs, tonic first',
      ['major','minor'].every(n => M.SCALES[n].length === 7 &&
        new Set(M.SCALES[n]).size === 7 && M.SCALES[n][0] === 0));
    ok('C major = C D E F G A B',
      M.SCALES.major.map(o => M.NOTES[M.degToPc(0, o)]).join(' ') === 'C D E F G A B');
    ok('A minor = A B C D E F G',
      M.SCALES.minor.map(o => M.NOTES[M.degToPc(9, o)]).join(' ') === 'A B C D E F G');

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
    ok('7 major degree chips, exact labels',
      JSON.stringify([...document.querySelectorAll('#degRow .chip')].map(c => c.textContent)) ===
      JSON.stringify(['1','2','3','4','5','6','7']));
    ok('degree chip offsets = major scale',
      JSON.stringify([...document.querySelectorAll('#degRow .chip')].map(c => +c.dataset.deg)) ===
      JSON.stringify(M.SCALES.major));
    ok('scale seg MAJOR|MINOR',
      JSON.stringify([...$('scaleRow').children].map(b => b.textContent)) ===
      JSON.stringify(['MAJOR','MINOR']));
    ok('display seg NOTES|DEGREES',
      JSON.stringify([...$('dispRow').children].map(b => b.textContent)) ===
      JSON.stringify(['NOTES','DEGREES']));
    ok('mode seg NORMAL|FLASH',
      JSON.stringify([...$('modeRow').children].map(b => b.textContent)) ===
      JSON.stringify(['NORMAL','FLASH']));
    ok('MAJOR / NOTES / NORMAL lit by default',
      segBtn('scaleRow','MAJOR').classList.contains('on') &&
      segBtn('dispRow','NOTES').classList.contains('on') &&
      segBtn('modeRow','NORMAL').classList.contains('on'));
    ok('hint line removed from actions', !document.querySelector('.actions .note'));
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

    // ---------- task: default C major + 1 ----------
    const T = A.getTask();
    ok('default task C major / 1 / C',
      T.keyPc === 0 && T.degIdx === 0 && T.targetPc === 0 &&
      T.scale === 'major' && !T.flash && T.needed === 12);
    ok('taskLine "C -> 1 (C)"', $('taskLine').textContent === 'C \u2192 1 (C)');
    ok('progress 0 / 12', $('progressLbl').textContent === 'PROGRESS 0 / 12');
    ok('errors 0', $('errorsLbl').textContent === 'ERRORS 0');
    ok('muted label hidden in normal mode', $('mutedLbl').hidden);
    ok('next hidden', $('nextBtn').hidden);
    ok('no scale overlay while the task is open',
      document.querySelectorAll('#scaleMarks .g-scale').length === 0);

    // ---------- correct click ----------
    click(cell(6, 8));                             // C on the low E string, 8th fret
    ok('found mark drawn', document.querySelectorAll('#marks .found').length === 1);
    ok('mark shows note name C', marksText() === 'C');
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

    // ---------- completion + scale overlay ----------
    M.targetPositions(0).forEach(p => click(cell(p.str, p.fret)));
    ok('all 12 found', document.querySelectorAll('#marks .found').length === 12);
    ok('task done', A.getTask().done);
    ok('complete banner', $('progressLbl').textContent === 'COMPLETE 12 / 12');
    ok('next button appears', !$('nextBtn').hidden);
    const scaleCount = M.SCALES.major.reduce(
      (a, o) => a + M.targetPositions(M.degToPc(0, o)).length, 0);
    ok('scale overlay: whole C major on the neck (' + scaleCount + ' dots)',
      document.querySelectorAll('#scaleMarks .g-scale').length === scaleCount);
    ok('found marks render above the overlay',
      !!($('scaleMarks').compareDocumentPosition($('marks')) & Node.DOCUMENT_POSITION_FOLLOWING));
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
    ok('overlay cleared on next task',
      document.querySelectorAll('#scaleMarks .g-scale').length === 0);

    // ---------- scale seg: MAJOR <-> MINOR ----------
    chipBy('keyRow', c => c.textContent === 'A').click();
    ok('key chip A -> task A / 1 (A)',
      A.getTask().keyPc === 9 && A.getTask().targetPc === 9 &&
      $('taskLine').textContent === 'A \u2192 1 (A)');
    click(cell(6, 5));                             // A on the low E string
    ok('found 1 on A (13 total)', $('progressLbl').textContent === 'PROGRESS 1 / 13');
    click(cell(6, 6));                             // Bb - error
    ok('error on A task', $('errorsLbl').textContent === 'ERRORS 1');
    segBtn('scaleRow', 'MINOR').click();
    ok('minor chips, exact labels',
      JSON.stringify([...document.querySelectorAll('#degRow .chip')].map(c => c.textContent)) ===
      JSON.stringify(['1','2','\u266d3','4','5','\u266d6','\u266d7']));
    ok('minor chip offsets = minor scale',
      JSON.stringify([...document.querySelectorAll('#degRow .chip')].map(c => +c.dataset.deg)) ===
      JSON.stringify(M.SCALES.minor));
    ok('scale switch keeps the degree number (1)',
      A.getTask().degIdx === 0 && A.getTask().targetPc === 9 &&
      A.getTask().found.size === 0 && $('errorsLbl').textContent === 'ERRORS 0' &&
      $('taskLine').textContent === 'A \u2192 1 (A)');
    chipBy('degRow', c => c.textContent === '\u266d3').click();
    ok('A minor b3 -> C, marks and errors cleared',
      A.getTask().targetPc === 0 && A.getTask().found.size === 0 &&
      $('taskLine').textContent === 'A \u2192 \u266d3 (C)' &&
      $('progressLbl').textContent === 'PROGRESS 0 / 12' &&
      $('errorsLbl').textContent === 'ERRORS 0');
    ok('C target: 12 positions', A.getTask().positions.length === 12);
    ok('MINOR seg lit', segBtn('scaleRow','MINOR').classList.contains('on') &&
      !segBtn('scaleRow','MAJOR').classList.contains('on'));

    // ---------- display seg: NOTES <-> DEGREES ----------
    click(cell(6, 8));                             // C on the low E string
    ok('mark shows note name (NOTES)', marksText() === 'C');
    ok('taskLine keeps the note (NOTES)', $('taskLine').textContent === 'A \u2192 \u266d3 (C)');
    segBtn('dispRow', 'DEGREES').click();
    ok('mark shows degree label (DEGREES)', marksText() === '\u266d3');
    ok('taskLine drops the note (DEGREES)', $('taskLine').textContent === 'A \u2192 \u266d3');
    ok('display switch keeps the task',
      A.getTask().found.size === 1 && A.getTask().degIdx === 3 && !A.getTask().done);
    segBtn('dispRow', 'NOTES').click();
    ok('back to NOTES', marksText() === 'C');

    // ---------- reset progress ----------
    click(cell(1, 8));                             // second C
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
    segBtn('keyModeRow', 'RANDOM').click();
    ok('random key dims key chips', $('keyRow').classList.contains('off'));
    const keys = new Set();
    for (let i = 0; i < 40; i++){ A.newTask(); keys.add(A.getTask().keyPc); }
    ok('random key varies (' + keys.size + ' of 12 in 40 draws)', keys.size > 1);
    ok('stored key pick untouched', A.state.keyPc === 9);
    segBtn('degModeRow', 'RANDOM').click();
    const degs = new Set();
    for (let i = 0; i < 40; i++){ A.newTask(); degs.add(A.getTask().degIdx); }
    ok('random degree varies within the scale (' + degs.size + ' of 7 in 40 draws)', degs.size > 1);
    ok('both segs lit RANDOM',
      segBtn('keyModeRow','RANDOM').classList.contains('on') &&
      segBtn('degModeRow','RANDOM').classList.contains('on'));

    // back to fixed via the segs
    segBtn('keyModeRow', 'FIXED').click();
    segBtn('degModeRow', 'FIXED').click();
    ok('fixed again: chips enabled and highlight picks',
      !$('keyRow').classList.contains('off') &&
      chipBy('keyRow', c => c.textContent === 'A').classList.contains('on') &&
      chipBy('degRow', c => c.textContent === '\u266d3').classList.contains('on'));
    A.newTask();
    ok('fixed task after seg reset', A.getTask().keyPc === 9 && A.getTask().degIdx === 3);

    // ---------- persistence of the controls ----------
    chipBy('keyRow', c => c.textContent === 'F').click();
    ok('F minor b3 -> Ab', $('taskLine').textContent === 'F \u2192 \u266d3 (A\u266d)');
    const saved = JSON.parse(localStorage.getItem('guitar-trainer-v2'));
    ok('selections persisted',
      saved.keyPc === 5 && saved.degIdx === 3 &&
      saved.keyRandom === false && saved.degRandom === false &&
      saved.scale === 'minor' && saved.showNotes === true && saved.flash === false);

    // ---------- flash mode ----------
    segBtn('modeRow', 'FLASH').click();
    const FT = A.getTask();
    ok('flash task: 3 positions needed', FT.flash && FT.needed === A.FLASH_TARGET && !FT.done);
    ok('flash progress 0 / 3', $('progressLbl').textContent === 'PROGRESS 0 / 3');
    ok('degree controls dimmed in flash',
      $('degRow').classList.contains('off') && $('degModeRow').classList.contains('off'));
    const mut = FT.muted;
    ok('two distinct muted strings',
      Array.isArray(mut) && mut.length === 2 && mut[0] !== mut[1] &&
      mut.every(s => s >= 1 && s <= 6));
    const ms = [...mut].sort((a, b) => a - b);
    ok('MUTED label shows both strings',
      !$('mutedLbl').hidden &&
      $('mutedLbl').textContent === 'MUTED ' + ms[0] + '\u00b7' + ms[1]);
    ok('50 muted cells (2 strings x 25)',
      document.querySelectorAll('#boardSvg .cell.muted').length === 50);
    ok('2 dimmed strings',
      document.querySelectorAll('#boardSvg .g-string.dimmed').length === 2);
    ok('open labels and string numbers dimmed too',
      document.querySelectorAll('#boardSvg .g-open.dimmed').length === 2 &&
      document.querySelectorAll('#boardSvg .g-slbl.dimmed').length === 2);
    ok('other strings untouched',
      document.querySelectorAll('#boardSvg .g-string:not(.dimmed)').length === 4);

    // muted string: silent no-op even on a real target position
    const mp = M.targetPositions(FT.targetPc).find(p => mut.includes(p.str));
    ok('muted string holds a target position', !!mp);
    click(cell(mp.str, mp.fret));
    ok('muted click ignored (no mark/error/cross)',
      A.getTask().found.size === 0 && A.getTask().errors === 0 &&
      document.querySelectorAll('#crosses .cross').length === 0 &&
      $('progressLbl').textContent === 'PROGRESS 0 / 3');

    // wrong click on an active string
    const actStr = [1,2,3,4,5,6].find(s => !mut.includes(s));
    const badFret = [...Array(25).keys()].find(f => M.notePc(actStr, f) !== FT.targetPc);
    click(cell(actStr, badFret));
    ok('flash error counted',
      $('errorsLbl').textContent === 'ERRORS 1' && A.getFlashErrors() === 1);

    // three hits complete the flash step
    const hits = M.targetPositions(FT.targetPc).filter(p => !mut.includes(p.str)).slice(0, 3);
    ok('3 active-string targets available', hits.length === 3);
    hits.forEach(p => click(cell(p.str, p.fret)));
    ok('flash completes at 3', FT.done && $('progressLbl').textContent === 'COMPLETE 3 / 3');
    ok('next button hidden in flash', $('nextBtn').hidden);
    ok('no scale overlay in flash',
      document.querySelectorAll('#scaleMarks .g-scale').length === 0);

    // auto-advance (the 700 ms timer path): new random degree, errors carry over
    const prevDeg = FT.degIdx, prevLine = $('taskLine').textContent;
    A.flashAdvance();
    ok('flash advances to a new degree',
      !A.getTask().done && A.getTask().found.size === 0 &&
      A.getTask().degIdx !== prevDeg && $('taskLine').textContent !== prevLine);
    ok('errors carry across the flash series',
      $('errorsLbl').textContent === 'ERRORS 1' && A.getFlashErrors() === 1);
    ok('mutes re-rolled, still valid',
      A.getTask().muted.length === 2 && A.getTask().muted[0] !== A.getTask().muted[1]);
    ok('progress reset to 0 / 3', $('progressLbl').textContent === 'PROGRESS 0 / 3');

    // NEW TASK starts a fresh series (errors included)
    click($('newBtn'));
    ok('new task resets the flash series',
      A.getTask().flash && $('errorsLbl').textContent === 'ERRORS 0' &&
      A.getFlashErrors() === 0 && $('progressLbl').textContent === 'PROGRESS 0 / 3');

    // back to normal mode
    segBtn('modeRow', 'NORMAL').click();
    ok('back to normal mode',
      !A.getTask().flash && A.getTask().needed === A.getTask().positions.length &&
      !$('degRow').classList.contains('off') && !$('degModeRow').classList.contains('off') &&
      $('mutedLbl').hidden && $('progressLbl').textContent === 'PROGRESS 0 / 12');
    ok('no muted cells left',
      document.querySelectorAll('#boardSvg .cell.muted').length === 0 &&
      document.querySelectorAll('#boardSvg .g-string.dimmed').length === 0);
    const lineKeep = $('taskLine').textContent;
    A.flashAdvance();
    ok('flashAdvance is a no-op in normal mode',
      A.getTask().found.size === 0 && !A.getTask().done &&
      $('taskLine').textContent === lineKeep);
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
  // Scenario: A minor, degree b3 -> find every C; one miss on the way,
  // then the completed task reveals the A-minor scale overlay on the neck.
  localStorage.removeItem('guitar-trainer-v2');
  Object.assign(window.__APP.state, {
    keyPc:9, degIdx:4, keyRandom:false, degRandom:false,
    scale:'major', showNotes:true, flash:false });
  window.__APP.newTask();            // A major, degree 3 (D flat)
  window.__APP.switchScale('minor'); // remaps 3 -> b3, rebuilds the degree chips
  const cell = (s, f) => document.querySelector('.cell[data-str="' + s + '"][data-fret="' + f + '"]');
  const click = elm => elm.dispatchEvent(new MouseEvent('click', { bubbles:true }));
  const ps = window.__MODEL.targetPositions(0);
  ps.slice(0, 4).forEach(p => click(cell(p.str, p.fret)));   // four Cs
  click(cell(6, 9));                                          // C# miss -> cross + error
  ps.slice(4).forEach(p => click(cell(p.str, p.fret)));       // complete: 12 / 12
  document.getAnimations().forEach(a => a.finish());
})();
"""

FLASH_JS = r"""
(function(){
  document.head.insertAdjacentHTML('beforeend', '<style>*{transition:none!important}</style>');
  // Scenario: flash mode, C major — two of three marks placed, two strings muted.
  localStorage.removeItem('guitar-trainer-v2');
  Object.assign(window.__APP.state, {
    keyPc:0, degIdx:0, keyRandom:false, degRandom:false,
    scale:'major', showNotes:true, flash:true });
  window.__APP.newTask();
  const cell = (s, f) => document.querySelector('.cell[data-str="' + s + '"][data-fret="' + f + '"]');
  const click = elm => elm.dispatchEvent(new MouseEvent('click', { bubbles:true }));
  const A = window.__APP, M = window.__MODEL;
  const mut = A.getTask().muted;
  const mutedTarget = M.targetPositions(0).find(p => mut.includes(p.str));
  click(cell(mutedTarget.str, mutedTarget.fret));             // ignored: string is muted
  M.targetPositions(0).filter(p => !mut.includes(p.str)).slice(0, 2)
    .forEach(p => click(cell(p.str, p.fret)));                // 2 of 3 marks
  click(cell(mut.includes(6) ? 5 : 6, 1));                    // wrong click -> error
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
inject(os.path.join(DST_DIR, 'index-flash.html'), FLASH_JS)
print('written:', DST_DIR)
