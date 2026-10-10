#!/usr/bin/env node
/* Language-switch smoke test (no browser needed).
   Extracts the page's <script>, runs it against a minimal DOM shim, and checks
   that switching to Vietnamese re-renders the JS-owned strings (scanner verdicts,
   score label, calculator unit) and stores the preference.
   Usage: node tools/check_lang.js [path/to/index.html] */
const fs = require('fs');

const htmlPath = process.argv[2] || `${__dirname}/../index.html`;
const html = fs.readFileSync(htmlPath, 'utf8');
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const script = blocks[blocks.length - 1];
if (!script || !/function tx\(/.test(script)) {
  console.error('FAIL: no bilingual runtime found in the last <script> block');
  process.exit(1);
}

const store = {};
const el = (id, extra = {}) => Object.assign({
  id, hidden: false, value: '', innerHTML: '', textContent: '',
  style: {}, dataset: {}, attrs: {},
  addEventListener() {}, setAttribute(k, v) { this.attrs[k] = v; },
  getAttribute(k) { return this.attrs[k]; },
  closest() { return null; }, scrollIntoView() {},
}, extra);

const reg = {};
['menuBtn', 'mobileNav', 'mstInput', 'scanOut', 'scanIdle', 'scanLine', 'scoreBar', 'scoreLabel',
  'runScan', 'invRange', 'flagRange', 'invLabel', 'flagLabel', 'outCount', 'outHours']
  .forEach(i => reg[i] = el(i));
reg.invRange.value = '800';
reg.flagRange.value = '2';

const demoBtns = ['clean', 'risky', 'cash'].map(k => el(`btn-${k}`, { dataset: { demo: k } }));
const langBtns = ['en', 'vi'].map(k => {
  const b = el(`lang-${k}`, { dataset: { lang: k } });
  b.handlers = {};
  b.addEventListener = function (t, f) { this.handlers[t] = f; };
  return b;
});

const document = {
  documentElement: { lang: 'en' },
  title: 'INITIAL',
  getElementById: id => reg[id] || null,
  querySelectorAll: sel => (sel === '.demoBtn' ? demoBtns
    : sel === '.langBtn' ? langBtns : []),
  addEventListener() {},
};
const window = { innerWidth: 1440, addEventListener() {} };
const localStorage = { getItem: () => null, setItem: (k, v) => { store[k] = v; } };

new Function('document', 'window', 'localStorage', script)(document, window, localStorage);

const read = () => ({
  lang: document.documentElement.lang,
  title: document.title,
  score: reg.scoreLabel.textContent,
  rows: (reg.scanOut.innerHTML.match(/>([^<>]{12,})</g) || []).map(s => s.slice(1, -1)),
  hours: reg.outHours.textContent,
});

const failures = [];
const english = read();
console.log('EN:', english.title);
console.log('   score:', english.score, '| hours:', english.hours);
english.rows.forEach(r => console.log('   -', r));

const vi = langBtns.find(b => b.dataset.lang === 'vi');
vi.handlers.click.call(vi);          // same call shape as a real click handler
const viet = read();
console.log('VI:', viet.title);
console.log('   score:', viet.score, '| hours:', viet.hours);
viet.rows.forEach(r => console.log('   -', r));

const hasDiacritics = s => /[ÀÁẢÃẠĂÂÊÔƠƯĐàáảãạăâêôơưđ]/.test(s);
if (viet.lang !== 'vi') failures.push('html lang did not switch to vi');
if (!hasDiacritics(viet.title)) failures.push('document.title still English');
if (!hasDiacritics(viet.score)) failures.push('score label still English');
if (!/giờ/.test(viet.hours)) failures.push('calculator unit still "hours"');
viet.rows.forEach((r, i) => {
  if (!hasDiacritics(r) && /[A-Za-z]{4}/.test(r)) failures.push(`scenario row ${i} still English: ${r}`);
});
if (store['vuahem.lang'] !== 'vi') failures.push('language preference not persisted');
if (vi.attrs['aria-current'] !== 'true') failures.push('active language not marked for assistive tech');

console.log(failures.length ? `\nFAIL: ${failures.length}` : '\nPASS: language switch re-renders JS-owned copy');
failures.forEach(f => console.log('  !', f));
process.exit(failures.length ? 1 : 0);
